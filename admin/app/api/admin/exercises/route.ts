import { type NextRequest, NextResponse } from "next/server";

import { ApiError, apiFetch } from "@/lib/api/server";
import type { AdminExercise } from "@/lib/api/types";

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const data = await apiFetch<AdminExercise>("/admin/exercises", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data, { status: 201 });
  } catch (e) {
    if (e instanceof ApiError) {
      return NextResponse.json(e.body ?? {}, { status: e.status });
    }
    return NextResponse.json({ detail: "서버 오류" }, { status: 500 });
  }
}
