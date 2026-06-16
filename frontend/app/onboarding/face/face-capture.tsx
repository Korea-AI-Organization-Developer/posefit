"use client";

import { useEffect, useRef, useState, useTransition } from "react";

import { Button, Card, CardBody } from "@/components/ui";
import {
  CameraView,
  type CameraPermission,
  type CameraViewHandle,
} from "@/components/camera/camera-view";
import { detectFaceAction, registerFaceAction } from "./actions";

function OvalOverlay({ detected, granted }: { detected: boolean; granted: boolean }) {
  const borderColor = !granted
    ? "border-border-strong"
    : detected
      ? "border-success"
      : "border-danger";
  return (
    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
      <div className={`aspect-[3/4] h-3/4 rounded-full border-2 transition-colors duration-300 ${borderColor}`} />
    </div>
  );
}

export function FaceCapture() {
  const cameraRef = useRef<CameraViewHandle>(null);
  const [permission, setPermission] = useState<CameraPermission>("prompt");
  const [phase, setPhase] = useState<"live" | "captured">("live");
  const [detected, setDetected] = useState(false);
  const [preview, setPreview] = useState<{ url: string; blob: Blob } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const granted = permission === "granted";
  const isDetectingRef = useRef(false);

  useEffect(() => {
    if (phase !== "live" || !granted) {
      setDetected(false);
      return;
    }

    async function runDetect() {
      if (isDetectingRef.current) return;
      const snapshot = await cameraRef.current?.capture();
      if (!snapshot) return;

      isDetectingRef.current = true;
      try {
        const fd = new FormData();
        fd.append("image", snapshot, "frame.jpg");
        const res = await detectFaceAction(fd);
        setDetected(res.detected);
      } finally {
        isDetectingRef.current = false;
      }
    }

    runDetect();
    const id = setInterval(runDetect, 1500);
    return () => clearInterval(id);
  }, [phase, granted]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview.url);
    };
  }, [preview]);

  async function capture() {
    const blob = await cameraRef.current?.capture();
    if (!blob) {
      setError("촬영에 실패했어요. 다시 시도해 주세요.");
      return;
    }
    setError(null);
    setPreview({ url: URL.createObjectURL(blob), blob });
    setPhase("captured");
  }

  function retake() {
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setPhase("live");
  }

  function submit() {
    if (!preview) return;
    setError(null);
    const fd = new FormData();
    fd.append("image", preview.blob, "face.jpg");
    startTransition(async () => {
      const res = await registerFaceAction(fd);
      if (res?.error) setError(res.error);
    });
  }

  return (
    <Card>
      <CardBody className="space-y-6">
        <div className="space-y-1.5">
          <h1 className="text-lg font-semibold">얼굴을 등록해 주세요</h1>
          <p className="text-sm text-text-muted">
            로그인 본인 확인에 사용돼요. 타원 안에 얼굴을 맞추고 촬영하세요.
          </p>
        </div>

        <div className="mx-auto w-full max-w-xs">
          {phase === "live" ? (
            <CameraView
              ref={cameraRef}
              overlay={<OvalOverlay detected={detected} granted={granted} />}
              onPermissionChange={setPermission}
              className="aspect-[3/4] w-full"
            />
          ) : (
            <div className="aspect-[3/4] w-full overflow-hidden rounded-md border border-border bg-surface-muted">
              {/* eslint-disable-next-line @next/next/no-img-element -- 블롭 미리보기(원격 최적화 불필요) */}
              <img
                src={preview?.url}
                alt="촬영된 얼굴 미리보기"
                className="h-full w-full object-cover [transform:scaleX(-1)]"
              />
            </div>
          )}
        </div>

        {phase === "live" && (
          <p className="text-center text-sm text-text-muted">
            {!granted
              ? "카메라를 준비하고 있어요…"
              : detected
                ? "얼굴이 인식됐어요. 촬영하세요."
                : "얼굴을 타원 안에 맞춰 주세요…"}
          </p>
        )}

        {error && <p className="text-center text-sm text-danger">{error}</p>}

        {phase === "live" ? (
          <Button
            size="lg"
            className="w-full"
            disabled={!granted || !detected}
            onClick={capture}
          >
            촬영
          </Button>
        ) : (
          <div className="flex gap-3">
            <Button
              variant="secondary"
              size="lg"
              className="flex-1"
              onClick={retake}
              disabled={pending}
            >
              다시 촬영
            </Button>
            <Button
              size="lg"
              className="flex-1"
              loading={pending}
              onClick={submit}
            >
              등록하기
            </Button>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
