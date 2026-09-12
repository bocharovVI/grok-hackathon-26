import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import type { DocRecord } from "../types";

export function DocsListScreen() {
  const [docs, setDocs] = useState<DocRecord[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void api
      .listDocs()
      .then(setDocs)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load documents."));
  }, []);

  return (
    <AppShell>
      <h1 className="sr-only">My docs</h1>
      {error ? <p className="mt-6 text-sm text-[#8a1f1f]">{error}</p> : null}
      {!docs && !error ? <p className="mt-10 text-muted">Loading documents…</p> : null}
      {docs?.length === 0 ? (
        <div className="mt-16">
          <h2 className="font-serif text-3xl">No documents yet</h2>
          <p className="mt-3 text-muted">Upload a scan from Overview to start a file.</p>
          <Link to="/" className="mt-6 inline-block border-b border-ink pb-0.5">
            Back to overview
          </Link>
        </div>
      ) : (
        <ul className="mt-10 space-y-6">
          {docs?.map((doc) => (
            <li key={doc.id}>
              <Link to={`/docs/${doc.id}`} className="block border-b border-ink pb-2 text-lg">
                {doc.title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
