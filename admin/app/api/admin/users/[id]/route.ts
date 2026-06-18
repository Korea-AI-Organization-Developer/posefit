import { type NextRequest, NextResponse } from "next/server";

import { apiFetch, ApiError } from "@/lib/api/server";
import type { AdminUserDetail } from "@/lib/api/types";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await request.json();

  try {
    const data = await apiFetch<AdminUserDetail>(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (e) {
    if (e instanceof ApiError) {
      return NextResponse.json(e.body ?? {}, { status: e.status });
    }
    return NextResponse.json({ detail: "서버 오류" }, { status: 500 });
  }
}
