"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { ArrowLeft, Loader2, Play, Square } from "lucide-react";

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
import { formatScore } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Exercise } from "@/lib/mock/exercises";
import {
  saveSession,
  startSession,
  stopSession,
  type FaceMatchFailure,
  type FeedbackSeverity,
  type StopSessionResult,
  type WorkoutSession,
} from "@/lib/mock/workout-session";

type Phase = "idle" | "recognizing" | "tracking" | "result";

const SEVERITY: Record<FeedbackSeverity, { tone: BadgeTone; label: string }> = {
  info: { tone: "neutral", label: "정보" },
  warning: { tone: "warning", label: "주의" },
  critical: { tone: "danger", label: "위험" },
};

/** mm:ss */
function clock(totalSec: number): string {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function messageFor(reason?: FaceMatchFailure): string {
  switch (reason) {
    case "FACE_NOT_DETECTED":
      return "얼굴이 인식되지 않았어요. 정면을 바라보고 다시 시도해 주세요.";
    case "MULTIPLE_FACES_DETECTED":
      return "여러 사람이 감지됐어요. 혼자 촬영해 주세요.";
    case "FACE_MISMATCH":
      return "등록된 얼굴과 일치하지 않아요.";
    case "FACE_REQUIRED":
      return "얼굴을 먼저 등록해 주세요. 설정 > 얼굴 인증에서 등록할 수 있어요.";
    default:
      return "얼굴 인식에 실패했어요. 다시 시도해 주세요.";
  }
}

/*
 * SCR-08 실행 + SCR-09 결과. 포즈 추정·점수는 실제 추론 없이 시뮬레이션이며,
 * 연결 지점은 주석으로 표시했다. CameraView(웹캠) 만 실제로 동작한다.
 */
export function WorkoutLive({
  exercise,
  initialSessionId,
}: {
  exercise: Exercise;
  initialSessionId: number | null;
}) {
  const router = useRouter();
  const cameraRef = useRef<CameraViewHandle>(null);
  const isDynamic = exercise.exerciseType === "dynamic";

  const [phase, setPhase] = useState<Phase>("idle");
  const [permission, setPermission] = useState<CameraPermission>("prompt");
  const [recognitionError, setRecognitionError] = useState<string | null>(null);

  const [elapsed, setElapsed] = useState(0);
  const [reps, setReps] = useState(0);
  const [hold, setHold] = useState(0);
  const [liveScore, setLiveScore] = useState<number | null>(null);

  const [stopResult, setStopResult] = useState<StopSessionResult | null>(null);
  const [saved, setSaved] = useState(false);
  const [stopping, startStop] = useTransition();
  const [savingPending, startSave] = useTransition();

  // SCR-07 createSession 결과(id)로 세션 객체를 재구성한다(실제로는 세션 상세를 받아온다).
  const [session, setSession] = useState<WorkoutSession>(() => ({
    id: initialSessionId ?? 0,
    exercise: { id: exercise.id, nameKo: exercise.nameKo },
    status: "in_progress",
    startedAt: new Date().toISOString(),
    endedAt: null,
    durationSec: null,
    score: null,
    repCount: null,
    holdSec: null,
    saved: false,
    videoUrl: null,
  }));

  const granted = permission === "granted";

  // 추적 중 1초 틱 — 진행시간·카운터·라이브 점수를 시뮬한다.
  useEffect(() => {
    if (phase !== "tracking") return;
    const id = setInterval(() => {
      setElapsed((e) => e + 1);
      // 연결 지점: 실제로는 정답 시퀀스와의 프레임 비교 결과(일치도)
      setLiveScore(82 + Math.floor(Math.random() * 14));
      if (isDynamic) setReps((r) => (Math.random() < 0.45 ? r + 1 : r));
      else setHold((h) => h + 1);
    }, 1000);
    return () => clearInterval(id);
  }, [phase, isDynamic]);

  async function handleStart() {
    setRecognitionError(null);
    setPhase("recognizing");
    // 연결 지점: 얼굴 프레임을 캡처해 :start 로 등록 임베딩과 매칭한다.
    await cameraRef.current?.capture();
    const result = await startSession(session.id);
    await new Promise((r) => setTimeout(r, 1200)); // 인식 시간 시뮬
    if (!result.matched) {
      setRecognitionError(messageFor(result.reason));
      setPhase("idle");
      return;
    }
    setPhase("tracking");
  }

  function handleStop() {
    startStop(async () => {
      const res = await stopSession(session, {
        durationSec: elapsed,
        repCount: isDynamic ? reps : null,
        holdSec: isDynamic ? null : hold,
      });
      setStopResult(res);
      setSession(res.session);
      setPhase("result");
    });
  }

  function handleSave() {
    startSave(async () => {
      const updated = await saveSession(session);
      setSession(updated);
      setSaved(true);
    });
  }

  // ─── SCR-09 결과 ──────────────────────────────────────────────────────────
  if (phase === "result" && stopResult) {
    return (
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <header className="flex items-center gap-3 border-b border-border pb-4">
          <h1 className="text-lg font-semibold">운동 결과</h1>
          <span className="ml-auto text-xs text-text-subtle tabular-nums">
            {exercise.nameKo} · {clock(session.durationSec ?? elapsed)}
          </span>
        </header>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          {/* 좌측 — 녹화 미리보기(시뮬) + 점수 */}
          <div className="flex flex-col gap-4">
            <div className="overflow-hidden rounded-md border border-border">
              {/* 시뮬: 실제 녹화 영상은 저장 시 오브젝트 스토리지에서 스트리밍한다 */}
              <div className="flex aspect-video w-full flex-col items-center justify-center gap-2 bg-surface-muted">
                <Play className="size-8 text-text-subtle" aria-hidden />
                <p className="text-xs text-text-subtle">녹화된 운동 영상</p>
              </div>
            </div>

            <Card>
              <CardBody className="py-6 text-center">
                <p className="font-mono text-xs text-text-subtle">SCORE</p>
                <p className="mt-1 font-mono text-5xl font-semibold tabular-nums">
                  {session.score != null ? formatScore(session.score) : "—"}
                  <span className="ml-1 text-xl font-normal text-text-subtle">
                    /100
                  </span>
                </p>
                <p className="mt-2 text-xs text-text-subtle tabular-nums">
                  {isDynamic
                    ? `반복 ${session.repCount ?? 0}회`
                    : `유지 ${clock(session.holdSec ?? 0)}`}{" "}
                  · 진행 {clock(session.durationSec ?? 0)}
                </p>
              </CardBody>
            </Card>
          </div>

          {/* 우측 — AI 피드백 + 저장/종료 */}
          <div className="flex flex-col gap-4">
            <Card className="flex-1">
              <CardHeader>
                <h2 className="text-sm font-semibold">AI 피드백</h2>
              </CardHeader>
              <CardBody className="p-0">
                <ul className="divide-y divide-border">
                  {stopResult.feedbacks.map((f) => (
                    <li key={f.id} className="flex gap-3 px-6 py-3">
                      <Badge tone={SEVERITY[f.severity].tone} className="shrink-0">
                        {SEVERITY[f.severity].label}
                      </Badge>
                      <div className="min-w-0">
                        <p className="text-sm">{f.content}</p>
                        <p className="mt-0.5 text-xs text-text-subtle">
                          {f.generatedBy === "llm" ? "AI 분석" : "규칙 기반"}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>

            {saved ? (
              <div className="space-y-3">
                <p className="text-sm text-success">
                  영상을 저장했어요. 리포트에서 다시 볼 수 있어요.
                </p>
                <div className="flex gap-3">
                  <Link
                    href="/reports"
                    className={buttonClasses("secondary", "md", "flex-1")}
                  >
                    리포트에서 보기
                  </Link>
                  <Link
                    href="/dashboard"
                    className={buttonClasses("primary", "md", "flex-1")}
                  >
                    완료
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex gap-3">
                  <Button
                    variant="secondary"
                    className="flex-1"
                    disabled={savingPending}
                    onClick={() => router.push("/dashboard")}
                  >
                    종료
                  </Button>
                  <Button
                    className="flex-1"
                    loading={savingPending}
                    onClick={handleSave}
                  >
                    영상 저장
                  </Button>
                </div>
                <p className="text-center text-xs text-text-subtle">
                  저장하지 않으면 영상은 즉시 폐기돼요
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ─── SCR-08 실행 ──────────────────────────────────────────────────────────
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="flex items-center gap-3 border-b border-border pb-4">
        <Link
          href={`/workout/${exercise.id}`}
          aria-label="정답 영상으로"
          className="inline-flex size-9 items-center justify-center rounded-sm text-text-muted transition-colors duration-150 ease-out hover:bg-surface-muted hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent [&_svg]:size-4"
        >
          <ArrowLeft aria-hidden />
        </Link>
        <h1 className="text-lg font-semibold">{exercise.nameKo} · 실시간 분석</h1>
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

      {recognitionError && (
        <p className="mt-4 rounded-sm bg-warning-soft px-3 py-2 text-sm text-warning">
          {recognitionError}
        </p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_240px]">
        <CameraView
          ref={cameraRef}
          onPermissionChange={setPermission}
          overlay={<CameraOverlay phase={phase} />}
          className="aspect-video w-full"
        />

        <div className="flex flex-col gap-3">
          <StatCard label="진행 시간" value={clock(elapsed)} />
          {isDynamic ? (
            <StatCard label="현재 반복" value={`${reps}회`} />
          ) : (
            <StatCard label="유지 시간" value={clock(hold)} />
          )}
          <StatCard
            label="실시간 자세 일치도"
            value={liveScore != null ? `${liveScore}%` : "—"}
            accent={liveScore != null && liveScore >= 85}
          />

          {phase === "tracking" ? (
            <button
              type="button"
              onClick={handleStop}
              disabled={stopping}
              className="mt-1 flex w-full items-center justify-center gap-2 rounded-md border-2 border-danger bg-surface py-5 text-lg font-semibold text-danger transition-colors duration-150 ease-out hover:bg-danger-soft disabled:opacity-50 [&_svg]:size-5"
            >
              <Square aria-hidden />
              STOP
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStart}
              disabled={!granted || phase === "recognizing"}
              className="mt-1 flex w-full items-center justify-center gap-2 rounded-md bg-accent py-5 text-lg font-semibold text-white transition-colors duration-150 ease-out hover:bg-accent-hover disabled:opacity-50 [&_svg]:size-5"
            >
              {phase === "recognizing" ? (
                <Loader2 className="animate-spin" aria-hidden />
              ) : (
                <Play aria-hidden />
              )}
              START
            </button>
          )}

          <p className="text-center text-xs text-text-subtle">
            {phase === "tracking"
              ? "STOP을 누르면 분석을 마치고 결과를 보여줘요"
              : !granted
                ? "카메라 권한을 허용해 주세요"
                : "START → 얼굴 인식 후 분석을 시작해요"}
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <p className="text-xs text-text-subtle">{label}</p>
      <p
        className={cn(
          "mt-1 font-mono text-2xl font-semibold tabular-nums",
          accent && "text-success",
        )}
      >
        {value}
      </p>
    </div>
  );
}

/* 카메라 위 가이드 오버레이 — 권한 허용(영상 표시) 상태에서만 렌더된다 */
function CameraOverlay({ phase }: { phase: Phase }) {
  if (phase === "recognizing") {
    return (
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/55">
        <div className="flex items-center gap-2 rounded-md bg-surface px-4 py-3 text-sm font-medium shadow-sm">
          <Loader2 className="size-4 animate-spin text-accent" aria-hidden />
          얼굴 인식 중…
        </div>
      </div>
    );
  }
  if (phase === "tracking") {
    return (
      <>
        {/* 자세 가이드 박스 — 실제로는 추정된 키포인트/스켈레톤이 그려진다 */}
        <div className="pointer-events-none absolute inset-[12%] rounded-md border-2 border-dashed border-accent/70" />
        <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-1.5 rounded-sm bg-black/70 px-2 py-1 font-mono text-[10px] text-white">
          <span className="size-1.5 rounded-full bg-danger" />
          REC · 17/17 keypoints · 22 FPS
        </div>
      </>
    );
  }
  return (
    <div className="pointer-events-none absolute inset-0 flex items-end justify-center pb-4">
      <span className="rounded-sm bg-black/60 px-2 py-1 text-xs text-white">
        준비되면 START를 눌러요
      </span>
    </div>
  );
}
