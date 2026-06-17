"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";

import { buttonClasses } from "@/components/ui";
import type { FaceGateMode } from "@/lib/api/types";

type GateModeAll = FaceGateMode | "passed" | "failed";

interface WsMessage {
  mode: GateModeAll;
  message: string;
  progress: number;
  total: number;
  faceInGuide: boolean;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const WS_BASE = API_BASE.replace(/^http/, "ws");
const WS_URL = `${WS_BASE}/workout/face-gate/ws`;

/** 카메라 프레임 전송 간격 (ms) */
const FRAME_MS = 150;

const MODE_LABEL: Record<FaceGateMode, string> = {
  registration: "얼굴 등록",
  verification: "얼굴 인증",
};

function guideColor(status: WsMessage): string {
  if (status.mode === "passed") return "#4ade80";   // green-400
  if (status.mode === "failed") return "#ef4444";   // red-500
  if (status.faceInGuide)       return "#4ade80";   // green-400
  if (status.mode === "registration") return "#60a5fa"; // blue-400
  return "#facc15";                                 // yellow-400
}

export function FaceGateClient({
  token,
  initialMode,
  returnTo = "/workout",
  reregister = false,
}: {
  token: string;
  initialMode: FaceGateMode;
  returnTo?: string;
  reregister?: boolean;
}) {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState(false);
  const [status, setStatus] = useState<WsMessage>({
    mode: initialMode,
    message: "카메라 연결 중...",
    progress: 0,
    total: initialMode === "registration" ? 40 : 3,
    faceInGuide: false,
  });

  // ── 카메라 시작 ────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480, facingMode: "user" } })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => setCameraReady(true);
        }
      })
      .catch(() => {
        if (!cancelled) setCameraError(true);
      });

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // ── WebSocket 연결 + 프레임 전송 ───────────────────────────────
  useEffect(() => {
    if (!cameraReady) return;

    const wsUrl = reregister ? `${WS_URL}?token=${token}&reregister=1` : `${WS_URL}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // 주기적으로 canvas에 video 프레임을 찍어 JPEG로 전송
      timerRef.current = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const canvas = captureCanvasRef.current;
        const video = videoRef.current;
        if (!canvas || !video || video.readyState < 2) return;

        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // CSS mirror(scaleX -1)는 display 전용이므로 canvas에는 raw 프레임이 그려짐
        // 백엔드가 cv2.flip(frame, 1)으로 다시 좌우 반전해 정면 처리
        ctx.drawImage(video, 0, 0);

        canvas.toBlob(
          (blob) => {
            if (!blob || ws.readyState !== WebSocket.OPEN) return;
            blob.arrayBuffer().then((buf) => ws.send(buf));
          },
          "image/jpeg",
          0.85,
        );
      }, FRAME_MS);
    };

    ws.onmessage = (ev) => {
      const msg: WsMessage = JSON.parse(ev.data as string);
      setStatus(msg);
      if (msg.mode === "passed") {
        router.push(returnTo);
      }
    };

    ws.onerror = () => {
      setStatus((prev) => ({
        ...prev,
        message: "서버 연결 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
      }));
    };

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      ws.close();
    };
  }, [cameraReady, token, router]);

  // ── UI ────────────────────────────────────────────────────────
  const modeLabel =
    status.mode === "passed"
      ? "인증 완료"
      : status.mode === "failed"
        ? "오류"
        : MODE_LABEL[status.mode as FaceGateMode] ?? "준비 중";

  const pct =
    status.total > 0
      ? Math.min((status.progress / status.total) * 100, 100)
      : 0;

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      {/* 상단 바 */}
      <div className="flex items-center gap-3 border-b border-border px-6 py-4">
        <button
          type="button"
          onClick={() => router.back()}
          className={buttonClasses("ghost", "sm")}
        >
          <ArrowLeft className="size-4" aria-hidden />
          뒤로
        </button>
        <h1 className="text-lg font-semibold">{modeLabel}</h1>
      </div>

      {/* 본문 */}
      <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-10">
        {/* 카메라 뷰 */}
        <div className="relative overflow-hidden rounded-2xl bg-surface-muted shadow-lg">
          {cameraError ? (
            <div className="flex h-[480px] w-[640px] items-center justify-center text-sm text-text-muted">
              카메라를 사용할 수 없습니다. 브라우저 권한을 확인해 주세요.
            </div>
          ) : (
            <>
              {/* 셀피 모드(좌우 반전) — CSS 전용, 전송 프레임에는 영향 없음 */}
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="h-[480px] w-[640px] scale-x-[-1] object-cover"
              />

              {/* 가이드 박스 오버레이 */}
              <div
                className="pointer-events-none absolute inset-0 flex items-center justify-center"
                aria-hidden
              >
                <div
                  style={{
                    borderColor: guideColor(status),
                    transition: "border-color 0.3s",
                  }}
                  className="rounded-xl border-2 h-[72%] w-[52%]"
                />
              </div>

              {/* 상태 메시지 오버레이 */}
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent px-4 pb-4 pt-10">
                <p className="text-center text-sm font-medium text-white">
                  {status.message}
                </p>
              </div>
            </>
          )}
        </div>

        {/* 진행 바 */}
        {status.total > 0 && status.mode !== "passed" && (
          <div className="w-full max-w-sm">
            <div className="mb-1.5 flex justify-between text-xs text-text-subtle">
              <span>{modeLabel}</span>
              <span>
                {status.progress} / {status.total}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface-muted">
              <div
                className="h-full rounded-full bg-accent transition-all duration-300 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}

        {/* 인증 완료 메시지 */}
        {status.mode === "passed" && (
          <p className="text-base font-medium text-green-500">
            {status.message}
          </p>
        )}
      </div>

      {/* 숨겨진 프레임 캡쳐용 캔버스 */}
      <canvas ref={captureCanvasRef} className="hidden" aria-hidden />
    </div>
  );
}
