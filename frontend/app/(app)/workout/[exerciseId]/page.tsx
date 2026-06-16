import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Play } from "lucide-react";

import { Card, CardBody, CardHeader } from "@/components/ui";
import { getExercise, type ExerciseType } from "@/lib/mock/exercises";
import { StartButton } from "./start-button";

export const metadata: Metadata = { title: "정답 영상" };

const TYPE_LABEL: Record<ExerciseType, string> = {
  dynamic: "동적 · 반복 횟수 측정",
  static: "정적 · 유지 시간 측정",
};

/*
 * SCR-07 정답(모범) 영상 보기 (EX-02). "운동 시작하기" → createSession 후 실행 화면.
 * getExercise() → GET /api/v1/exercises/{id} (백엔드 준비 후 lib/api 로 교체).
 */
export default async function ExerciseDetailPage({
  params,
}: {
  params: Promise<{ exerciseId: string }>;
}) {
  const { exerciseId } = await params;
  const exercise = await getExercise(Number(exerciseId));
  if (!exercise) notFound();

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="flex items-center gap-3 border-b border-border pb-4">
        <Link
          href="/workout"
          aria-label="운동 선택으로"
          className="inline-flex size-9 items-center justify-center rounded-sm text-text-muted transition-colors duration-150 ease-out hover:bg-surface-muted hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent [&_svg]:size-4"
        >
          <ArrowLeft aria-hidden />
        </Link>
        <div>
          <h1 className="text-lg font-semibold">
            {exercise.nameKo}
            {exercise.nameEn && (
              <span className="ml-2 text-sm font-normal text-text-subtle">
                {exercise.nameEn}
              </span>
            )}
          </h1>
        </div>
        <span className="ml-auto text-xs text-text-subtle">
          {TYPE_LABEL[exercise.exerciseType]}
        </span>
      </header>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        {/* 정답 영상 — 영상이 없으면 poster 플레이스홀더 */}
        <div className="overflow-hidden rounded-md border border-border bg-surface">
          {exercise.referenceVideoUrl ? (
            <video
              controls
              src={exercise.referenceVideoUrl}
              className="aspect-video w-full bg-black"
            />
          ) : (
            <div className="flex aspect-video w-full flex-col items-center justify-center gap-3 bg-surface-muted">
              <span className="inline-flex size-14 items-center justify-center rounded-full border border-border-strong text-text-subtle [&_svg]:size-6">
                <Play aria-hidden />
              </span>
              <p className="text-sm text-text-subtle">정답 영상 준비 중이에요</p>
            </div>
          )}
        </div>

        {/* 설명 + 운동 시작 */}
        <div className="flex flex-col gap-4">
          <Card className="flex-1">
            <CardHeader>
              <h2 className="text-sm font-semibold">운동 설명</h2>
            </CardHeader>
            <CardBody>
              <p className="text-sm leading-relaxed text-text-muted">
                {exercise.description ?? "설명이 준비 중이에요."}
              </p>
            </CardBody>
          </Card>

          <StartButton exerciseId={exercise.id} />
          <p className="text-center text-xs text-text-subtle">
            시작하면 카메라가 켜지고 얼굴 인식 후 분석이 진행돼요
          </p>
        </div>
      </div>
    </div>
  );
}
