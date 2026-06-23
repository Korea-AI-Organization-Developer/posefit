"use client";

import { useState } from "react";
import { Button, Dialog } from "@/components/ui";
import type { ReportOverview } from "@/lib/api/types";
import { fetchReportOverview } from "./actions";


function formatDuration(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}시간 ${m}분`;
  return `${m}분`;
}

/* 활동 강도 — 운동 횟수 기준, 대시보드 ActivityHeatmap 과 동일한 5단계 초록 톤 */
const LEVEL_COLORS = ["#EDEDEE", "#C8EDE4", "#8DD5C3", "#46BBA2", "#0D9B7B"];

function sessionLevel(count: number): number {
  if (count <= 0) return 0;
  if (count <= 2) return 1;
  if (count <= 5) return 2;
  if (count <= 9) return 3;
  return 4;
}

function CalendarGrid({ days }: { days: ReportOverview["calendar"]["days"] }) {
  const todayStr = new Date().toISOString().slice(0, 10);
  const firstDow = days.length > 0 ? (new Date(days[0].date).getDay() + 6) % 7 : 0;

  return (
    <div>
      <div className="grid grid-cols-7 gap-1.5">
        {["월", "화", "수", "목", "금", "토", "일"].map((d) => (
          <div key={d} className="py-1 text-center text-xs text-text-muted">{d}</div>
        ))}
        {Array.from({ length: firstDow }, (_, i) => (
          <div key={`empty-${i}`} className="aspect-square" />
        ))}
        {days.map((day) => {
          const isToday = day.date === todayStr;
          const tooltip = day.sessionsCount > 0
            ? `${day.date} · ${day.sessionsCount}회${day.avgScore != null ? ` · 평균 ${day.avgScore}점` : ""}`
            : day.date;
          return (
            <div
              key={day.date}
              title={tooltip}
              style={{
                backgroundColor: LEVEL_COLORS[sessionLevel(day.sessionsCount)],
                outline: isToday ? "2px solid #1D9E75" : undefined,
                outlineOffset: isToday ? "1px" : undefined,
              }}
              className="aspect-square cursor-pointer rounded-md transition-transform hover:scale-110"
            />
          );
        })}
      </div>
      {/* 범례 */}
      <div className="mt-3 flex items-center justify-end gap-1.5">
        <span className="text-xs text-text-muted">적음</span>
        {LEVEL_COLORS.map((color) => (
          <div key={color} className="size-3.5 rounded-sm" style={{ backgroundColor: color }} />
        ))}
        <span className="text-xs text-text-muted">많음</span>
      </div>
    </div>
  );
}

export function OverviewDialog({ exerciseId }: { exerciseId?: number }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ReportOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function handleOpen() {
    setOpen(true);
    if (data) return;
    setLoading(true);
    setError(false);
    try {
      const result = await fetchReportOverview(exerciseId);
      setData(result);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  const { summary, calendar, scoreTrend } = data ?? {};

  return (
    <>
      <Button variant="secondary" size="sm" onClick={handleOpen}>
        전체 보기
      </Button>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="운동 전체 요약"
        size="lg"
      >
        {loading && (
          <p className="py-10 text-center text-sm text-text-muted">불러오는 중...</p>
        )}
        {error && (
          <p className="py-10 text-center text-sm text-red-500">데이터를 불러오지 못했어요.</p>
        )}
        {data && summary && (
          <div className="space-y-6">
            {/* 누적 요약 */}
            <section>
              <h3 className="mb-3 text-sm font-semibold text-text-muted">누적 통계</h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <StatBox label="총 운동 횟수" value={`${summary.sessionsCount}회`} />
                <StatBox label="총 운동 시간" value={formatDuration(summary.totalDurationSec)} />
                <StatBox label="평균 점수" value={summary.avgScore != null ? `${summary.avgScore}점` : "-"} />
                <StatBox
                  label="최고 종목"
                  value={summary.bestExercise ? summary.bestExercise.nameKo : "-"}
                  sub={summary.bestExercise ? `최고 ${summary.bestExercise.bestScore}점` : undefined}
                />
              </div>
            </section>

            {/* 최근 30일 캘린더 */}
            {calendar && (
              <section>
                <h3 className="mb-3 text-sm font-semibold text-text-muted">최근 30일 활동</h3>
                <CalendarGrid days={calendar.days} />
              </section>
            )}

            {/* 종목별 최근 점수 */}
            <section>
              <h3 className="mb-3 text-sm font-semibold text-text-muted">종목별 최근 점수 (90일)</h3>
              {scoreTrend && scoreTrend.series.length > 0 ? (
                <div className="space-y-2">
                  {scoreTrend.series.map((s) => {
                    const latest = s.points.at(-1);
                    return (
                      <div key={s.exercise.id} className="flex items-center justify-between rounded-md bg-surface-muted px-4 py-2 text-sm">
                        <span>{s.exercise.nameKo}</span>
                        <span className="font-medium">{latest ? `${latest.avgScore}점` : "-"}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-text-muted">최근 90일간 운동 기록이 없어요.</p>
              )}
            </section>

            {/* 종합 평가 */}
            {data.evaluation && (
              <section>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-muted">
                  종합 평가
                  {data.evaluation.source === "ai" && (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                      AI
                    </span>
                  )}
                </h3>
                {data.evaluation.summary && (
                  <p className="mb-3 rounded-md bg-surface-muted px-4 py-3 text-sm leading-relaxed">
                    {data.evaluation.summary}
                  </p>
                )}
                {data.evaluation.messages.length === 0 ? (
                  <p className="text-sm text-text-muted">평가 데이터가 없어요.</p>
                ) : (
                  <div className="space-y-2">
                    {data.evaluation.messages.map((msg, i) => {
                      const icon =
                        msg.type === "positive" ? "💪"
                        : msg.type === "warning" ? "⚠️"
                        : "💡";
                      return (
                        <div key={i} className="flex gap-3 rounded-md bg-surface-muted px-4 py-3 text-sm">
                          <span className="shrink-0">{icon}</span>
                          <span className="text-text-muted">{msg.text}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            )}
          </div>
        )}
      </Dialog>
    </>
  );
}

function StatBox({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-md bg-surface-muted px-4 py-3">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="mt-1 text-base font-semibold">{value}</p>
      {sub && <p className="text-xs text-text-muted">{sub}</p>}
    </div>
  );
}
