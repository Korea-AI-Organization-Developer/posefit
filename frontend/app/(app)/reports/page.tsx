import type { Metadata } from "next";

import { Card, CardBody, CardHeader } from "@/components/ui";
import { getExercises } from "@/lib/api/exercises";
import { getReportSummary, getScoreTrend, type ReportPeriod, type TrendDays } from "@/lib/api/reports";
import { OverviewDialog } from "./overview-dialog";
import { QueryTabs } from "./query-tabs";
import { ScoreTrendChart } from "./score-trend-chart";
import { SummaryCard } from "./summary-card";

export const metadata: Metadata = { title: "리포트" };

const PERIODS: ReportPeriod[] = ["day", "week", "month"];
const PERIOD_LABELS: Record<ReportPeriod, string> = {
  day: "일",
  week: "주",
  month: "월",
  cumulative: "누적",
};
const TREND_DAYS: TrendDays[] = [7, 30, 90];

const firstParam = (v: string | string[] | undefined): string | undefined =>
  Array.isArray(v) ? v[0] : v;

/*
 * SCR-10 리포트 (REP-01~07).
 * 필터(period·days·exerciseId)는 URL searchParams 로 다룬다 → 데이터 fetch 는 전부
 * 서버에서 수행하므로, 백엔드 연동 시 @/lib/mock/* 만 @/lib/api/* 로 바꾸면 된다.
 *   getReportSummary() → GET /api/v1/reports/summary
 *   getScoreTrend()    → GET /api/v1/reports/score-trend
 *   getExercises()     → GET /api/v1/exercises
 */
export default async function ReportsPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;

  const period = (() => {
    const v = firstParam(sp.period);
    return PERIODS.includes(v as ReportPeriod) ? (v as ReportPeriod) : "week";
  })();
  const days = (() => {
    const v = Number(firstParam(sp.days));
    return TREND_DAYS.includes(v as TrendDays) ? (v as TrendDays) : 7;
  })();

  const { items: exercises } = await getExercises();
  const validIds = new Set(exercises.map((e) => e.id));
  const exerciseId = (() => {
    const v = Number(firstParam(sp.exerciseId));
    return validIds.has(v) ? v : exercises[0]?.id;
  })();

  const [summary, trend] = await Promise.all([
    getReportSummary(period, undefined, exerciseId),
    getScoreTrend(days, exerciseId),
  ]);

  // 현재 필터 — QueryTabs 가 다른 파라미터를 보존하며 URL 을 갱신하도록 함께 넘긴다.
  const currentParams: Record<string, string> = { period, days: String(days) };
  if (exerciseId != null) currentParams.exerciseId = String(exerciseId);

  const periodOptions = PERIODS.map((p) => ({
    value: p,
    label: PERIOD_LABELS[p],
  }));
  const daysOptions = TREND_DAYS.map((d) => ({
    value: String(d),
    label: `${d}일`,
  }));
  const exerciseOptions = exercises.map((e) => ({
    value: String(e.id),
    label: e.nameKo,
  }));

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">리포트</h1>
          <p className="mt-1 text-sm text-text-muted">
            운동 기록을 기간·종목별로 돌아봐요
          </p>
        </div>
        <OverviewDialog exerciseId={exerciseId} />
      </header>

      {/* REP-07 — 종목 필터. 요약·차트·목록 전체에 적용된다. */}
      <div className="mt-6 flex items-center gap-3">
        <span className="shrink-0 text-sm text-text-muted">종목</span>
        <div className="overflow-x-auto">
          <QueryTabs
            paramKey="exerciseId"
            options={exerciseOptions}
            value={exerciseId != null ? String(exerciseId) : String(exercises[0]?.id ?? "")}
            currentParams={currentParams}
            size="sm"
            aria-label="종목 필터"
          />
        </div>
      </div>

      <div className="mt-8 space-y-6">
        {/* REP-03~06 — 기간 요약 */}
        <SummaryCard
          summary={summary}
          control={
            <QueryTabs
              paramKey="period"
              options={periodOptions}
              value={period}
              currentParams={currentParams}
              size="sm"
              aria-label="기간 선택"
            />
          }
        />

        {/* REP-02 — 점수 추이 차트 */}
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">점수 추이</h2>
            <QueryTabs
              paramKey="days"
              options={daysOptions}
              value={String(days)}
              currentParams={currentParams}
              size="sm"
              aria-label="기간 일수 선택"
            />
          </CardHeader>
          <CardBody>
            <ScoreTrendChart series={trend.series} />
          </CardBody>
        </Card>

      </div>
    </div>
  );
}
