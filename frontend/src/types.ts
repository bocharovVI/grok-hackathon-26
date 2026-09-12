export type Sex = "female" | "male" | "other" | "";

export type Profile = {
  heightCm: string;
  weightKg: string;
  age: string;
  sex: Sex;
  comments: string;
};

export type SessionUser = {
  id: string;
  email: string;
  profileComplete: boolean;
};

/** Auth payload from a public API on a different Render origin. */
export type AuthSession = SessionUser & {
  token?: string;
};

export type DocRecord = {
  id: string;
  title: string;
  kind: "image" | "pdf";
  previewUrl: string;
  extracted: Record<string, unknown>;
};

export type DiagnosisRecord = {
  id: string;
  title: string;
  summary: string;
  findings: string[];
};
