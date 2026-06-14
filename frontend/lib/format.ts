/* 날짜·점수 표시 포맷 — KST 기준 (서버/클라이언트 어디서 렌더해도 동일) */

const sessionTimeFormatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  month: "long",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

/** "2026-06-09T18:30:00+09:00" → "6월 9일 18:30" */
export function formatSessionTime(iso: string): string {
  return sessionTimeFormatter.format(new Date(iso));
}

const dayFormatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  month: "long",
  day: "numeric",
});

/** "2026-06-09" → "6월 9일" */
export function formatDay(date: string): string {
  return dayFormatter.format(new Date(`${date}T00:00:00+09:00`));
}

const dateWithWeekdayFormatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  month: "long",
  day: "numeric",
  weekday: "long",
});

/** "2026-06-10" → "6월 10일 수요일" */
export function formatDateWithWeekday(date: string): string {
  return dateWithWeekdayFormatter.format(new Date(`${date}T00:00:00+09:00`));
}

/** 92.25 → "92" (표시용 반올림 — 원본 DECIMAL(5,2)은 데이터에 유지) */
export function formatScore(score: number): string {
  return String(Math.round(score));
}
