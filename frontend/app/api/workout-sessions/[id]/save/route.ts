import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const token = (await cookies()).get("accessToken")?.value;

  const res = await fetch(`${API_BASE}/workout-sessions/${id}:save`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  return NextResponse.json(body, { status: res.status });
}
