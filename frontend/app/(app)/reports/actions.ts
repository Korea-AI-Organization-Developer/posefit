"use server";

import { apiFetch } from "@/lib/api/server";
import type { ReportOverview } from "@/lib/api/types";

export async function fetchReportOverview(): Promise<ReportOverview> {
  return apiFetch("/reports/overview");
}
