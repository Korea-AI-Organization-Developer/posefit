import type { TimeseriesPoint } from "@/lib/api/types";
import { formatDayShort } from "@/lib/format";

/*
 * 의존성 없는 SVG 라인 차트 (가입·세션 2계열).
 * 저장소가 차트 라이브러리를 두지 않는 방침이라 직접 그린다(소비자 앱 동일).
 */

const W = 760;
const H = 220;
const PAD = { top: 16, right: 16, bottom: 28, left: 32 };

function buildPath(values: number[], max: number): string {
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const stepX = values.length > 1 ? innerW / (values.length - 1) : 0;
  return values
    .map((v, i) => {
      const x = PAD.left + i * stepX;
      const y = PAD.top + innerH - (max === 0 ? 0 : (v / max) * innerH);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function TrendChart({ points }: { points: TimeseriesPoint[] }) {
  if (points.length === 0) {
    return <p className="text-sm text-text-muted">표시할 데이터가 없습니다.</p>;
  }

  const signups = points.map((p) => p.signups);
  const sessions = points.map((p) => p.sessions);
  const max = Math.max(1, ...signups, ...sessions);

  const tickIdx = [0, Math.floor((points.length - 1) / 2), points.length - 1];

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center gap-4 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-full bg-accent" /> 세션
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-full bg-border-strong" /> 가입
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label="최근 30일 가입·세션 추이"
      >
        <line
          x1={PAD.left}
          y1={H - PAD.bottom}
          x2={W - PAD.right}
          y2={H - PAD.bottom}
          className="stroke-border"
          strokeWidth={1}
        />
        <path
          d={buildPath(sessions, max)}
          fill="none"
          className="stroke-accent"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <path
          d={buildPath(signups, max)}
          fill="none"
          className="stroke-border-strong"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {tickIdx.map((i) => {
          const innerW = W - PAD.left - PAD.right;
          const stepX = points.length > 1 ? innerW / (points.length - 1) : 0;
          const x = PAD.left + i * stepX;
          return (
            <text
              key={i}
              x={x}
              y={H - 8}
              textAnchor="middle"
              className="fill-text-subtle text-[10px]"
            >
              {formatDayShort(points[i].date)}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
