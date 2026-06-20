"use client";

import Link from "next/link";
import { Badge } from "@/components/ui";
import { buttonClasses } from "@/components/ui";

/* SET-04 — 얼굴 인증 현황. 등록·재등록은 운동 시작 시 face-gate 에서 처리한다. */
export function FaceSection({ registered }: { registered: boolean }) {
  return (
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
        {!registered && (
          <p className="text-xs text-warning">
            얼굴 데이터가 없어요. 운동 시작하기를 누르면 등록할 수 있어요.
          </p>
        )}
      </div>

      <Link
        href={registered ? "/workout/face-gate?reregister=1" : "/workout/face-gate"}
        className={buttonClasses("secondary", "sm", "shrink-0")}
      >
        {registered ? "재등록" : "등록"}
      </Link>
    </div>
  );
}
