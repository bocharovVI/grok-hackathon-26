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
    if (busy) return;
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
      <form
        ref={formRef}
        className="mt-16 flex flex-col gap-6"
        aria-busy={busy}
        onSubmit={(e) => {
          e.preventDefault();
          void submit("signup");
        }}
      >
        <div>
          <h1 className="text-3xl font-medium">Регистрация</h1>
          <p className="mt-3 text-muted">Создайте аккаунт для хранения медицинских документов.</p>
        </div>
        <label className="block">
          <span className="text-sm">Email</span>
          <input
            required
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full border-b border-ink bg-transparent py-2 outline-none"
          />
        </label>
        <label className="block">
          <span className="text-sm">Пароль</span>
          <input
            required
            minLength={8}
            maxLength={72}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Не менее 8 символов"
            className="w-full border-b border-ink bg-transparent py-2 outline-none"
          />
        </label>
        {error ? <p role="alert" className="text-sm text-[#8a1f1f]">{error}</p> : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full cursor-pointer rounded-xl bg-brand px-4 py-3 font-medium text-paper hover:bg-ink disabled:cursor-wait disabled:opacity-50"
        >
          Зарегистрироваться
        </button>
        <div className="flex flex-col gap-3">
          <p className="text-center text-sm text-muted">Уже есть аккаунт?</p>
          <button
            type="button"
            disabled={busy}
            onClick={() => void submit("signin")}
            className="w-full cursor-pointer rounded-md border border-ink px-4 py-3 font-medium disabled:cursor-wait disabled:opacity-50"
          >
            Войти
          </button>
        </div>
        {busy ? <p role="status" className="text-center text-sm text-muted">Подождите…</p> : null}
      </form>
    </AppShell>
  );
}
