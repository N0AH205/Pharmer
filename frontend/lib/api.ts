import type { QueryRequest, QueryResponse } from "./types";

const API_BASE = "/api";

export async function queryDrug(smiles: string): Promise<QueryResponse> {
  const body: QueryRequest = { smiles };

  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    return { success: false, error: text || "Request failed" };
  }

  return res.json();
}
