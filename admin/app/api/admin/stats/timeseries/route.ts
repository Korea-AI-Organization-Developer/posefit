import { type NextRequest, NextResponse } from "next/server";

import { ApiError, apiFetch } from "@/lib/api/server";
import type { StatsTimeseries } from "@/lib/api/types";

export async function GET(request: NextRequest) {
  const from = request.nextUrl.searchParams.get("from");
  const to = request.nextUrl.searchParams.get("to");

  try {
    const data = await apiFetch<StatsTimeseries>(
      `/admin/stats/timeseries?from=${from}&to=${to}`,
    );
    return NextResponse.json(data);
  } catch (e) {
    if (e instanceof ApiError) {
      return NextResponse.json(e.body ?? {}, { status: e.status });
    }
    return NextResponse.json({ detail: "서버 오류" }, { status: 500 });
  }
}
