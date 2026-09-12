import { useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useSession } from "../session/SessionContext";
import medistoryLogo from "../assets/medistory_logo.png";

type AppShellProps = {
  children: ReactNode;
  showPlay?: boolean;
  onPlay?: () => void;
};

export function AppShell({ children, showPlay, onPlay }: AppShellProps) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const { setUser } = useSession();
  const navigate = useNavigate();

  async function logout() {
    try {
      await api.logout();
      setUser(null);
      navigate("/auth");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign out. Please try again.");
    }
  }

  return (
    <div className="relative mx-auto min-h-dvh w-full max-w-[430px] bg-paper shadow-[0_0_0_1px_var(--color-line)]">
      <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-3">
        <Link to="/" aria-label="MediStory — главная" className="block min-w-0 max-w-[240px] flex-1 rounded-lg">
          <img src={medistoryLogo} alt="MediStory" width={2172} height={724} className="block h-auto w-full" />
        </Link>
        <div className="flex shrink-0 items-center gap-2">
          {showPlay ? (
            <button
              type="button"
              onClick={onPlay}
              aria-label="View recorded diagnoses"
              className="grid h-10 w-10 place-items-center rounded-xl bg-mist text-brand hover:bg-line"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="6 3 20 12 6 21 6 3" />
              </svg>
            </button>
          ) : null}
          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="grid h-10 w-10 place-items-center rounded-xl bg-mist text-brand hover:bg-line"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" x2="20" y1="6" y2="6" />
              <line x1="4" x2="20" y1="12" y2="12" />
              <line x1="4" x2="20" y1="18" y2="18" />
            </svg>
          </button>
        </div>
      </header>
      {open ? (
        <nav className="absolute right-4 z-20 w-40 rounded-xl border border-line bg-paper p-3 text-sm shadow-lg">
          <Link className="block py-1.5" to="/docs" onClick={() => setOpen(false)}>
            my docs
          </Link>
          <Link className="block py-1.5" to="/anketa" onClick={() => setOpen(false)}>
            profile
          </Link>
          <button type="button" className="block w-full py-1.5 text-left" onClick={() => void logout()}>
            logout
          </button>
        </nav>
      ) : null}
      <main className="px-6 pb-10">
        {error ? <p role="alert" className="mt-4 text-sm text-[#8a1f1f]">{error}</p> : null}
        {children}
      </main>
    </div>
  );
}
