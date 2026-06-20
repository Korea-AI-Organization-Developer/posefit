import { type NextRequest, NextResponse } from "next/server";

import { ApiError, apiFetch } from "@/lib/api/server";
import type { LlmModel } from "@/lib/api/types";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await request.json();

  try {
    const data = await apiFetch<LlmModel>(`/admin/llm/models/${id}`, {
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

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    await apiFetch(`/admin/llm/models/${id}`, { method: "DELETE" });
    return new NextResponse(null, { status: 204 });
  } catch (e) {
    if (e instanceof ApiError) {
      return NextResponse.json(e.body ?? {}, { status: e.status });
    }
    return NextResponse.json({ detail: "서버 오류" }, { status: 500 });
  }
}
