import { redirect } from "next/navigation";

/* 얼굴 등록은 온보딩에서 제거됨 — 운동 시작 시 face-gate 에서 처리한다. */
export default function FacePage() {
  redirect("/dashboard");
}
