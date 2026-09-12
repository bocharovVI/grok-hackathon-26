import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { AppShell } from "../components/AppShell";
import { useSession } from "../session/SessionContext";
import type { Profile, Sex } from "../types";

const empty: Profile = {
  heightCm: "",
  weightKg: "",
  age: "",
  sex: "",
  comments: "",
};

export function AnketaScreen() {
  const { setUser } = useSession();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<Profile>(empty);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void api.getProfile().then(setProfile).catch(() => undefined);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await api.saveProfile(profile);
      setUser(user);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the anketa.");
    } finally {
      setBusy(false);
    }
  }

  function field(key: keyof Profile, placeholder: string) {
    return (
      <input
        required={key !== "comments"}
        value={profile[key]}
        onChange={(e) => setProfile((p) => ({ ...p, [key]: e.target.value }))}
        placeholder={placeholder}
        className="w-full border-b border-ink bg-transparent py-3 outline-none"
      />
    );
  }

  return (
    <AppShell>
      <form className="mt-6 flex flex-col gap-5" onSubmit={(e) => void onSubmit(e)}>
        <h1 className="font-serif text-4xl">Анкета</h1>
        {field("heightCm", "рост")}
        {field("weightKg", "вес")}
        <div className="flex gap-3">
          <input
            required
            inputMode="numeric"
            value={profile.age}
            onChange={(e) => setProfile((p) => ({ ...p, age: e.target.value }))}
            placeholder="возраст"
            className="w-1/2 border-b border-ink bg-transparent py-3 outline-none"
          />
          <select
            required
            value={profile.sex}
            onChange={(e) => setProfile((p) => ({ ...p, sex: e.target.value as Sex }))}
            className="w-1/2 border-b border-ink bg-transparent py-3 outline-none"
          >
            <option value="">пол</option>
            <option value="female">жен</option>
            <option value="male">муж</option>
            <option value="other">другое</option>
          </select>
        </div>
        <textarea
          value={profile.comments}
          onChange={(e) => setProfile((p) => ({ ...p, comments: e.target.value }))}
          placeholder="комментарии"
          rows={3}
          className="w-full resize-none border-b border-ink bg-transparent py-3 outline-none"
        />
        {error ? <p className="text-sm text-[#8a1f1f]">{error}</p> : null}
        <button
          type="submit"
          disabled={busy}
          className="mt-4 self-start rounded-md bg-ink px-4 py-2 text-sm text-paper"
        >
          Save
        </button>
      </form>
    </AppShell>
  );
}
