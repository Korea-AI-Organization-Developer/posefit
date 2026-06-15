"use client";

import { useState, useTransition } from "react";
import { Button, Dialog } from "@/components/ui";
import { formatBytes } from "@/lib/format";
import { purgeVideos, type VideosSummary } from "@/lib/mock/videos";

/* SET-07 — 저장 영상 합계 + 일괄 삭제(목업, 비동기 처리 안내). */
export function VideosSection({ initial }: { initial: VideosSummary }) {
  const [summary, setSummary] = useState(initial);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [done, setDone] = useState<number | null>(null);
  const [pending, startTransition] = useTransition();

  const empty = summary.count === 0;

  function purge() {
    startTransition(async () => {
      const res = await purgeVideos();
      setSummary({ count: 0, totalBytes: 0 });
      setDone(res.purgedSessionsCount);
      setConfirmOpen(false);
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-text-muted tabular-nums">
          {empty ? (
            "저장된 영상이 없어요"
          ) : (
            <>
              총 <span className="font-medium text-text">{summary.count}개</span>{" "}
              영상 · 약{" "}
              <span className="font-medium text-text">
                {formatBytes(summary.totalBytes)}
              </span>
            </>
          )}
        </p>
        <Button
          variant="danger"
          size="sm"
          disabled={empty || pending}
          onClick={() => setConfirmOpen(true)}
        >
          전체 삭제
        </Button>
      </div>

      {done != null && (
        <p className="rounded-sm bg-surface-muted px-3 py-2 text-sm text-text-muted">
          {done}개 영상 삭제 요청이 접수됐어요. 처리에는 시간이 조금 걸릴 수 있어요.
        </p>
      )}

      <Dialog
        open={confirmOpen}
        onClose={() => !pending && setConfirmOpen(false)}
        title="저장한 영상을 모두 삭제할까요?"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setConfirmOpen(false)}
              disabled={pending}
            >
              취소
            </Button>
            <Button variant="danger" loading={pending} onClick={purge}>
              전체 삭제
            </Button>
          </>
        }
      >
        <p className="text-sm text-text-muted">
          저장된 영상 {summary.count}개가 모두 삭제돼요. 운동 기록·점수는 유지되지만
          영상은 되돌릴 수 없어요.
        </p>
      </Dialog>
    </div>
  );
}
