import { listLlmModels } from "@/lib/mock/admin-api";
import { LlmManager } from "./llm-manager";

export const metadata = { title: "LLM 모델" };

export default async function LlmPage() {
  const models = await listLlmModels();
  return <LlmManager initial={models} />;
}
