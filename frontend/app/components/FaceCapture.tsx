"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Status = "idle" | "loading" | "ready" | "detecting" | "captured" | "error";

interface Props {
  onCapture?: (base64: string) => void;
  autoDetect?: boolean;           // 자동으로 주기적 캡처 시도
  onAutoDetect?: (base64: string) => void;
  detectInterval?: number;        // ms 단위 (기본 2000)
  label?: string;
}

export default function FaceCapture({
  onCapture,
  autoDetect = false,
  onAutoDetect,
  detectInterval = 2000,
  label = "카메라",
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [status, setStatus] = useState<Status>("idle");
  const [faceDetected, setFaceDetected] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    setStatus("loading");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.85);
  }, []);

  const handleCapture = useCallback(() => {
    const base64 = captureFrame();
    if (!base64) return;
    setCapturedImage(base64);
    setStatus("captured");
    onCapture?.(base64);
  }, [captureFrame, onCapture]);

  const handleRetake = useCallback(() => {
    setCapturedImage(null);
    setStatus("ready");
    setFaceDetected(false);
  }, []);

  // 자동 감지 인터벌
  useEffect(() => {
    if (!autoDetect || status !== "ready") return;

    setStatus("detecting");
    intervalRef.current = setInterval(() => {
      const base64 = captureFrame();
      if (base64) {
        setFaceDetected(true);
        onAutoDetect?.(base64);
      }
    }, detectInterval);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoDetect, status, captureFrame, onAutoDetect, detectInterval]);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-full max-w-sm aspect-video rounded-2xl overflow-hidden bg-slate-900 border border-slate-700">
        {/* 비디오 */}
        <video
          ref={videoRef}
          className={`w-full h-full object-cover scale-x-[-1] ${capturedImage ? "hidden" : ""}`}
          muted
          playsInline
        />

        {/* 캡처된 이미지 */}
        {capturedImage && (
          <img
            src={capturedImage}
            alt="캡처된 얼굴"
            className="w-full h-full object-cover scale-x-[-1]"
          />
        )}

        {/* 로딩 */}
        {status === "loading" && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
            <div className="flex flex-col items-center gap-2 text-slate-400">
              <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span className="text-sm">카메라 연결 중...</span>
            </div>
          </div>
        )}

        {/* 에러 */}
        {status === "error" && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
            <div className="flex flex-col items-center gap-2 text-red-400 text-center px-4">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M5.07 19H19a2 2 0 001.75-2.96L13.75 4a2 2 0 00-3.5 0L3.25 16.04A2 2 0 005.07 19z" />
              </svg>
              <span className="text-sm">카메라 접근 권한이 필요합니다</span>
              <button onClick={startCamera} className="text-xs text-emerald-400 underline">다시 시도</button>
            </div>
          </div>
        )}

        {/* 얼굴 가이드 오버레이 */}
        {(status === "ready" || status === "detecting") && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div
              className={`w-40 h-52 rounded-full border-2 transition-colors ${
                faceDetected ? "border-emerald-400 shadow-lg shadow-emerald-400/30" : "border-white/30"
              }`}
            />
          </div>
        )}

        {/* 자동 감지 상태 표시 */}
        {status === "detecting" && (
          <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/50 rounded-full px-3 py-1">
            <div className={`w-2 h-2 rounded-full ${faceDetected ? "bg-emerald-400 animate-pulse" : "bg-slate-400"}`} />
            <span className="text-xs text-white">{faceDetected ? "얼굴 감지됨" : "얼굴을 화면에 맞춰주세요"}</span>
          </div>
        )}

        {/* 완료 표시 */}
        {status === "captured" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <div className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        )}
      </div>

      {/* 캔버스 (숨김) */}
      <canvas ref={canvasRef} className="hidden" />

      {/* 버튼 */}
      {!autoDetect && (
        <div className="flex gap-3 w-full max-w-sm">
          {status === "captured" ? (
            <button
              onClick={handleRetake}
              className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700/60 transition-colors text-sm font-medium"
            >
              다시 찍기
            </button>
          ) : (
            <button
              onClick={handleCapture}
              disabled={status !== "ready"}
              className="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium transition-colors text-sm flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
