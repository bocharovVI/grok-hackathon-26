import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import type { DocRecord } from "../types";

export function DocDetailScreen() {
  const { id } = useParams();
  const [doc, setDoc] = useState<DocRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    void api
      .getDoc(id)
      .then(setDoc)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Document not found."));
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
            {doc.previewUrl && doc.kind === "image" ? (
              <img src={doc.previewUrl} alt={doc.title} className="max-h-56 object-contain" />
            ) : (
              <div>
                <p className="text-xl italic">image</p>
                <p className="mt-2 text-lg">Pdf</p>
              </div>
            )}
          </div>
          <pre className="mt-8 overflow-x-auto text-[15px] leading-7">
            {`${doc.title} : {\n  ${Object.entries(doc.extracted)
              .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
              .join(",\n  ")}\n}`}
          </pre>
          <Link to="/docs" className="mt-8 inline-block text-sm text-muted">
            All documents
          </Link>
        </>
      )}
    </AppShell>
  );
}
