import type { DiagnosisRecord, DocRecord, Profile, SessionUser } from "../types";

const KEY = "anketa.mock.v1";

type Store = {
  users: Array<{
    id: string;
    email: string;
    password: string;
    profile: Profile | null;
  }>;
  sessionUserId: string | null;
  docs: DocRecord[];
  diagnosis: DiagnosisRecord | null;
  overview: string[];
};

const emptyProfile = (): Profile => ({
  heightCm: "",
  weightKg: "",
  age: "",
  sex: "",
  comments: "",
});

const seed = (): Store => ({
  users: [],
  sessionUserId: null,
  docs: [
    {
      id: "doc-1",
      title: "doc 1",
      kind: "image",
      previewUrl: "",
      extracted: {
        type: "lab",
        date: "2026-03-12",
        hemoglobin: "132 g/L",
        glucose: "5.1 mmol/L",
      },
    },
    {
      id: "doc-2",
      title: "doc 2",
      kind: "pdf",
      previewUrl: "",
      extracted: {
        type: "ultrasound",
        organ: "thyroid",
        note: "No focal lesions described",
      },
    },
    {
      id: "doc-3",
      title: "doc 3",
      kind: "image",
      previewUrl: "",
      extracted: {
        type: "prescription",
        drug: "levothyroxine",
        dose: "50 mcg",
      },
    },
  ],
  diagnosis: null,
  overview: [
    "Your profile is incomplete until it is saved.",
    "Upload lab scans or PDFs, then generate a diagnosis.",
    "Extracted fields appear on each document.",
  ],
});

function read(): Store {
  const raw = localStorage.getItem(KEY);
  if (!raw) {
    const next = seed();
    localStorage.setItem(KEY, JSON.stringify(next));
    return next;
  }
  return JSON.parse(raw) as Store;
}

function write(store: Store) {
  localStorage.setItem(KEY, JSON.stringify(store));
}

function toUser(row: Store["users"][number]): SessionUser {
  return {
    id: row.id,
    email: row.email,
    profileComplete: Boolean(
      row.profile?.heightCm && row.profile.weightKg && row.profile.age && row.profile.sex,
    ),
  };
}

export const mockApi = {
  async signup(email: string, password: string): Promise<SessionUser> {
    const store = read();
    if (store.users.some((u) => u.email === email)) {
      throw new Error("An account with this email already exists.");
    }
    const user = {
      id: crypto.randomUUID(),
      email,
      password,
      profile: emptyProfile(),
    };
    store.users.push(user);
    store.sessionUserId = user.id;
    write(store);
    return toUser(user);
  },

  async login(email: string, password: string): Promise<SessionUser> {
    const store = read();
    const user = store.users.find((u) => u.email === email && u.password === password);
    if (!user) throw new Error("Email or password is incorrect.");
    store.sessionUserId = user.id;
    write(store);
    return toUser(user);
  },

  async logout(): Promise<void> {
    const store = read();
    store.sessionUserId = null;
    write(store);
  },

  async me(): Promise<SessionUser | null> {
    const store = read();
    const user = store.users.find((u) => u.id === store.sessionUserId);
    return user ? toUser(user) : null;
  },

  async getProfile(): Promise<Profile> {
    const store = read();
    const user = store.users.find((u) => u.id === store.sessionUserId);
    if (!user) throw new Error("Sign in required.");
    return user.profile ?? emptyProfile();
  },

  async saveProfile(profile: Profile): Promise<SessionUser> {
    const store = read();
    const user = store.users.find((u) => u.id === store.sessionUserId);
    if (!user) throw new Error("Sign in required.");
    user.profile = profile;
    store.overview = [
      `Age ${profile.age}, ${profile.sex || "unspecified sex"}.`,
      `Height ${profile.heightCm} cm, weight ${profile.weightKg} kg.`,
      profile.comments.trim() || "No extra comments on file.",
    ];
    write(store);
    return toUser(user);
  },

  async overview(): Promise<string[]> {
    return read().overview;
  },

  async listDocs(): Promise<DocRecord[]> {
    return read().docs;
  },

  async getDoc(id: string): Promise<DocRecord> {
    const doc = read().docs.find((d) => d.id === id);
    if (!doc) throw new Error("Document not found.");
    return doc;
  },

  async uploadDoc(file: File): Promise<DocRecord> {
    const store = read();
    const kind = file.type.includes("pdf") ? "pdf" : "image";
    const doc: DocRecord = {
      id: crypto.randomUUID(),
      title: file.name.replace(/\.[^.]+$/, "") || "untitled",
      kind,
      previewUrl: URL.createObjectURL(file),
      extracted: {
        filename: file.name,
        bytes: file.size,
        uploadedAt: new Date().toISOString(),
      },
    };
    store.docs = [doc, ...store.docs];
    write(store);
    return doc;
  },

  async createDiagnosis(): Promise<DiagnosisRecord> {
    const store = read();
    const user = store.users.find((u) => u.id === store.sessionUserId);
    const diagnosis: DiagnosisRecord = {
      id: crypto.randomUUID(),
      title: "Working diagnosis",
      summary:
        "Generated from your profile and uploaded documents. This is a demo summary until the live model is wired.",
      findings: [
        user?.profile?.comments
          ? `Patient note: ${user.profile.comments}`
          : "No comments in your profile.",
        `${store.docs.length} document(s) on file for review.`,
        "Correlate labs with symptoms before any treatment change.",
      ],
    };
    store.diagnosis = diagnosis;
    write(store);
    return diagnosis;
  },

  async getDiagnosis(): Promise<DiagnosisRecord | null> {
    return read().diagnosis;
  },
};
