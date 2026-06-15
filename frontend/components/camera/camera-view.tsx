"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { CameraOff } from "lucide-react";
import { cn } from "@/lib/utils";

export type CameraPermission =
  | "prompt"
  | "granted"
  | "denied"
  | "unavailable";

export interface CameraViewHandle {
  /** 현재 프레임을 jpeg Blob으로 캡처. 스트림이 없으면 null */
  capture: () => Promise<Blob | null>;
}

export interface CameraViewProps {
  /** 프리뷰 위에 겹칠 가이드(타원 등) */
  overlay?: ReactNode;
  className?: string;
  onPermissionChange?: (permission: CameraPermission) => void;
}

/*
 * getUserMedia 웹캠 프리뷰 + 권한 처리. U4 얼굴 등록·U5 운동 실행·U3 얼굴 재등록 공용.
 * 캡처는 ref(capture())로 노출. 셀카처럼 좌우 반전해서 보여준다.
 */
export const CameraView = forwardRef<CameraViewHandle, CameraViewProps>(
  function CameraView({ overlay, className, onPermissionChange }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [permission, setPermission] = useState<CameraPermission>("prompt");

    useEffect(() => {
      let stream: MediaStream | null = null;
      let cancelled = false;

      async function start() {
        if (!navigator.mediaDevices?.getUserMedia) {
          setPermission("unavailable");
          onPermissionChange?.("unavailable");
          return;
        }
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" },
            audio: false,
          });
          if (cancelled) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }
          if (videoRef.current) videoRef.current.srcObject = stream;
          setPermission("granted");
          onPermissionChange?.("granted");
        } catch {
          setPermission("denied");
          onPermissionChange?.("denied");
        }
      }

      start();
      return () => {
        cancelled = true;
        stream?.getTracks().forEach((t) => t.stop());
      };
    }, [onPermissionChange]);

    useImperativeHandle(
      ref,
      () => ({
        async capture() {
          const video = videoRef.current;
          if (!video || video.videoWidth === 0) return null;
          const canvas = document.createElement("canvas");
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext("2d");
          if (!ctx) return null;
          ctx.drawImage(video, 0, 0);
          return new Promise<Blob | null>((resolve) =>
            canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9),
          );
        },
      }),
      [],
    );

    const blocked = permission === "denied" || permission === "unavailable";

    return (
      <div
        className={cn(
          "relative overflow-hidden rounded-md border border-border bg-surface-muted",
          className,
        )}
      >
        {blocked ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-10 text-center [&_svg]:size-8 [&_svg]:text-text-subtle">
            <CameraOff aria-hidden />
            <p className="text-sm text-text-muted">
              {permission === "unavailable"
                ? "이 브라우저에서는 카메라를 쓸 수 없어요."
                : "카메라 권한이 차단됐어요. 브라우저 주소창의 카메라 아이콘에서 권한을 허용한 뒤 새로고침해 주세요."}
            </p>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-full w-full object-cover [transform:scaleX(-1)]"
            />
            {overlay}
          </>
        )}
      </div>
    );
  },
);
