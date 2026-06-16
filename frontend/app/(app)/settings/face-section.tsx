"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { Badge, Button, Dialog } from "@/components/ui";
import {
  CameraView,
  type CameraPermission,
  type CameraViewHandle,
} from "@/components/camera/camera-view";
import {
  deleteFaceAction,
  detectFaceAction,
  reRegisterFaceAction,
} from "./actions";

/* 감지 상태에 따라 타원 테두리 색을 바꾼다 — 전부 semantic 토큰 */
function OvalOverlay({
  detected,
  granted,
}: {
  detected: boolean;
  granted: boolean;
}) {
  const border = !granted
    ? "border-border-strong"
    : detected
      ? "border-success"
      : "border-danger";
  return (
    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
      <div
        className={`aspect-[3/4] h-3/4 rounded-full border-2 transition-colors duration-300 ${border}`}
      />
    </div>
  );
}

/* SET-04/05 — 얼굴 재등록(PUT) · 삭제(DELETE). CameraView 프리미티브를 재사용한다. */
export function FaceSection({ registered: initial }: { registered: boolean }) {
  const [registered, setRegistered] = useState(initial);
  const [notice, setNotice] = useState<string | null>(null);

  const [camOpen, setCamOpen] = useState(false);
  const [delOpen, setDelOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-1.5">
          {registered ? (
            <Badge tone="success">등록됨</Badge>
          ) : (
            <Badge tone="warning">미등록</Badge>
          )}
          <p className="text-xs text-text-subtle">
            운동 시작 시 본인 확인에 사용돼요. 원본 이미지는 저장하지 않아요.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setNotice(null);
              setCamOpen(true);
            }}
          >
            {registered ? "재등록" : "등록"}
          </Button>
          {registered && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                setNotice(null);
                setDelOpen(true);
              }}
            >
              삭제
            </Button>
          )}
        </div>
      </div>

      {notice && <p className="text-sm text-success">{notice}</p>}
      {!registered && (
        <p className="rounded-sm bg-warning-soft px-3 py-2 text-sm text-warning">
          얼굴 데이터가 없어 운동 시작이 제한돼요. 다시 등록해 주세요.
        </p>
      )}

      {camOpen && (
        <ReRegisterDialog
          onClose={() => setCamOpen(false)}
          onDone={() => {
            setRegistered(true);
            setNotice("얼굴을 다시 등록했어요.");
            setCamOpen(false);
          }}
        />
      )}

      <DeleteDialog
        open={delOpen}
        onClose={() => setDelOpen(false)}
        onDone={() => {
          setRegistered(false);
          setNotice(null);
          setDelOpen(false);
        }}
      />
    </div>
  );
}

/* 카메라 재등록 다이얼로그 — 온보딩과 동일하게 감지→촬영→미리보기→PUT 흐름 */
function ReRegisterDialog({
  onClose,
  onDone,
}: {
  onClose: () => void;
  onDone: () => void;
}) {
  const cameraRef = useRef<CameraViewHandle>(null);
  const isDetectingRef = useRef(false);
  const [permission, setPermission] = useState<CameraPermission>("prompt");
  const [phase, setPhase] = useState<"live" | "captured">("live");
  const [detected, setDetected] = useState(false);
  const [preview, setPreview] = useState<{ url: string; blob: Blob } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const granted = permission === "granted";

  useEffect(() => {
    if (phase !== "live" || !granted) {
      setDetected(false);
      return;
    }
    async function run() {
      if (isDetectingRef.current) return;
      const frame = await cameraRef.current?.capture();
      if (!frame) return;
      isDetectingRef.current = true;
      try {
        const fd = new FormData();
        fd.append("image", frame, "frame.jpg");
        const res = await detectFaceAction(fd);
        setDetected(res.detected);
      } finally {
        isDetectingRef.current = false;
      }
    }
    run();
    const id = setInterval(run, 1500);
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
      const res = await reRegisterFaceAction(fd);
      if (res?.error) setError(res.error);
      else onDone();
    });
  }

  return (
    <Dialog open onClose={() => !pending && onClose()} title="얼굴 재등록">
      <div className="space-y-4">
        <p className="text-sm text-text-muted">
          타원 안에 얼굴을 맞추고 촬영하세요. 테두리가 초록색이면 인식된 거예요.
        </p>

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
              {/* eslint-disable-next-line @next/next/no-img-element -- 블롭 미리보기 */}
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
      </div>
    </Dialog>
  );
}

/* 얼굴 삭제 확인 — 삭제 시 운동 시작이 제한됨을 안내 */
function DeleteDialog({
  open,
  onClose,
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  onDone: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function confirm() {
    setError(null);
    startTransition(async () => {
      const res = await deleteFaceAction();
      if (res?.error) setError(res.error);
      else onDone();
    });
  }

  return (
    <Dialog
      open={open}
      onClose={() => !pending && onClose()}
      title="얼굴 데이터를 삭제할까요?"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            취소
          </Button>
          <Button variant="danger" loading={pending} onClick={confirm}>
            삭제
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <p className="text-sm text-text-muted">
          저장된 얼굴 임베딩이 삭제돼요. 삭제 후에는 본인 확인을 할 수 없어
          <span className="font-medium text-text"> 운동 시작이 제한</span>돼요.
        </p>
        <p className="text-sm text-text-muted">
          언제든 다시 등록할 수 있어요.
        </p>
        {error && <p className="text-sm text-danger">{error}</p>}
      </div>
    </Dialog>
  );
}
