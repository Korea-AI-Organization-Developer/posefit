import type { ReactNode } from "react";

import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { formatDay, formatDuration, formatScore } from "@/lib/format";
import type { ReportSummary } from "@/lib/mock/reports";

interface Stat {
  label: string;
  value: ReactNode;
}

/* REP-03~06 — 기간 요약. 점수는 대시보드 규칙대로 neutral Badge. */
export function SummaryCard({
  summary,
  control,
}: {
  summary: ReportSummary;
  /** 기간 전환 컨트롤 (PeriodTabs) — 헤더 우측에 배치 */
  control?: ReactNode;
}) {
  const {
    periodStart,
    periodEnd,
    sessionsCount,
    totalDurationSec,
    avgScore,
    bestExercise,
  } = summary;

  const rangeLabel =
    periodStart === periodEnd
      ? formatDay(periodStart)
      : `${formatDay(periodStart)} – ${formatDay(periodEnd)}`;

  const stats: Stat[] = [
    {
      label: "운동 횟수",
      value: (
        <span className="font-mono text-2xl font-semibold tabular-nums">
          {sessionsCount}
          <span className="ml-0.5 text-sm font-normal text-text-subtle">회</span>
        </span>
      ),
    },
    {
      label: "총 운동 시간",
      value: (
        <span className="font-mono text-2xl font-semibold tabular-nums">
          {formatDuration(totalDurationSec)}
        </span>
      ),
    },
    {
      label: "평균 점수",
      value:
        avgScore != null ? (
          <Badge className="font-mono text-sm">{formatScore(avgScore)}점</Badge>
        ) : (
          <span className="text-text-subtle">—</span>
        ),
    },
    {
      label: "최고 종목",
      value: bestExercise ? (
        <span className="text-base font-medium">
          {bestExercise.nameKo}
          <span className="ml-1.5 font-mono text-sm text-text-muted tabular-nums">
            {formatScore(bestExercise.bestScore)}점
          </span>
        </span>
      ) : (
        <span className="text-text-subtle">—</span>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div>
          <h2 className="text-sm font-semibold">기간 요약</h2>
          <p className="mt-0.5 text-xs text-text-subtle tabular-nums">
            {rangeLabel}
          </p>
        </div>
        {control}
      </CardHeader>
      <CardBody>
        {sessionsCount === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm font-medium">이 기간에 운동 기록이 없어요</p>
            <p className="mt-1 text-sm text-text-muted">
              다른 기간이나 종목을 선택해 보세요
            </p>
          </div>
        ) : (
          <dl className="grid grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-4">
            {stats.map(({ label, value }) => (
              <div key={label}>
                <dt className="text-sm text-text-muted">{label}</dt>
                <dd className="mt-2 flex min-h-8 items-center">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </CardBody>
    </Card>
  );
}
