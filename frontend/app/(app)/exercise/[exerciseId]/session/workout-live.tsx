"use client";

import Link from "next/link";
import { useEffect, useRef, useState, useTransition } from "react";
import { AlertTriangle, ArrowLeft, Check, ChevronDown, ChevronUp, Loader2, Play, Sparkles, Square } from "lucide-react";

import {
  Badge,
  Button,
  buttonClasses,
  Card,
  CardBody,
  CardHeader,
  type BadgeTone,
} from "@/components/ui";
import {
  CameraView,
  type CameraPermission,
  type CameraViewHandle,
} from "@/components/camera/camera-view";
import { cn } from "@/lib/utils";
import { formatScore } from "@/lib/format";
import type { ExerciseDetailResponse } from "@/lib/api/exercises";
import type { Feedback, FeedbackSeverity } from "@/lib/api/types";
import {
  stopSet,
  summarizeExercise,
  type ExerciseFeedbackSummary,
} from "@/lib/api/workout-client";
import { logVideoFile } from "./actions";

/*
 * SCR-08 운동 실행(멀티 세트) + SCR-09 결과.
 *   START → 영상 녹화 → STOP = 세트 1회 → :stop 으로 그 세트 피드백 1건 받기.
 *   세트를 원하는 만큼 반복(아래에 세트 1·2·3… 누적) → "운동 마치기" 로 :summary 호출 →
 *   이번 묶음 전체 종합 피드백을 받는다.
 * 포즈 추정·채점은 백엔드 담당(현재 placeholder). 카메라 녹화·업로드는 실제 동작.
 */
type Phase = "idle" | "countdown" | "recording" | "processing";

const SEVERITY: Record<FeedbackSeverity, { tone: BadgeTone; label: string }> = {
  info: { tone: "neutral", label: "정보" },
  warning: { tone: "warning", label: "주의" },
  critical: { tone: "danger", label: "위험" },
};

interface SetResult {
  setNumber: number;
  sessionId: number;
  score: number | null;
  feedback: Feedback;
}

/** mm:ss */
function clock(totalSec: number): string {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function WorkoutLive({
  exercise,
  initialSessionId,
}: {
  exercise: ExerciseDetailResponse;
  initialSessionId?: number | null;
}) {
  const cameraRef = useRef<CameraViewHandle>(null);
  const recordStartRef = useRef<string | null>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [permission, setPermission] = useState<CameraPermission>("prompt");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [sets, setSets] = useState<SetResult[]>([]);
  const [summary, setSummary] = useState<ExerciseFeedbackSummary | null>(null);
  const [finishing, startFinish] = useTransition();

  const [countdown, setCountdown] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoFilename, setVideoFilename] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  const granted = permission === "granted";

  // 녹화 중 1초 틱 — 경과 시간 표시.
  useEffect(() => {
    if (phase !== "recording") return;
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [phase]);

  async function handleStart() {
    setError(null);
    // 5초 카운트다운
    setPhase("countdown");
    for (let i = 5; i >= 1; i--) {
      setCountdown(i);
      await new Promise((r) => setTimeout(r, 1000));
    }
    setCountdown(0);
    setElapsed(0);
    recordStartRef.current = new Date().toISOString();
    cameraRef.current?.startRecording();
    setPhase("recording");
  }

  async function handleStop() {
    setPhase("processing");
    const startAt = recordStartRef.current ?? new Date().toISOString();
    const endAt = new Date().toISOString();
    try {
      const recorded = await cameraRef.current?.stopRecording() ?? null;
      if (recorded) {
        setVideoFilename(recorded.filename);
        const url = URL.createObjectURL(recorded.blob);
        setVideoUrl(url);
        await logVideoFile(recorded.filename, recorded.blob.size);
      } else throw new Error("녹화 영상을 가져오지 못했어요. 다시 시도해 주세요.");

      const res = await stopSet({
        exerciseId: exercise.id,
        startAt,
        endAt,
        blob: recorded.blob,
        filename: recorded.filename,
      });
      setSets((prev) => [
        ...prev,
        {
          setNumber: prev.length + 1,
          sessionId: res.sessionId,
          score: res.score,
          feedback: res.feedback,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "세트 분석에 실패했어요.");
    } finally {
      setPhase("idle");
    }
  }

  function handleFinish() {
    setError(null);
    startFinish(async () => {
      try {
        const result = await summarizeExercise(
          exercise.id,
          sets.map((s) => s.sessionId),
        );
        setSummary(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "종합 피드백 생성에 실패했어요.");
      }
    });
  }

  // ─── SCR-09 운동 종합 결과 ────────────────────────────────────────────────
  if (summary) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-10">
        <header className="flex items-center gap-3 border-b border-border pb-4">
          <h1 className="text-lg font-semibold">운동 종합 결과</h1>
          <span className="ml-auto text-xs text-text-subtle tabular-nums">
            {exercise.nameKo} · {summary.setCount}세트
          </span>
        </header>

        <Card className="mt-8 border-accent/40">
          <CardHeader className="flex items-center gap-2">
            <Sparkles className="size-4 text-accent" aria-hidden />
            <h2 className="text-sm font-semibold">AI 종합 피드백</h2>
          </CardHeader>
          <CardBody>
            <p className="text-sm leading-relaxed">{summary.content}</p>
          </CardBody>
        </Card>

        <h3 className="mt-8 text-sm font-semibold text-text-muted">세트별 피드백</h3>
        <SetList sets={sets} className="mt-3" />

        <div className="mt-8 flex gap-3">
          <Link
            href="/dashboard"
            className={buttonClasses("secondary", "md", "flex-1")}
          >
            대시보드로
          </Link>
          <Link
            href={`/exercise/${exercise.id}`}
            className={buttonClasses("primary", "md", "flex-1")}
          >
            이 운동 다시 보기
          </Link>
        </div>
      </div>
    );
  }

  // ─── SCR-08 실행(멀티 세트) ───────────────────────────────────────────────
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="flex items-center gap-3 border-b border-border pb-4">
        <Link
          href={`/exercise/${exercise.id}`}
          aria-label="정답 영상으로"
          className="inline-flex size-9 items-center justify-center rounded-sm text-text-muted transition-colors duration-150 ease-out hover:bg-surface-muted hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent [&_svg]:size-4"
        >
          <ArrowLeft aria-hidden />
        </Link>
        <h1 className="text-lg font-semibold">{exercise.nameKo}</h1>
        <span
          className={cn(
            "ml-auto inline-flex items-center gap-1.5 text-xs",
            granted ? "text-success" : "text-text-subtle",
          )}
        >
          <span
            className={cn(
              "size-1.5 rounded-full",
              granted ? "bg-success" : "bg-text-subtle",
            )}
          />
          {granted ? "카메라 연결됨" : "카메라 준비 중"}
        </span>
      </header>

      {error && (
        <p className="mt-4 rounded-sm bg-danger-soft px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_280px]">
        <CameraView
          ref={cameraRef}
          onPermissionChange={setPermission}
          overlay={<CameraOverlay phase={phase} countdown={countdown} />}
          className="aspect-video w-full"
        />

        <div className="flex flex-col gap-3">
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="text-xs text-text-subtle">
              {phase === "recording" ? "녹화 중" : "현재 세트"}
            </p>
            <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">
              {phase === "recording" ? clock(elapsed) : `세트 ${sets.length + 1}`}
            </p>
          </div>

          {sets.length > 0 && (
            <div className="rounded-md border border-border bg-surface p-4">
              <SetLast sets={sets} />
            </div>
          )}

          {phase === "recording" ? (
            <button
              type="button"
              onClick={handleStop}
              className="mt-1 flex w-full items-center justify-center gap-2 rounded-md border-2 border-danger bg-surface py-5 text-lg font-semibold text-danger transition-colors duration-150 ease-out hover:bg-danger-soft [&_svg]:size-5"
            >
              <Square aria-hidden />
              STOP
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStart}
              disabled={!granted || phase === "processing"}
              className="mt-1 flex w-full items-center justify-center gap-2 rounded-md bg-accent py-5 text-lg font-semibold text-white transition-colors duration-150 ease-out hover:bg-accent-hover disabled:opacity-50 [&_svg]:size-5"
            >
              {phase === "processing" ? (
                <Loader2 className="animate-spin" aria-hidden />
              ) : (
                <Play aria-hidden />
              )}
              {sets.length === 0 ? "START" : "다음 세트"}
            </button>
          )}

          {sets.length > 0 && (
            <Button
              variant="secondary"
              className="w-full"
              loading={finishing}
              disabled={phase !== "idle"}
              onClick={handleFinish}
            >
              운동 마치기 ({sets.length}세트)
            </Button>
          )}

          <p className="text-center text-xs text-text-subtle">
            {phase === "recording"
              ? "STOP을 누르면 이 세트를 분석해요"
              : phase === "countdown"
                ? "카메라를 바라보고 준비해 주세요"
                : phase === "processing"
                  ? "세트를 분석하고 있어요…"
                  : !granted
                    ? "카메라 권한을 허용해 주세요"
                    : sets.length === 0
                      ? "START → 한 세트를 녹화하고 피드백을 받아요"
                      : "다음 세트를 하거나, 운동을 마치고 종합 피드백을 받아요"}
          </p>
        </div>
      </div>
    </div>
  );
}

/* 가장 최근 세트 1건 — 와이어프레임 plank_fullscreen_redesign.html 기준 */
function SetLast({ sets, className }: { sets: SetResult[]; className?: string }) {
  const [expanded, setExpanded] = useState(false);

  const last = sets[sets.length - 1];
  if (!last) return null;

  const { feedback } = last;

  // 기본 3개 표시, 나머지는 접기/펼치기
  const visibleTimeline = feedback.timeline
    ? feedback.timeline.slice(0, expanded ? undefined : 3)
    : [];
  // 숨겨진 구간 수
  const hiddenCount = feedback.timeline
    ? Math.max(0, feedback.timeline.length - 3)
    : 0;

  return (
    <div className={cn(className)}>
      {/* 헤더: "N 세트 피드백" (좌) + 심각도 뱃지 (우) */}
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm text-text-muted">{last.setNumber} 세트 피드백</span>
        <Badge tone={SEVERITY[feedback.severity].tone}>
          {SEVERITY[feedback.severity].label}
        </Badge>
      </div>

      {/* 요약 카드: summary 있으면 summary, 없으면 content 폴백. timeline 있으면 바 표시 */}
      <div className="mb-2.5 rounded-lg border border-border bg-surface px-4 py-3.5">
        <p className="text-sm leading-relaxed">
          {/* feedback.summary: 백엔드 확정 전 임시 필드명 */}
          {feedback.summary ?? feedback.content}
        </p>

        {/* 타임라인 바 — feedback.timeline 데이터 있을 때만 렌더 */}
        {feedback.timeline && feedback.timeline.length > 0 && (
          <>
            <div className="mt-2.5 flex h-[9px] overflow-hidden rounded-full">
              {feedback.timeline.map((seg, i) => (
                // seg.isGood: true=성공 구간(초록), false=오류 구간(빨강)
                <div
                  key={i}
                  className={cn("flex-1", seg.isGood ? "bg-success" : "bg-danger")}
                />
              ))}
            </div>
            <div className="mt-1 flex justify-between text-xs text-text-subtle">
              {/* 첫 구간 레이블 / 마지막 구간 레이블 */}
              {/* seg.timestamp: 백엔드 확정 전 임시 필드명 */}
              <span>{feedback.timeline[0].timestamp}</span>
              <span>{feedback.timeline[feedback.timeline.length - 1].timestamp}</span>
            </div>
          </>
        )}
      </div>

      {/* 구간 카드 목록 — feedback.timeline 데이터 있을 때만 렌더 */}
      {feedback.timeline && feedback.timeline.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {visibleTimeline.map((seg, i) => (
            <div
              key={i}
              className={cn(
                "flex items-start gap-2 rounded-r-md border border-border bg-surface px-2.5 py-2",
                // seg.isGood: true=성공(초록 좌측 테두리), false=오류(빨강 좌측 테두리)
                seg.isGood ? "border-l-[3px] border-l-success" : "border-l-[3px] border-l-danger",
              )}
            >
              {seg.isGood ? (
                <Check className="mt-0.5 size-4 shrink-0 text-success" aria-hidden />
              ) : (
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-danger" aria-hidden />
              )}
              <div>
                {/* seg.timestamp: 구간 시각 레이블. 백엔드 확정 전 임시 필드명 */}
                <p className="text-xs font-medium">{seg.timestamp}</p>
                {/* seg.comment: 구간 설명 텍스트. 백엔드 확정 전 임시 필드명 */}
                <p className="text-xs text-text-subtle">{seg.comment}</p>
              </div>
            </div>
          ))}

          {/* 숨겨진 구간이 있을 때만 펼치기/접기 버튼 표시 */}
          {hiddenCount > 0 && (
            <button
              type="button"
              onClick={() => setExpanded((e) => !e)}
              className="mt-2 flex w-full items-center justify-center gap-1 py-1.5 text-xs text-text-muted transition-colors hover:text-text"
            >
              {expanded ? (
                <ChevronUp className="size-3.5" aria-hidden />
              ) : (
                <ChevronDown className="size-3.5" aria-hidden />
              )}
              {expanded ? "구간 접기" : `구간 ${hiddenCount}개 더 보기`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* 세트 카드 목록 — 세트 N · 점수 · 피드백 */
function SetList({ sets, className }: { sets: SetResult[]; className?: string }) {
  return (
    <ul className={cn("space-y-3", className)}>
      {sets.map((s) => (
        <li key={s.sessionId}>
          <Card>
            <CardBody className="flex gap-3 py-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge tone={SEVERITY[s.feedback.severity].tone}>
                    {SEVERITY[s.feedback.severity].label}
                  </Badge>
                  <span className="text-xs text-text-subtle">
                    {s.feedback.generatedBy === "llm" ? "AI 분석" : "규칙 기반"}
                  </span>
                  {s.score != null && (
                    <span className="ml-auto font-mono text-sm tabular-nums text-text-muted">
                      {formatScore(s.score)}점
                    </span>
                  )}
                </div>
                <p className="mt-1.5 text-sm leading-relaxed">
                  {s.feedback.content}
                </p>
              </div>
            </CardBody>
          </Card>
        </li>
      ))}
    </ul>
  );
}

/* 카메라 위 가이드 오버레이 */
function CameraOverlay({ phase, countdown }: { phase: Phase; countdown: number }) {
  if (phase === "countdown") {
    return (
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/60">
        <div className="flex flex-col items-center gap-3">
          <span className="font-mono text-[9rem] font-black leading-none text-white drop-shadow-[0_0_40px_rgba(255,255,255,0.5)]">
            {countdown}
          </span>
          <span className="rounded-full border border-white/30 px-4 py-1 text-sm font-medium tracking-widest text-white/80 uppercase">
            준비
          </span>
        </div>
      </div>
    );
  }
  if (phase === "recording") {
    return (
      <>
        <div className="pointer-events-none absolute inset-[12%] rounded-md border-2 border-dashed border-accent/70" />
        <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-1.5 rounded-sm bg-black/70 px-2 py-1 font-mono text-[10px] text-white">
          <span className="size-1.5 animate-pulse rounded-full bg-danger" />
          REC
        </div>
      </>
    );
  }
  if (phase === "processing") {
    return (
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/55">
        <div className="flex items-center gap-2 rounded-md bg-surface px-4 py-3 text-sm font-medium shadow-sm">
          <Loader2 className="size-4 animate-spin text-accent" aria-hidden />
          세트 분석 중…
        </div>
      </div>
    );
  }
  return (
    <div className="pointer-events-none absolute inset-0 flex items-end justify-center pb-4">
      <span className="rounded-sm bg-black/60 px-2 py-1 text-xs text-white">
        START를 누르면 5초 카운트다운 후 녹화가 시작돼요.
      </span>
    </div>
  );
}
