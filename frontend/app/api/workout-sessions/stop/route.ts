import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function POST(req: NextRequest) {
  const token = (await cookies()).get("accessToken")?.value;
  const formData = await req.formData();

  const res = await fetch(`${API_BASE}/workout-sessions:stop`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  // 상대 경로 videoUrl → 절대 URL 변환
  if (
    res.ok &&
    body &&
    typeof body === "object" &&
    "videoUrl" in body &&
    typeof (body as { videoUrl: string }).videoUrl === "string" &&
    (body as { videoUrl: string }).videoUrl.startsWith("/")
  ) {
    const serverOrigin = new URL(API_BASE).origin;
    (body as { videoUrl: string }).videoUrl =
      `${serverOrigin}${(body as { videoUrl: string }).videoUrl}`;
  }

  return NextResponse.json(body, { status: res.status });
}
