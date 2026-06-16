import { requireStep } from "@/lib/auth/guard";
import { TermsForm } from "./terms-form";

/* SCR-02 약관 동의 — 가입 1단계. agreements_required 단계에서만 머문다. */
export default async function TermsPage() {
  await requireStep("agreements_required");
  return <TermsForm />;
}
