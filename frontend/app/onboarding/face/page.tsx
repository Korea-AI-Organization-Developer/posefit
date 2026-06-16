import { requireStep } from "@/lib/auth/guard";
import { FaceCapture } from "./face-capture";

/* SCR-04 얼굴 등록 — 가입 3단계. face_required 단계에서만 머문다. 완료 시 complete → 대시보드. */
export default async function FacePage() {
  await requireStep("face_required");
  return <FaceCapture />;
}
