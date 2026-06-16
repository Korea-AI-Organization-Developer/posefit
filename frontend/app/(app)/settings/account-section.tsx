"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { LogOut } from "lucide-react";
import { Button, Checkbox, Dialog } from "@/components/ui";
import { withdrawAction } from "./actions";

/* 탈퇴 시 삭제되는 데이터 — 요구사항 5.2 */
const DELETE_ITEMS = [
  "운동 기록·점수·통계",
  "저장한 영상",
  "얼굴 인증 데이터",
  "프로필·신체 정보",
];

/* 로그아웃 + 회원 탈퇴(SET-08). */
export function AccountSection() {
  const router = useRouter();
  const [loggingOut, startLogout] = useTransition();

  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [withdrawing, startWithdraw] = useTransition();

  function logout() {
    startLogout(async () => {
      // 기존 로그아웃 라우트 재사용 — 백엔드 token_version +1 후 인증 쿠키 제거
      await fetch("/auth/logout", { method: "POST" });
      router.push("/");
      router.refresh();
    });
  }

  function openWithdraw() {
    setAgreed(false);
    setError(null);
    setWithdrawOpen(true);
  }

  function confirmWithdraw() {
    setError(null);
    startWithdraw(async () => {
      const res = await withdrawAction();
      // 성공 시 서버 액션이 redirect 하므로 여기로 돌아오지 않는다
      if (res?.error) setError(res.error);
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium">로그아웃</p>
          <p className="mt-0.5 text-xs text-text-subtle">
            이 기기에서 로그아웃해요.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          leftIcon={<LogOut />}
          loading={loggingOut}
          onClick={logout}
        >
          로그아웃
        </Button>
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-border pt-6">
        <div>
          <p className="text-sm font-medium text-danger">회원 탈퇴</p>
          <p className="mt-0.5 text-xs text-text-subtle">
            계정과 모든 데이터를 삭제해요. 되돌릴 수 없어요.
          </p>
        </div>
        <Button variant="danger" size="sm" onClick={openWithdraw}>
          회원 탈퇴
        </Button>
      </div>

      <Dialog
        open={withdrawOpen}
        onClose={() => !withdrawing && setWithdrawOpen(false)}
        title="정말 탈퇴하시겠어요?"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setWithdrawOpen(false)}
              disabled={withdrawing}
            >
              취소
            </Button>
            <Button
              variant="danger"
              disabled={!agreed}
              loading={withdrawing}
              onClick={confirmWithdraw}
            >
              탈퇴하기
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-text-muted">
            탈퇴하면 아래 데이터가 모두 삭제돼요.
          </p>
          <ul className="space-y-1.5">
            {DELETE_ITEMS.map((item) => (
              <li
                key={item}
                className="flex items-center gap-2 text-sm text-text-muted"
              >
                <span
                  aria-hidden
                  className="size-1 shrink-0 rounded-full bg-text-subtle"
                />
                {item}
              </li>
            ))}
          </ul>
          <Checkbox
            label="위 내용을 확인했으며 탈퇴에 동의합니다."
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          {error && <p className="text-sm text-danger">{error}</p>}
        </div>
      </Dialog>
    </div>
  );
}
