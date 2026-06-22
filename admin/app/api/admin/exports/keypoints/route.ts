import { type NextRequest } from "next/server";
import { cookies } from "next/headers";

import { ADMIN_ACCESS_COOKIE } from "@/lib/auth/cookies";
import { API_BASE } from "@/lib/api/server";

export async function GET(request: NextRequest) {
  const token = (await cookies()).get(ADMIN_ACCESS_COOKIE)?.value;
  if (!token) {
    return new Response(JSON.stringify({ detail: "인증이 필요합니다" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const qs = request.nextUrl.searchParams.toString();
  const upstream = await fetch(`${API_BASE}/admin/exports/keypoints?${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!upstream.ok) {
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  const contentType = upstream.headers.get("Content-Type") ?? "application/octet-stream";
  const disposition = upstream.headers.get("Content-Disposition") ?? "";

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": contentType,
      "Content-Disposition": disposition,
    },
  });
}
