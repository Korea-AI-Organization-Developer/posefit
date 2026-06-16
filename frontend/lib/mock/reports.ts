/*
 * 리포트 목업 — docs/openapi.yaml ReportSummary / ScoreTrendResponse 기준.
 *   getReportSummary() → GET /api/v1/reports/summary
 *   getScoreTrend()    → GET /api/v1/reports/score-trend
 * API 준비 후 lib/api/reports.ts 로 교체 (시그니처 동일).
 *
 * 데이터는 가입일(SIGNUP_DATE)~기준일(MOCK_TODAY)의 결정론적 세션 기록에서 파생한다.
 * 같은 입력엔 항상 같은 출력 → 정적 빌드 결과가 흔들리지 않는다.
 */

import { MOCK_TODAY } from "./dashboard";
import type { EmbeddedExercise } from "./workout-sessions";

export type ReportPeriod = "day" | "week" | "month" | "cumulative";
export type TrendDays = 7 | 30 | 90;

export interface BestExercise {
  id: number;
  nameKo: string;
  bestScore: number;
}

export interface ReportSummary {
  period: ReportPeriod;
  periodStart: string;
  periodEnd: string;
  sessionsCount: number;
  totalDurationSec: number;
  avgScore: number | null;
  bestExercise: BestExercise | null;
}

export interface ScoreTrendPoint {
  date: string;
  avgScore: number;
}

export interface ScoreTrendSeries {
  exercise: EmbeddedExercise;
  points: ScoreTrendPoint[];
}

export interface ScoreTrendResponse {
  series: ScoreTrendSeries[];
}

/* dashboard/exercises 목업과 동일한 종목. base = 평균 점수 기준선. */
const EXERCISES = [
  { id: 1, nameKo: "런지", base: 80, dynamic: true },
  { id: 2, nameKo: "플랭크", base: 84, dynamic: false },
  { id: 3, nameKo: "푸쉬업", base: 83, dynamic: true },
  { id: 4, nameKo: "오버헤드프레스", base: 77, dynamic: true },
];

const SIGNUP_DATE = "2026-03-12";

// ─── 날짜 유틸 (YYYY-MM-DD 를 UTC 자정으로 다뤄 TZ 흔들림 제거) ──────────────
function toUTC(date: string): Date {
  return new Date(`${date}T00:00:00Z`);
}
function fmt(d: Date): string {
  return d.toISOString().slice(0, 10);
}
function addDays(date: string, n: number): string {
  const d = toUTC(date);
  d.setUTCDate(d.getUTCDate() + n);
  return fmt(d);
}
function daysBetween(a: string, b: string): number {
  return Math.round((toUTC(b).getTime() - toUTC(a).getTime()) / 86_400_000);
}
/** 월요일 시작 주의 [월, 일] 경계 — weeklySessionsCount(월~일 KST)와 정렬 */
function weekBounds(date: string): [string, string] {
  const mondayIdx = (toUTC(date).getUTCDay() + 6) % 7;
  const start = addDays(date, -mondayIdx);
  return [start, addDays(start, 6)];
}
function monthBounds(date: string): [string, string] {
  const d = toUTC(date);
  const y = d.getUTCFullYear();
  const m = d.getUTCMonth();
  return [fmt(new Date(Date.UTC(y, m, 1))), fmt(new Date(Date.UTC(y, m + 1, 0)))];
}
function periodBounds(period: ReportPeriod, ref: string): [string, string] {
  if (period === "day") return [ref, ref];
  if (period === "week") return weekBounds(ref);
  if (period === "month") return monthBounds(ref);
  return [SIGNUP_DATE, ref]; // cumulative
}

// ─── 결정론적 난수·점수 ────────────────────────────────────────────────────
function hash01(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295; // [0,1]
}
const round2 = (x: number) => Math.round(x * 100) / 100;
const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

const TOTAL_DAYS = daysBetween(SIGNUP_DATE, MOCK_TODAY);

/** 가입 이후 완만한 우상향(+8점) + 결정론적 흔들림. seed 로 용도(기록/추이)를 분리. */
function scoreFor(date: string, exId: number, base: number, seed: string): number {
  const progress = clamp(daysBetween(SIGNUP_DATE, date) / TOTAL_DAYS, 0, 1);
  const jitter = (hash01(`${date}:${exId}:${seed}`) - 0.5) * 8;
  return clamp(round2(base + progress * 8 + jitter), 60, 99);
}

// ─── 세션 기록 fixture (요약 집계용) ───────────────────────────────────────
interface SessionRecord {
  date: string;
  exerciseId: number;
  nameKo: string;
  score: number;
  durationSec: number;
}

const RECORDS: SessionRecord[] = (() => {
  const out: SessionRecord[] = [];
  for (let i = 0; i <= TOTAL_DAYS; i++) {
    const date = addDays(SIGNUP_DATE, i);
    for (const ex of EXERCISES) {
      if (hash01(`${date}:${ex.id}:do`) > 0.18) continue; // 종목당 하루 ~18%
      out.push({
        date,
        exerciseId: ex.id,
        nameKo: ex.nameKo,
        score: scoreFor(date, ex.id, ex.base, "rec"),
        durationSec: 90 + Math.floor(hash01(`${date}:${ex.id}:dur`) * 90),
      });
    }
  }
  return out;
})();

/* 기간 요약 (Q-R11). bestExercise 는 기간 내 최고 단일 점수(best_score) 종목. */
export async function getReportSummary(
  period: ReportPeriod,
  referenceDate?: string,
  exerciseId?: number,
): Promise<ReportSummary> {
  const ref = referenceDate ?? MOCK_TODAY;
  const [periodStart, periodEnd] = periodBounds(period, ref);

  let recs = RECORDS.filter((r) => r.date >= periodStart && r.date <= periodEnd);
  if (exerciseId != null) recs = recs.filter((r) => r.exerciseId === exerciseId);

  const sessionsCount = recs.length;
  const totalDurationSec = recs.reduce((a, r) => a + r.durationSec, 0);
  const avgScore = sessionsCount
    ? round2(recs.reduce((a, r) => a + r.score, 0) / sessionsCount)
    : null;

  let bestExercise: BestExercise | null = null;
  if (recs.length) {
    const top = recs.reduce((a, r) => (r.score > a.score ? r : a));
    bestExercise = { id: top.exerciseId, nameKo: top.nameKo, bestScore: top.score };
  }

  return {
    period,
    periodStart,
    periodEnd,
    sessionsCount,
    totalDurationSec,
    avgScore,
    bestExercise,
  };
}

/** 차트용 틱 — 시리즈가 같은 x 좌표를 공유하도록 균일 간격으로 뽑는다. */
function trendTicks(days: number): string[] {
  const step = days <= 7 ? 1 : days <= 30 ? 3 : 10;
  const set = new Set<string>();
  for (let offset = 0; offset < days; offset += step) {
    set.add(addDays(MOCK_TODAY, -offset));
  }
  set.add(addDays(MOCK_TODAY, -(days - 1))); // 시작 경계 보장
  return [...set].sort(); // YYYY-MM-DD 사전식 = 시간순
}

/* 점수 추이 (Q-R12). 종목별 시리즈, 모든 시리즈가 동일 틱 날짜를 갖는다. */
export async function getScoreTrend(
  days: TrendDays,
  exerciseId?: number,
): Promise<ScoreTrendResponse> {
  const ticks = trendTicks(days);
  const exes =
    exerciseId != null ? EXERCISES.filter((e) => e.id === exerciseId) : EXERCISES;

  const series: ScoreTrendSeries[] = exes.map((ex) => ({
    exercise: { id: ex.id, nameKo: ex.nameKo },
    points: ticks.map((date) => ({
      date,
      avgScore: scoreFor(date, ex.id, ex.base, "trend"),
    })),
  }));

  return { series };
}
