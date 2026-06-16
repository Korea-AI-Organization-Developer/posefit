/*
 * 표시용 포맷 헬퍼 — 모두 KST(Asia/Seoul) 기준, Server/Client 동일 결과.
 * (소비자 앱 frontend/lib/format.ts 의 관리자용 축약본)
 */

const KST = "Asia/Seoul";

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: KST,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: KST,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(d);
}

/** "6월 9일" 형태 (차트 축 라벨 등) */
export function formatDayShort(iso: string): string {
  const d = new Date(iso);
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: KST,
    month: "long",
    day: "numeric",
  }).format(d);
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "-";
  return Math.round(score).toString();
}

/** 1,234 천 단위 구분 */
export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "-";
  return new Intl.NumberFormat("ko-KR").format(n);
}
