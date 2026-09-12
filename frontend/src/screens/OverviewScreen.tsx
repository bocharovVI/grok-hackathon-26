import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";

export function OverviewScreen() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [bullets, setBullets] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void api
      .overview()
      .then(setBullets)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load overview."));
  }, []);

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setError("");
    try {
      const doc = await api.uploadDoc(file);
      navigate(`/docs/${doc.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  async function onCreate() {
    setError("");
    try {
      await api.createDiagnosis();
      navigate("/diagnosis");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create a diagnosis.");
    }
  }

  return (
    <AppShell showPlay onPlay={() => void onCreate()}>
      <h1 className="mt-6 font-serif text-4xl italic">Overview</h1>
      <ul className="mt-8 space-y-4">
        {(bullets.length ? bullets : ["…", "…", "…"]).map((line, index) => (
          <li key={`${line}-${index}`} className="flex items-start gap-3 text-[17px]">
            <span className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-ink" />
            <span>{line}</span>
          </li>
        ))}
      </ul>
      {error ? <p className="mt-4 text-sm text-[#8a1f1f]">{error}</p> : null}
      <div className="mt-16 flex items-center gap-3">
        <button
          type="button"
          aria-label="Upload document"
          onClick={() => inputRef.current?.click()}
          className="grid h-10 w-10 place-items-center rounded-md border border-ink"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" x2="12" y1="3" y2="15" />
          </svg>
        </button>
        <button type="button" onClick={() => void onCreate()} className="text-lg">
          or create
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/*,.pdf,application/pdf"
          className="hidden"
          onChange={(e) => void onUpload(e.target.files?.[0])}
        />
      </div>
    </AppShell>
  );
}
