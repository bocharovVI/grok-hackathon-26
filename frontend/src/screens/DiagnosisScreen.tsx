import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import type { DiagnosisRecord } from "../types";

export function DiagnosisScreen() {
  const [record, setRecord] = useState<DiagnosisRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void api
      .getDiagnosis()
      .then(setRecord)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load diagnosis."));
  }, []);

  return (
    <AppShell>
      <h1 className="mt-20 text-center font-serif text-4xl">диагноз</h1>
      {error ? <p className="mt-6 text-center text-sm text-[#8a1f1f]">{error}</p> : null}
      {!record && !error ? (
        <p className="mt-10 text-center text-muted">Generate a diagnosis from Overview.</p>
      ) : null}
      {record ? (
        <div className="mt-10 space-y-4 text-[17px] leading-7">
          <p className="font-medium">{record.title}</p>
          <p>{record.summary}</p>
          <ul className="space-y-3">
            {record.findings.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-ink" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="mt-12 text-center">
        <Link to="/" className="border-b border-ink pb-0.5">
          Overview
        </Link>
      </div>
    </AppShell>
  );
}
