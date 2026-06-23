import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const BACKEND_ORIGIN = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/api\/v1\/?$/, "");

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const token = (await cookies()).get("accessToken")?.value;

  const backendUrl = `${BACKEND_ORIGIN}/saves/${path.join("/")}`;

  const res = await fetch(backendUrl, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) {
    return new NextResponse(null, { status: res.status });
  }

  // 백엔드 응답을 그대로 스트리밍 — Content-Type, Content-Length 등 보존
  return new NextResponse(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") ?? "video/mp4",
      "Content-Length": res.headers.get("Content-Length") ?? "",
      "Accept-Ranges": "bytes",
      "Cache-Control": "private, max-age=3600",
    },
  });
}
