import { apiFetch } from "@/lib/api/server";
import type { LlmModel, LlmProvider } from "@/lib/api/types";

export async function listLlmModels(): Promise<LlmModel[]> {
  return apiFetch<LlmModel[]>("/admin/llm/models");
}

export interface LlmModelCreatePayload {
  provider: LlmProvider;
  modelName: string;
  displayName: string;
  params?: Record<string, unknown> | null;
}

export async function createLlmModel(payload: LlmModelCreatePayload): Promise<LlmModel> {
  return apiFetch<LlmModel>("/admin/llm/models", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
