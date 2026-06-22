"use client";

import { type MouseEvent, useMemo, useRef, useState } from "react";
import { formatDay, formatScore } from "@/lib/format";
import type { ScoreTrendSeries } from "@/lib/api/reports";

/* viewBox 좌표계 — 컨테이너 너비에 맞춰 반응형으로 스케일된다. */
const W = 640;
const H = 260;
const PAD = { l: 36, r: 16, t: 16, b: 28 };
const PLOT_W = W - PAD.l - PAD.r;
const PLOT_H = H - PAD.t - PAD.b;

/* 멀티 시리즈 구분 — 색은 accent 하나로 통일하고 대시 패턴으로만 나눈다(절제). */
const DASHES = ["", "5 4", "1.5 4", "7 4 1.5 4"];

const Y_MAX = 100;
const Y_STEP = 10;

function shortDate(date: string): string {
  const [, m, d] = date.split("-");
  return `${+m}/${+d}`;
}

interface Geometry {
  dates: string[];
  yMin: number;
  xs: number[];
  gridYs: { value: number; y: number }[];
}

/* REP-02 — 점수 추이. 차트 라이브러리 없이 SVG 로 직접 그린다. */
export function ScoreTrendChart({ series }: { series: ScoreTrendSeries[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [hoverSeries, setHoverSeries] = useState<number | null>(null);

  const dates = series[0]?.points.map((p) => p.date) ?? [];
  const n = dates.length;

  const geo = useMemo<Geometry>(() => {
    const values = series.flatMap((s) => s.points.map((p) => p.avgScore));
    const dataMin = values.length ? Math.min(...values) : Y_MAX;
    // 점수가 몰린 구간을 확대해 보여주되 0~90 사이로만 바닥을 잡는다.
    const yMin = Math.min(90, Math.max(0, Math.floor((dataMin - 5) / 10) * 10));
    const xAt = (i: number) =>
      n <= 1 ? PAD.l + PLOT_W / 2 : PAD.l + (i / (n - 1)) * PLOT_W;
    const gridYs: Geometry["gridYs"] = [];
    for (let v = yMin; v <= Y_MAX; v += Y_STEP) {
      gridYs.push({ value: v, y: PAD.t + (1 - (v - yMin) / (Y_MAX - yMin)) * PLOT_H });
    }
    return {
      dates,
      yMin,
      xs: Array.from({ length: n }, (_, i) => xAt(i)),
      gridYs,
    };
  }, [series, dates, n]);

  const yAt = (v: number) =>
    PAD.t + (1 - (v - geo.yMin) / (Y_MAX - geo.yMin)) * PLOT_H;

  // x축 라벨 — 최대 6개만 노출해 겹침을 막는다.
  const labelStep = Math.max(1, Math.ceil(n / 6));
  const labelIdx = new Set<number>();
  for (let i = 0; i < n; i += labelStep) labelIdx.add(i);
  if (n > 0) labelIdx.add(n - 1);

  function handleMove(e: MouseEvent<SVGSVGElement>) {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || n === 0) return;
    const localX = ((e.clientX - rect.left) / rect.width) * W;
    let best = 0;
    let bestD = Infinity;
    for (let i = 0; i < n; i++) {
      const d = Math.abs(geo.xs[i] - localX);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    }
    setHoverIndex(best);
  }

  if (n === 0) {
    return (
      <div className="flex h-60 items-center justify-center rounded-md border border-dashed border-border">
        <p className="text-sm text-text-muted">표시할 점수 데이터가 없어요</p>
      </div>
    );
  }

  const hoverX = hoverIndex != null ? geo.xs[hoverIndex] : null;

  return (
    <div>
      {/* 범례 — 항목에 호버하면 해당 시리즈를 강조 */}
      {series.length > 1 && (
        <ul className="mb-3 flex flex-wrap gap-x-4 gap-y-1.5">
          {series.map((s, i) => (
            <li
              key={s.exercise.id}
              onMouseEnter={() => setHoverSeries(s.exercise.id)}
              onMouseLeave={() => setHoverSeries(null)}
              className="flex cursor-default items-center gap-1.5 text-xs text-text-muted"
            >
              <svg width="16" height="6" aria-hidden className="overflow-visible">
                <line
                  x1="0"
                  y1="3"
                  x2="16"
                  y2="3"
                  className="stroke-accent"
                  strokeWidth="1.5"
                  strokeDasharray={DASHES[i % DASHES.length]}
                />
              </svg>
              {s.exercise.nameKo}
            </li>
          ))}
        </ul>
      )}

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          className="w-full"
          role="img"
          aria-label={`점수 추이 차트 — ${series.map((s) => s.exercise.nameKo).join(", ")}`}
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* 가로 그리드 + y축 라벨 */}
          {geo.gridYs.map(({ value, y }) => (
            <g key={value}>
              <line
                x1={PAD.l}
                y1={y}
                x2={W - PAD.r}
                y2={y}
                className={value === geo.yMin ? "stroke-border-strong" : "stroke-border"}
                strokeWidth="1"
                vectorEffect="non-scaling-stroke"
              />
              <text
                x={PAD.l - 8}
                y={y + 3}
                textAnchor="end"
                className="fill-text-subtle text-[10px] tabular-nums"
              >
                {value}
              </text>
            </g>
          ))}

          {/* x축 라벨 */}
          {[...labelIdx].sort((a, b) => a - b).map((i) => (
            <text
              key={i}
              x={geo.xs[i]}
              y={H - 8}
              textAnchor="middle"
              className="fill-text-subtle text-[10px] tabular-nums"
            >
              {shortDate(geo.dates[i])}
            </text>
          ))}

          {/* 호버 가이드 라인 */}
          {hoverX != null && (
            <line
              x1={hoverX}
              y1={PAD.t}
              x2={hoverX}
              y2={PAD.t + PLOT_H}
              className="stroke-border-strong"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          )}

          {/* 시리즈 라인 */}
          {series.map((s, i) => {
            const dimmed = hoverSeries != null && hoverSeries !== s.exercise.id;
            const points = s.points
              .map((p, idx) => `${geo.xs[idx]},${yAt(p.avgScore)}`)
              .join(" ");
            return (
              <polyline
                key={s.exercise.id}
                points={points}
                fill="none"
                className="stroke-accent"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray={DASHES[i % DASHES.length]}
                vectorEffect="non-scaling-stroke"
                style={{ opacity: dimmed ? 0.25 : 1 }}
              />
            );
          })}

          {/* 호버 지점의 각 시리즈 점 */}
          {hoverIndex != null &&
            series.map((s) => {
              const p = s.points[hoverIndex];
              if (!p) return null;
              const dimmed = hoverSeries != null && hoverSeries !== s.exercise.id;
              return (
                <circle
                  key={s.exercise.id}
                  cx={geo.xs[hoverIndex]}
                  cy={yAt(p.avgScore)}
                  r="3"
                  className="fill-surface stroke-accent"
                  strokeWidth="1.5"
                  vectorEffect="non-scaling-stroke"
                  style={{ opacity: dimmed ? 0.25 : 1 }}
                />
              );
            })}
        </svg>

        {/* 툴팁 — viewBox x 를 컨테이너 비율로 환산해 배치 */}
        {hoverIndex != null && (
          <div
            className="pointer-events-none absolute top-0 z-10 -translate-x-1/2"
            style={{ left: `${(geo.xs[hoverIndex] / W) * 100}%` }}
          >
            <div className="rounded-sm border border-border bg-surface px-2.5 py-1.5 shadow-sm">
              <p className="text-[11px] font-medium text-text-muted">
                {formatDay(geo.dates[hoverIndex])}
              </p>
              <ul className="mt-1 space-y-0.5">
                {series.map((s, i) => {
                  const p = s.points[hoverIndex];
                  if (!p) return null;
                  return (
                    <li
                      key={s.exercise.id}
                      className="flex items-center gap-1.5 text-xs whitespace-nowrap"
                    >
                      <svg width="12" height="6" aria-hidden>
                        <line
                          x1="0"
                          y1="3"
                          x2="12"
                          y2="3"
                          className="stroke-accent"
                          strokeWidth="1.5"
                          strokeDasharray={DASHES[i % DASHES.length]}
                        />
                      </svg>
                      <span className="text-text-muted">{s.exercise.nameKo}</span>
                      <span className="ml-auto font-mono font-medium tabular-nums">
                        {formatScore(p.avgScore)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
