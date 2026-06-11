import type { Metadata } from "next";

export const metadata: Metadata = { title: "운동하기" };

/* SCR-06~09 스텁 — 운동 선택/정답 영상/실행/결과 플로우가 들어온다 */
export default function WorkoutPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">운동하기</h1>
      <p className="mt-2 text-sm text-text-muted">
        SCR-06~09 — 운동 도메인 단계에서 구현 예정
      </p>
    </div>
  );
}
