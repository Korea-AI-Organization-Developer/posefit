import type { Metadata } from "next";

export const metadata: Metadata = { title: "설정" };

/* SCR-11 스텁 — 계정 정보/소셜 연동/얼굴 재등록/탈퇴가 들어온다 */
export default function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">설정</h1>
      <p className="mt-2 text-sm text-text-muted">
        SCR-11 — 설정 도메인 단계에서 구현 예정
      </p>
    </div>
  );
}
