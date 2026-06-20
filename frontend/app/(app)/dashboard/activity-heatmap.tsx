import { Card, CardBody, CardHeader } from "@/components/ui";
import { formatDay } from "@/lib/format";
import type { CalendarDay } from "@/lib/api/reports";

const TOTAL_DAYS = 30;

/* 주 시작은 월요일 — weeklySessionsCount 의 월~일(KST) 기준과 맞춘다 */
const WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"];

/* 활동 강도 — accent 알파(명도) 차로만 구분한다 */
function intensityClass(count: number): string {
  if (count === 0) return "bg-surface-muted";
  if (count === 1) return "bg-accent/25";
  if (count === 2) return "bg-accent/55";
  return "bg-accent";
}

/** baseDate(YYYY-MM-DD)에서 과거 N일의 날짜 목록 — 오래된 날부터 */
function lastNDates(baseDate: string, n: number): string[] {
  const base = new Date(`${baseDate}T00:00:00Z`);
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(base);
    d.setUTCDate(base.getUTCDate() - (n - 1 - i));
    return d.toISOString().slice(0, 10);
  });
}

/** 월요일=0 … 일요일=6 */
function mondayIndex(date: string): number {
  return (new Date(`${date}T00:00:00Z`).getUTCDay() + 6) % 7;
}

/*
 * MAIN-06 — 최근 30일 활동 히트맵.
 * 열=요일(월~일) 달력 정렬 — 칸의 위치가 "무슨 요일에 운동하는가"를 보여준다.
 * API는 운동한 날만 줄 수 있으므로 날짜로 매칭한다.
 */
export function ActivityHeatmap({
  days,
  baseDate,
}: {
  days: CalendarDay[];
  baseDate: string;
}) {
  const countByDate = new Map(days.map((d) => [d.date, d.sessionsCount]));
  const dates = lastNDates(baseDate, TOTAL_DAYS);
  const activeDays = dates.filter((date) => (countByDate.get(date) ?? 0) > 0);
  const leadingBlanks = mondayIndex(dates[0]);

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">최근 30일 활동</h2>
        <span className="text-xs text-text-subtle">
          {activeDays.length}일 운동
        </span>
      </CardHeader>
      <CardBody>
        <div role="img" aria-label={`최근 30일 중 ${activeDays.length}일 운동`}>
          <div className="grid grid-cols-7 gap-1.5">
            {WEEKDAY_LABELS.map((label) => (
              <span
                key={label}
                className="text-center text-xs text-text-subtle"
              >
                {label}
              </span>
            ))}
            {Array.from({ length: leadingBlanks }, (_, i) => (
              <span key={`blank-${i}`} />
            ))}
            {dates.map((date) => {
              const count = countByDate.get(date) ?? 0;
              return (
                <span
                  key={date}
                  title={`${formatDay(date)} · ${count}회`}
                  className={`aspect-square rounded-xs ${intensityClass(count)}`}
                />
              );
            })}
          </div>
        </div>
        <div className="mt-4 flex items-center justify-end gap-1.5 text-xs text-text-subtle">
          적음
          <span className="size-2.5 rounded-xs bg-surface-muted" />
          <span className="size-2.5 rounded-xs bg-accent/25" />
          <span className="size-2.5 rounded-xs bg-accent/55" />
          <span className="size-2.5 rounded-xs bg-accent" />
          많음
        </div>
      </CardBody>
    </Card>
  );
}
