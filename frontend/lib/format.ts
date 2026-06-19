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

/*
 * 백엔드가 타임존 표기 없이 보내는 datetime("2026-06-09T09:30:00")은 UTC(naive)다.
 * JS `new Date()`는 표기가 없으면 "로컬 시간"으로 해석하므로, 표기가 없을 때만 'Z'를
 * 붙여 UTC로 확정한 뒤 KST로 포맷한다. (이미 offset/Z가 있으면 그대로 둔다.)
 */
function asUtcDate(iso: string): Date {
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`);
}

/** 백엔드 datetime(UTC, 표기 없음 가능) → "6월 9일 18:30" (KST) */
export function formatFeedbackTime(iso: string): string {
  return sessionTimeFormatter.format(asUtcDate(iso));
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

/** 누적 운동 시간: 141 → "2분 21초", 3600 → "1시간", 4530 → "1시간 15분" */
export function formatDuration(totalSec: number): string {
  if (totalSec <= 0) return "0초";
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return m > 0 ? `${h}시간 ${m}분` : `${h}시간`;
  if (m > 0) return s > 0 ? `${m}분 ${s}초` : `${m}분`;
  return `${s}초`;
}

/** 저장 용량: 260046848 → "248 MB", 1610612736 → "1.5 GB" */
export function formatBytes(bytes: number): string {
  if (bytes <= 0) return "0 MB";
  const mb = bytes / (1024 * 1024);
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
}
