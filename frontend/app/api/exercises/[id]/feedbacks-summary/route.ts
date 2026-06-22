import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

/*
 * BFF: 운동 종합 피드백 — 클라이언트(workout-live)가 호출.
 * httpOnly accessToken 쿠키를 읽어 백엔드 POST /exercises/{id}/feedbacks:summary 로 전달한다.
 * (백엔드 경로의 ':summary' 는 폴더명에 쓸 수 없어 라우트는 /feedbacks-summary 로 둔다.)
 */
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const token = (await cookies()).get("accessToken")?.value;
  const payload = await req.json();

  const res = await fetch(`${API_BASE}/exercises/${id}/feedbacks:summary`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  return NextResponse.json(body, { status: res.status });
}
