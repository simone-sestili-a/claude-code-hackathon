import type {
  ChatApiResponse,
  FollowUpApiResponse,
  DocumentProcessingResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Errore ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore JSON parse error
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function sendChatMessage(params: {
  message: string;
  sessionId?: string;
  pdf?: File;
}): Promise<ChatApiResponse> {
  const form = new FormData();
  form.append("message", params.message);
  if (params.sessionId) form.append("session_id", params.sessionId);
  if (params.pdf) form.append("pdf", params.pdf);

  const res = await fetch(`${API_BASE}/chat`, { method: "POST", body: form });
  return handleResponse<ChatApiResponse>(res);
}

export async function sendFollowUp(params: {
  sessionId: string;
  question: string;
}): Promise<FollowUpApiResponse> {
  const res = await fetch(`${API_BASE}/followup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: params.sessionId, question: params.question }),
  });
  return handleResponse<FollowUpApiResponse>(res);
}

export async function processDocument(params: {
  pdf?: File;
  pagesJson?: string;
  flowType?: string;
  sessionId?: string;
}): Promise<DocumentProcessingResponse> {
  const form = new FormData();
  form.append("flow_type", params.flowType ?? "ercole");
  if (params.pdf) form.append("pdf", params.pdf);
  if (params.pagesJson) form.append("pages_json", params.pagesJson);
  if (params.sessionId) form.append("session_id", params.sessionId);

  const res = await fetch(`${API_BASE}/process-document`, { method: "POST", body: form });
  return handleResponse<DocumentProcessingResponse>(res);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/`, {
      signal: AbortSignal.timeout(4000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export function getApiBase(): string {
  return API_BASE;
}
