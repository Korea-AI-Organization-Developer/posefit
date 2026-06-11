import type { Metadata } from "next";

export const metadata: Metadata = { title: "리포트" };

/* SCR-10 스텁 — 히스토리/일·주·월간 리포트가 들어온다 */
export default function ReportsPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">리포트</h1>
      <p className="mt-2 text-sm text-text-muted">
        SCR-10 — 보고 도메인 단계에서 구현 예정
      </p>
    </div>
  );
}
