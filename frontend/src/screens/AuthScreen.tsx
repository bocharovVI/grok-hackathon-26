import { useRef, useState } from "react";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import { useSession } from "../session/SessionContext";

export function AuthScreen() {
  const { setUser } = useSession();
  const formRef = useRef<HTMLFormElement>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(next: "signup" | "signin") {
    if (!formRef.current?.reportValidity()) return;
    setError("");
    setBusy(true);
    try {
      const user =
        next === "signup"
          ? await api.signup(email.trim(), password)
          : await api.login(email.trim(), password);
      setUser(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <form ref={formRef} className="mt-24 flex flex-col gap-8" onSubmit={(e) => e.preventDefault()}>
        <button
          type="button"
          disabled={busy}
          onClick={() => void submit("signup")}
          className="text-left text-[28px] font-medium lowercase leading-none"
        >
          sign up
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void submit("signin")}
          className="text-left text-[28px] font-medium lowercase leading-none"
        >
          sign in
        </button>
        <label className="block">
          <span className="sr-only">Email</span>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email"
            className="w-full border-b border-ink bg-transparent py-2 outline-none"
          />
        </label>
        <label className="block">
          <span className="sr-only">Password</span>
          <input
            required
            minLength={8}
            maxLength={72}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            className="w-full border-b border-ink bg-transparent py-2 outline-none"
          />
        </label>
        {error ? <p className="text-sm text-[#8a1f1f]">{error}</p> : null}
      </form>
    </AppShell>
  );
}
