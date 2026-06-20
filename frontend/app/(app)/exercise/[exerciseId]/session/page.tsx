import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { getExerciseDetail } from "@/lib/api/exercises";
import { WorkoutLive } from "./workout-live";

export const metadata: Metadata = { title: "운동 실행" };

/*
 * SCR-08 운동 실행 + SCR-09 결과. 실시간 분석은 클라이언트(WorkoutLive)가 시뮬한다.
 * 서버는 운동 메타데이터만 내려준다. sessionId 는 SCR-07 createSession 결과(?s=).
 */
export default async function SessionPage({
  params,
  searchParams,
}: {
  params: Promise<{ exerciseId: string }>;
  searchParams: Promise<{ s?: string }>;
}) {
  const { exerciseId } = await params;
  const { s } = await searchParams;
  const exercise = await getExerciseDetail(Number(exerciseId));
  if (!exercise) notFound();

  return (
    <WorkoutLive exercise={exercise} initialSessionId={s ? Number(s) : null} />
  );
}
