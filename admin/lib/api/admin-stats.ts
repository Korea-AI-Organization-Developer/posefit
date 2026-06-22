import { apiFetch } from "@/lib/api/server";
import type { StatsOverview, TimeseriesPoint } from "@/lib/api/types";

export async function getStatsOverview(): Promise<StatsOverview> {
  return apiFetch<StatsOverview>("/admin/stats/overview");
}

export async function getTimeseries(from: string, to: string): Promise<{ points: TimeseriesPoint[] }> {
  const qs = new URLSearchParams({ from, to });
  return apiFetch<{ points: TimeseriesPoint[] }>(`/admin/stats/timeseries?${qs.toString()}`);
}
