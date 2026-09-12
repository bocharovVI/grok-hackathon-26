import type { AuthSession, DiagnosisRecord, DocRecord, Profile, SessionUser } from "../types";
import { readAccessToken, writeAccessToken } from "./authToken";
import { mockApi } from "./mock";

const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

function asUser(session: AuthSession): SessionUser {
  return {
    id: session.id,
    email: session.email,
    profileComplete: session.profileComplete,
  };
}

function remember(session: AuthSession): SessionUser {
  writeAccessToken(session.token ?? null);
  return asUser(session);
}

function headers(init?: RequestInit, json = false): HeadersInit {
  const token = readAccessToken();
  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init?.headers,
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: headers(init, Boolean(init?.body)),
    credentials: readAccessToken() ? "omit" : "include",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  usesMock: !apiBase,

  async signup(email: string, password: string) {
    if (!apiBase) return mockApi.signup(email, password);
    return remember(
      await request<AuthSession>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    );
  },

  async login(email: string, password: string) {
    if (!apiBase) return mockApi.login(email, password);
    return remember(
      await request<AuthSession>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    );
  },

  async logout() {
    writeAccessToken(null);
    if (!apiBase) return mockApi.logout();
    return request<void>("/auth/logout", { method: "POST" });
  },

  me() {
    if (!apiBase) return mockApi.me();
    return request<SessionUser | null>("/me");
  },

  getProfile() {
    if (!apiBase) return mockApi.getProfile();
    return request<Profile>("/me/profile");
  },

  saveProfile(profile: Profile) {
    if (!apiBase) return mockApi.saveProfile(profile);
    return request<SessionUser>("/me/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    });
  },

  overview() {
    if (!apiBase) return mockApi.overview();
    return request<string[]>("/overview");
  },

  listDocs() {
    if (!apiBase) return mockApi.listDocs();
    return request<DocRecord[]>("/docs");
  },

  getDoc(id: string) {
    if (!apiBase) return mockApi.getDoc(id);
    return request<DocRecord>(`/docs/${id}`);
  },

  async uploadDoc(file: File) {
    if (!apiBase) return mockApi.uploadDoc(file);
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`${apiBase}/docs`, {
      method: "POST",
      headers: headers({}),
      body,
      credentials: readAccessToken() ? "omit" : "include",
    });
    if (!res.ok) throw new Error("Upload failed.");
    return (await res.json()) as DocRecord;
  },

  createDiagnosis() {
    if (!apiBase) return mockApi.createDiagnosis();
    return request<DiagnosisRecord>("/diagnosis", { method: "POST" });
  },

  getDiagnosis() {
    if (!apiBase) return mockApi.getDiagnosis();
    return request<DiagnosisRecord | null>("/diagnosis");
  },
};
