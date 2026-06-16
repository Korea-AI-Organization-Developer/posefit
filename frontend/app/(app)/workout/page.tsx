import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Dumbbell } from "lucide-react";

import { formatScore } from "@/lib/format";
// ← 이번에 바꾼 줄: 가짜 데이터(@/lib/mock/exercises) → 진짜 API(@/lib/api/exercises)로 교체.
//    getExercises 함수의 모양(시그니처)이 mock과 api가 똑같아서, 이 import 한 줄만 바꾸면
//    아래 화면 코드는 그대로 둔 채 진짜 데이터가 나온다.
import { getExercises, type ExerciseType } from "@/lib/api/exercises";

export const metadata: Metadata = { title: "운동 선택" };

const TYPE_LABEL: Record<ExerciseType, string> = {
  dynamic: "동적",
  static: "정적",
};

/* openapi nameEn → /public/exercises 픽토그램 (대시보드 타일과 동일 매핑) */
const EXERCISE_IMAGE: Record<string, string> = {
  Lunge: "/exercises/lunge.png",
  Plank: "/exercises/plank.png",
  "Push-up": "/exercises/pushup.png",
  "Overhead Press": "/exercises/overhead-press.png",
};

/*
 * SCR-06 운동 선택 (EX-01). 카드 클릭 → /workout/[id] 정답 영상.
 * getExercises() → GET /api/v1/exercises (백엔드 준비 후 lib/api 로 교체).
 */
// WorkoutPage: /workout 페이지를 그리는 컴포넌트(화면 함수).
// async function = "서버 컴포넌트". 브라우저가 아니라 서버에서 미리 그려서 보내므로,
//                  함수 안에서 바로 await로 데이터를 불러올 수 있다.
export default async function WorkoutPage() {
  // getExercises()로 운동 목록을 받아온다(API 호출). await = 응답이 올 때까지 기다림.
  // { items } = 응답 객체에서 items 배열만 꺼내 쓴다(구조 분해 할당).
  const { items } = await getExercises();

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">운동 선택</h1>
        <p className="mt-1 text-sm text-text-muted">
          정답 영상과 비교하며 자세를 교정할 운동을 골라요
        </p>
      </header>

      <ul className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {/* items.map: 받아온 운동 배열을 하나씩 돌며(exercise) 카드 하나(<li>)씩 만든다. */}
        {items.map((exercise) => {
          // 운동 영문 이름으로 픽토그램 이미지 경로를 찾는다. 없으면 undefined(아래에서 아령 아이콘으로 대체).
          const src = exercise.nameEn
            ? EXERCISE_IMAGE[exercise.nameEn]
            : undefined;
          return (
            // key={exercise.id}: 리스트의 각 항목을 구분하는 고유값(리액트 필수). 운동 id를 쓴다.
            <li key={exercise.id} className="flex">
              {/* 카드 클릭 시 이동할 주소. /workout/1 처럼 운동 id가 들어간 상세 페이지로 간다. */}
              <Link
                href={`/workout/${exercise.id}`}
                className="flex flex-1 flex-col rounded-md border border-border bg-surface p-4 transition-colors duration-150 ease-out hover:border-border-strong hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                {src ? (
                  <div className="relative min-h-32 flex-1">
                    <Image
                      src={src}
                      alt=""
                      fill
                      sizes="(max-width: 640px) 45vw, 240px"
                      className="object-contain p-2"
                    />
                  </div>
                ) : (
                  <div className="flex min-h-32 flex-1 items-center justify-center text-text-subtle">
                    <Dumbbell className="size-12" aria-hidden />
                  </div>
                )}
                <div className="mt-2">
                  <p className="text-sm font-medium">
                    {exercise.nameKo}
                    {exercise.nameEn && (
                      <span className="ml-1.5 text-xs font-normal text-text-subtle">
                        {exercise.nameEn}
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-text-subtle">
                    {TYPE_LABEL[exercise.exerciseType]}
                    {exercise.userAvgScore != null
                      ? ` · 평균 ${formatScore(exercise.userAvgScore)}점`
                      : " · 기록 없음"}
                  </p>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
