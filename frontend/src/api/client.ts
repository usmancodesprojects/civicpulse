import type { Complaint, ComplaintCreate, ComplaintPage, Stats, Status } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<{ data: T; response: Response }> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({ detail: response.statusText }))) as {
      detail?: string;
      errors?: { field: string; message: string }[];
    };
    const fieldErrors = payload.errors?.map((item) => `${item.field}: ${item.message}`).join("; ");
    throw new ApiError(fieldErrors || payload.detail || "Request failed", response.status);
  }
  return { data: (await response.json()) as T, response };
}

export const api = {
  createComplaint: (payload: ComplaintCreate) =>
    request<Complaint>("/api/complaints", { method: "POST", body: JSON.stringify(payload) }).then(
      (result) => result.data,
    ),
  listComplaints: (query: URLSearchParams) =>
    request<ComplaintPage>(`/api/complaints?${query}`).then((result) => result.data),
  updateStatus: (id: string, status: Status) =>
    request<Complaint>(`/api/complaints/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }).then((result) => result.data),
  stats: () =>
    request<Stats>("/api/stats").then(({ data, response }) => ({
      data,
      cache: response.headers.get("X-Cache") ?? "UNKNOWN",
    })),
};
