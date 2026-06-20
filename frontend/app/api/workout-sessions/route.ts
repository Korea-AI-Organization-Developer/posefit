import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function POST(req: NextRequest) {
  const token = (await cookies()).get("accessToken")?.value;
  const body = await req.json();

  const res = await fetch(`${API_BASE}/workout-sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  let resBody: unknown;
  try {
    resBody = await res.json();
  } catch {
    resBody = null;
  }

  return NextResponse.json(resBody, { status: res.status });
}
