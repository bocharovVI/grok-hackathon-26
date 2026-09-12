import type { AuthSession, DiagnosisRecord, DocRecord, Profile, SessionUser } from "../types";
import { readAccessToken, writeAccessToken } from "./authToken";
import { mockApi } from "./mock";

const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const useMock = import.meta.env.VITE_USE_MOCK === "true";

async function responseError(res: Response): Promise<Error> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  return new Error(typeof detail === "string" ? detail : Array.isArray(detail)
    ? detail.map((item: { msg: string }) => item.msg).join("; ")
    : `Request failed (${res.status})`);
}

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
  if (!apiBase) throw new Error("API URL is not configured. Set VITE_API_URL and rebuild.");
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: headers(init, Boolean(init?.body)),
    credentials: "omit",
  });
  if (!res.ok) {
    throw await responseError(res);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  usesMock: useMock,

  async signup(email: string, password: string) {
    if (useMock) return mockApi.signup(email, password);
    return remember(
      await request<AuthSession>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    );
  },

  async login(email: string, password: string) {
    if (useMock) return mockApi.login(email, password);
    return remember(
      await request<AuthSession>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    );
  },

  async logout() {
    if (useMock) return mockApi.logout();
    if (apiBase && readAccessToken()) {
      const res = await fetch(`${apiBase}/auth/logout`, {
        method: "POST", headers: headers(), credentials: "omit",
      });
      if (!res.ok && res.status !== 401) throw await responseError(res);
    }
    writeAccessToken(null);
  },

  me() {
    if (useMock) return mockApi.me();
    return request<SessionUser | null>("/me");
  },

  getProfile() {
    if (useMock) return mockApi.getProfile();
    return request<Profile>("/me/profile");
  },

  saveProfile(profile: Profile) {
    if (useMock) return mockApi.saveProfile(profile);
    return request<SessionUser>("/me/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    });
  },

  overview() {
    if (useMock) return mockApi.overview();
    return request<string[]>("/overview");
  },

  listDocs() {
    if (useMock) return mockApi.listDocs();
    return request<DocRecord[]>("/docs");
  },

  getDoc(id: string) {
    if (useMock) return mockApi.getDoc(id);
    return request<DocRecord>(`/docs/${id}`);
  },

  async uploadDoc(file: File) {
    if (useMock) return mockApi.uploadDoc(file);
    if (!apiBase) throw new Error("API URL is not configured.");
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`${apiBase}/docs`, {
      method: "POST",
      headers: headers({}),
      body,
      credentials: "omit",
    });
    if (!res.ok) throw await responseError(res);
    return (await res.json()) as DocRecord;
  },

  createDiagnosis() {
    if (useMock) return mockApi.createDiagnosis();
    return request<DiagnosisRecord | null>("/diagnosis", { method: "POST" });
  },

  getDiagnosis() {
    if (useMock) return mockApi.getDiagnosis();
    return request<DiagnosisRecord | null>("/diagnosis");
  },

  async previewDoc(doc: DocRecord): Promise<string> {
    if (useMock) return doc.previewUrl;
    const res = await fetch(`${apiBase}/docs/${encodeURIComponent(doc.id)}/file`, {
      headers: headers(), credentials: "omit",
    });
    if (!res.ok) throw await responseError(res);
    return URL.createObjectURL(await res.blob());
  },
};
