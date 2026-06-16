import { cookies } from "next/headers";

import { ADMIN_ACCESS_COOKIE } from "@/lib/auth/cookies";

/*
 * 서버 전용 관리자 API fetch (BFF) — Server Component·Route Handler 에서만 호출.
 * httpOnly admin_accessToken 쿠키를 읽어 FastAPI 에 Authorization: Bearer 로 전달한다.
 *
 * ⚠️ 백엔드 /admin/* 미구현 단계에서는 화면이 lib/mock/* 를 사용한다.
 *    엔드포인트가 준비되면 각 페이지의 import 를 lib/mock → 이 모듈 기반 호출로 교체한다.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body?: unknown,
  ) {
    super(`API ${status}`);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = (await cookies()).get(ADMIN_ACCESS_COOKIE)?.value;
  const isForm = init?.body instanceof FormData;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.body && !isForm ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = undefined;
    }
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function apiErrorMessage(
  e: unknown,
  fallback = "요청을 처리하지 못했어요.",
): string {
  if (e instanceof ApiError && e.body && typeof e.body === "object") {
    const detail = (e.body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
      return detail[0].msg as string;
    }
  }
  return fallback;
}
