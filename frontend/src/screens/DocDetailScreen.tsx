import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import type { DocRecord } from "../types";

export function DocDetailScreen() {
  const { id } = useParams();
  const [doc, setDoc] = useState<DocRecord | null>(null);
  const [error, setError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!id) return;
    let active = true;
    let url = "";
    setDoc(null);
    setPreviewUrl("");
    setError("");
    void api
      .getDoc(id)
      .then(async (record) => {
        if (!active) return;
        setDoc(record);
        url = await api.previewDoc(record);
        if (active) setPreviewUrl(url);
        else if (!api.usesMock) URL.revokeObjectURL(url);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Document not found.");
      });
    return () => {
      active = false;
      if (url && !api.usesMock) URL.revokeObjectURL(url);
    };
  }, [id]);

  return (
    <AppShell>
      {error ? (
        <p className="mt-10 text-sm text-[#8a1f1f]">{error}</p>
      ) : !doc ? (
        <p className="mt-10 text-muted">Loading document…</p>
      ) : (
        <>
          <div className="mt-4 grid min-h-[220px] place-items-center rounded-md border border-ink bg-mist px-4 py-10 text-center">
            {previewUrl && doc.kind === "image" ? (
              <img src={previewUrl} alt={doc.title} className="max-h-56 object-contain" />
            ) : previewUrl ? (
              <a href={previewUrl} target="_blank" rel="noreferrer" className="underline">Open original PDF</a>
            ) : (
              <div>
                <p className="text-lg">Loading preview…</p>
              </div>
            )}
          </div>
          <pre className="mt-8 overflow-x-auto text-[15px] leading-7">
            {JSON.stringify(doc.extracted, null, 2)}
          </pre>
          <Link to="/docs" className="mt-8 inline-block text-sm text-muted">
            All documents
          </Link>
        </>
      )}
    </AppShell>
  );
}
