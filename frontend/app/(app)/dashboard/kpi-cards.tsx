import { Card, CardBody } from "@/components/ui";
import { formatScore } from "@/lib/format";
import type { DashboardResponse } from "@/lib/api/dashboard";

interface Kpi {
  label: string;
  value: string;
  suffix: string;
}

/* MAIN-01 — KPI 카드 3종. 숫자가 주인공: 수치는 mono로 크게, 라벨은 작게 */
export function KpiCards({ dashboard }: { dashboard: DashboardResponse }) {
  const kpis: Kpi[] = [
    {
      label: "최근 점수",
      value:
        dashboard.recentScore != null
          ? formatScore(dashboard.recentScore)
          : "—",
      suffix: "/100",
    },
    {
      label: "이번 주 운동",
      value: String(dashboard.weeklySessionsCount),
      suffix: "회",
    },
    {
      label: "누적 운동",
      value: String(dashboard.lifetimeSessionsCount),
      suffix: "회",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-6">
      {kpis.map(({ label, value, suffix }) => (
        <Card key={label}>
          <CardBody>
            <p className="text-sm text-text-muted">{label}</p>
            <p className="mt-2 font-mono text-3xl font-semibold tracking-tight tabular-nums">
              {value}
              <span className="ml-0.5 text-base font-normal text-text-subtle">
                {suffix}
              </span>
            </p>
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
