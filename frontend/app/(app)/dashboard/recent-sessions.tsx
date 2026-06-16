import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { formatScore, formatSessionTime } from "@/lib/format";
import type { WorkoutSessionSummary } from "@/lib/mock/dashboard";

/* MAIN-02 — 최근 운동 기록. 행 클릭 시 해당 세션 리포트로 이동 */
export function RecentSessions({
  sessions,
}: {
  sessions: WorkoutSessionSummary[];
}) {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">최근 운동 기록</h2>
        <Link
          href="/reports"
          className="text-sm text-text-muted transition-colors duration-150 ease-out hover:text-text"
        >
          전체 보기
        </Link>
      </CardHeader>
      <CardBody className="p-0">
        {sessions.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-medium">아직 운동 기록이 없어요</p>
            <p className="mt-1 text-sm text-text-muted">
              첫 운동을 시작하면 여기에 기록이 쌓입니다
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {sessions.map((session) => (
              <li key={session.id}>
                {/* 세션 상세 라우트(/reports/...)가 확정되면 href를 교체한다 */}
                <Link
                  href={`/reports?session=${session.id}`}
                  className="flex items-center justify-between gap-4 px-6 py-4 transition-colors duration-150 ease-out hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {session.exercise.nameKo}
                    </p>
                    <p className="mt-0.5 text-xs text-text-subtle">
                      {formatSessionTime(session.startedAt)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {session.score != null && (
                      <Badge className="font-mono">
                        {formatScore(session.score)}점
                      </Badge>
                    )}
                    <ChevronRight
                      className="size-4 text-text-subtle"
                      aria-hidden
                    />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
