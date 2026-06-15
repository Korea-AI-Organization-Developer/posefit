import type { Metadata } from "next";
import { formatDateWithWeekday } from "@/lib/format";
import { getMe } from "@/lib/api/users";
import { getCalendar, getDashboard, MOCK_TODAY } from "@/lib/mock/dashboard";
import { getExercises } from "@/lib/mock/exercises";
import { ActivityHeatmap } from "./activity-heatmap";
import { KpiCards } from "./kpi-cards";
import { RecentSessions } from "./recent-sessions";
import { WorkoutCta } from "./workout-cta";

export const metadata: Metadata = { title: "대시보드" };

/*
 * SCR-05 메인 대시보드 (MAIN-01~06).
 * getMe()는 실제 API(@/lib/api/users). 나머지는 백엔드 미구현이라 목업 —
 * 구현 후 @/lib/mock/* 을 fetch 기반 @/lib/api/* 로 교체한다 (시그니처 동일):
 *   getDashboard() → GET /api/v1/users/me/dashboard
 *   getCalendar()  → GET /api/v1/reports/calendar?days=30
 *   getExercises() → GET /api/v1/exercises
 */
export default async function DashboardPage() {
  const [me, dashboard, calendar, exercises] = await Promise.all([
    getMe(),
    getDashboard(),
    getCalendar(),
    getExercises(),
  ]);

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header>
        <p className="text-sm text-text-muted">
          {formatDateWithWeekday(MOCK_TODAY)}
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          {me.nickname} 님, 안녕하세요
        </h1>
      </header>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* 좌측 — KPI + 주 CTA (MAIN-01, MAIN-03) */}
        <section className="flex flex-col gap-6">
          <KpiCards dashboard={dashboard} />
          <WorkoutCta exercises={exercises.items} />
        </section>

        {/* 우측 — 최근 기록 + 30일 활동 (MAIN-02, MAIN-06) */}
        <section className="flex flex-col gap-6">
          <RecentSessions sessions={dashboard.recentSessions} />
          <ActivityHeatmap days={calendar.days} baseDate={MOCK_TODAY} />
        </section>
      </div>
    </div>
  );
}
