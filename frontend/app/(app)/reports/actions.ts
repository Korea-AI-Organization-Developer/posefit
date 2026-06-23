"use server";

import { apiFetch } from "@/lib/api/server";
import type { ReportOverview } from "@/lib/api/types";

export async function fetchReportOverview(exerciseId?: number): Promise<ReportOverview> {
  const qs = exerciseId != null ? `?exerciseId=${exerciseId}` : "";
  return apiFetch(`/reports/overview${qs}`);
}
