"use client";

import { useState } from "react";
import { Play } from "lucide-react";
import { Badge, Card, CardBody, CardHeader, Dialog } from "@/components/ui";
import { formatDuration, formatScore, formatSessionTime } from "@/lib/format";
import type { WorkoutSessionSummary } from "@/lib/mock/workout-sessions";

/* REP-01 — 저장한 영상 목록. 행 클릭 시 Dialog 로 재생(현재는 poster 플레이스홀더). */
export function SavedVideos({
  sessions,
}: {
  sessions: WorkoutSessionSummary[];
}) {
  const [selected, setSelected] = useState<WorkoutSessionSummary | null>(null);

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">저장한 영상</h2>
        <span className="text-xs text-text-subtle tabular-nums">
          {sessions.length}개
        </span>
      </CardHeader>
      <CardBody className="p-0">
        {sessions.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-medium">저장한 영상이 없어요</p>
            <p className="mt-1 text-sm text-text-muted">
              운동 결과 화면에서 영상을 저장하면 여기에 모여요
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelected(session)}
                  className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition-colors duration-150 ease-out hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
                >
                  <div className="flex items-center gap-3">
                    <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-sm bg-surface-muted text-text-subtle [&_svg]:size-4">
                      <Play aria-hidden />
                    </span>
                    <div>
                      <p className="text-sm font-medium">
                        {session.exercise.nameKo}
                      </p>
                      <p className="mt-0.5 text-xs text-text-subtle">
                        {formatSessionTime(session.startedAt)}
                      </p>
                    </div>
                  </div>
                  {session.score != null && (
                    <Badge className="font-mono">
                      {formatScore(session.score)}점
                    </Badge>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardBody>

      <Dialog
        open={selected != null}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.exercise.nameKo} 다시 보기` : undefined}
        size="lg"
      >
        {selected && (
          <div className="space-y-4">
            {/* poster 플레이스홀더 — 실제 영상 스트리밍은 백엔드 연동 후 연결 */}
            <div className="flex aspect-video w-full flex-col items-center justify-center gap-2 rounded-md border border-border bg-surface-muted">
              <Play className="size-8 text-text-subtle" aria-hidden />
              <p className="text-xs text-text-subtle">
                영상 미리보기는 준비 중이에요
              </p>
            </div>

            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-text-muted">일시</dt>
                <dd className="tabular-nums">
                  {formatSessionTime(selected.startedAt)}
                </dd>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-text-muted">운동 시간</dt>
                <dd className="tabular-nums">
                  {selected.durationSec != null
                    ? formatDuration(selected.durationSec)
                    : "—"}
                </dd>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-text-muted">점수</dt>
                <dd className="font-mono tabular-nums">
                  {selected.score != null ? `${formatScore(selected.score)}점` : "—"}
                </dd>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-text-muted">반복</dt>
                <dd className="tabular-nums">
                  {selected.repCount != null ? `${selected.repCount}회` : "—"}
                </dd>
              </div>
            </dl>
          </div>
        )}
      </Dialog>
    </Card>
  );
}
