import base64
import io
import json
import logging
import warnings
from functools import lru_cache
from pathlib import Path
from threading import Lock
from time import monotonic

import httpx
import pypdfium2 as pdfium
from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[2]
PDF_LOCK = Lock()  # PDFium calls must not overlap between request threads.
logger = logging.getLogger("uvicorn.error.document_parser")


class InvalidDocument(ValueError):
    pass


class ParserError(ValueError):
    pass


@lru_cache
def response_schema() -> dict:
    return json.loads((ROOT / "outpatient_visit_general.schema.json").read_text(encoding="utf-8"))


def image_part(image: Image.Image) -> dict:
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((2400, 2400))
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}", "detail": "high"}}


def prepare_images(content: bytes) -> tuple[str, list[dict]]:
    if content.startswith(b"%PDF-"):
        try:
            with PDF_LOCK, pdfium.PdfDocument(content) as pdf:
                if not 1 <= len(pdf) <= settings.max_pdf_pages:
                    raise InvalidDocument(f"PDF must contain 1–{settings.max_pdf_pages} pages")
                parts = []
                for page in pdf:
                    try:
                        width, height = page.get_size()
                        if width <= 0 or height <= 0:
                            raise InvalidDocument("Invalid PDF page dimensions")
                        bitmap = page.render(scale=min(2, 2400 / max(width, height)))
                        try:
                            parts.append(image_part(bitmap.to_pil()))
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
                return "application/pdf", parts
        except pdfium.PdfiumError as exc:
            raise InvalidDocument("Cannot read this PDF (it may be encrypted or damaged)") from exc
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.width * image.height > 20_000_000:
                    raise InvalidDocument("Image exceeds 20 megapixels; resize it before uploading")
                if image.format not in ("PNG", "JPEG", "WEBP"):
                    raise InvalidDocument("Supported formats: PDF, PNG, JPEG, WEBP")
                if getattr(image, "n_frames", 1) != 1:
                    raise InvalidDocument("Animated images are not supported; upload a PDF for multiple pages")
                mime = Image.MIME[image.format]
                return mime, [image_part(image)]
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidDocument("Invalid or excessively large image") from exc


def parse_document(images: list[dict], context: dict) -> dict:
    if not settings.xai_api_key:
        raise ParserError("XAI_API_KEY is not configured")
    prompt = (ROOT / "prompt_medical_document_parser_v3.md").read_text(encoding="utf-8")
    started = monotonic()
    logger.info("Grok request started model=%s pages=%d read_timeout_seconds=%s reasoning_effort=%s",
                settings.xai_model, len(images), settings.xai_timeout_seconds,
                settings.xai_reasoning_effort or "provider_default")
    try:
        timeout = httpx.Timeout(connect=10, read=settings.xai_timeout_seconds, write=60, pool=10)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.xai_api_key}"},
                json={
                    "model": settings.xai_model,
                    **({"reasoning_effort": settings.xai_reasoning_effort} if settings.xai_reasoning_effort else {}),
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": "DOCUMENT_CONTEXT:\n" + json.dumps(context) +
                             "\nSOURCE_IMAGES: all pages of one document, in order."},
                            *images,
                        ]},
                    ],
                    "response_format": {"type": "json_schema", "json_schema": {
                        "name": "medical_history_db_import", "strict": True, "schema": response_schema(),
                    }},
                },
            )
            response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
            raise ParserError("Grok did not return a complete extraction")
        data = json.loads(choice["message"]["content"])
        logger.info("Grok response received model=%s elapsed_seconds=%.1f", settings.xai_model, monotonic() - started)
        return data
    except httpx.TimeoutException as exc:
        logger.warning("Grok timeout model=%s stage=%s elapsed_seconds=%.1f",
                       settings.xai_model, type(exc).__name__, monotonic() - started)
        if isinstance(exc, httpx.ReadTimeout):
            raise ParserError(
                f"Grok did not respond within the {settings.xai_timeout_seconds:g}-second read timeout. "
                "Try a document with fewer pages or retry later."
            ) from exc
        raise ParserError("Connection to Grok timed out; please try again later") from exc
    except httpx.HTTPError as exc:
        logger.warning("Grok request failed model=%s error_type=%s status=%s elapsed_seconds=%.1f",
                       settings.xai_model, type(exc).__name__,
                       exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None,
                       monotonic() - started)
        raise ParserError("Grok request failed; check API key, model and quota on the server") from exc
    except ParserError:
        raise
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ParserError("Grok returned an invalid response") from exc


def validate_extraction(data: dict, context: dict) -> None:
    # Validation errors can contain medical data: do not echo them to logs or responses.
    if next(Draft202012Validator(response_schema(), format_checker=FormatChecker()).iter_errors(data), None):
        raise ParserError("Grok output does not match the medical document schema")
    if data["patient"]["id"] != context["patient_id"] or "user_id" in data["patient"]:
        raise ParserError("Grok returned an inconsistent patient identity")
    if len(data["documents"]) != 1:
        raise ParserError("Expected exactly one source document")
    document = data["documents"][0]
    for field, key in (("id", "document_id"), ("s3_url", "s3_url"), ("created_at", "ingested_at")):
        if document[field] != context[key]:
            raise ParserError("Grok changed the source document context")

    collections = {key: {row["id"] for row in data[key]} for key in (
        "documents", "medical_organizations", "doctors", "medical_visits", "medications",
        "operations", "diagnoses", "recommendations",
    )}
    seen = {data["patient"]["id"]}
    for key, ids in collections.items():
        if len(ids) != len(data[key]) or seen & ids:
            raise ParserError("Grok returned duplicate entity IDs")
        seen.update(ids)
        for row in data[key]:
            if "patient_id" in row and row["patient_id"] != context["patient_id"]:
                raise ParserError("Grok returned a record for another patient")
            for fk, target in (("doctor_id", "doctors"), ("med_org_id", "medical_organizations"),
                               ("document_id", "documents")):
                if row.get(fk) is not None and row[fk] not in collections[target]:
                    raise ParserError("Grok returned a dangling entity reference")
            for fk, target in (("diagnosis_ids", "diagnoses"), ("recommendation_ids", "recommendations")):
                if any(value not in collections[target] for value in row.get(fk, [])):
                    raise ParserError("Grok returned a dangling visit reference")
