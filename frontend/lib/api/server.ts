import { cookies } from "next/headers";

/*
 * 서버 전용 API fetch — Server Component·Route Handler에서만 호출한다.
 * httpOnly accessToken 쿠키를 읽어 FastAPI에 Authorization: Bearer로 전달하는 BFF 패턴.
 * (proxy.ts는 cookies()를 못 쓰므로 자체 fetch를 사용한다.)
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** 비-2xx 응답 — status와 파싱된 본문(있으면)을 담는다 */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body?: unknown,
  ) {
    super(`API ${status}`);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = (await cookies()).get("accessToken")?.value;
  const isForm = init?.body instanceof FormData;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      // FormData는 boundary를 브라우저/런타임이 설정하므로 Content-Type을 지정하지 않는다
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

/**
 * ApiError에서 사용자에게 보일 메시지를 뽑는다.
 * FastAPI HTTPException → { detail: "문자열" }, 검증 실패 → { detail: [{ msg }] }.
 */
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
