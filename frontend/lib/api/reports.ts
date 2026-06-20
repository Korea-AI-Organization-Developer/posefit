import { apiFetch } from "./server";
import type { ReportPeriod, ReportSummary, ScoreTrendResponse } from "./types";

export type { ReportPeriod, ReportSummary, ScoreTrendResponse } from "./types";
export type TrendDays = 7 | 30 | 90;

export async function getReportSummary(
  period: ReportPeriod,
  referenceDate?: string,
  exerciseId?: number,
): Promise<ReportSummary> {
  const sp = new URLSearchParams({ period });
  if (referenceDate) sp.set("referenceDate", referenceDate);
  if (exerciseId != null) sp.set("exerciseId", String(exerciseId));
  return apiFetch(`/reports/summary?${sp}`);
}

export async function getScoreTrend(
  days: TrendDays,
  exerciseId?: number,
): Promise<ScoreTrendResponse> {
  const sp = new URLSearchParams({ days: String(days) });
  if (exerciseId != null) sp.set("exerciseId", String(exerciseId));
  return apiFetch(`/reports/score-trend?${sp}`);
}
