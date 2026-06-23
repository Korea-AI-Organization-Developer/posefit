"use client";

import { useState } from "react";
import { TrendChart } from "@/components/charts/trend-chart";
import { Card, CardBody, CardHeader } from "@/components/ui";
import type { TimeseriesPoint } from "@/lib/api/types";

const PERIODS = [
  { label: "7일", days: 7 },
  { label: "30일", days: 30 },
  { label: "90일", days: 90 },
] as const;

type Period = (typeof PERIODS)[number]["days"];

async function fetchTimeseries(days: number): Promise<TimeseriesPoint[]> {
  const to = new Date();
  const from = new Date(to);
  from.setDate(from.getDate() - (days - 1));

  const qs = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
  });
  const res = await fetch(`/api/admin/stats/timeseries?${qs.toString()}`);
  if (!res.ok) throw new Error("timeseries fetch failed");
  const data = await res.json();
  return data.points;
}

export function TimeseriesSection({
  initialPoints,
}: {
  initialPoints: TimeseriesPoint[];
}) {
  const [period, setPeriod] = useState<Period>(30);
  const [points, setPoints] = useState(initialPoints);
  const [loading, setLoading] = useState(false);

  async function handlePeriod(days: Period) {
    if (days === period) return;
    setLoading(true);
    try {
      const next = await fetchTimeseries(days);
      setPoints(next);
      setPeriod(days);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="text-sm font-semibold">추이</h3>
        <div className="flex items-center gap-1">
          {PERIODS.map(({ label, days }) => (
            <button
              key={days}
              onClick={() => handlePeriod(days)}
              disabled={loading}
              className={[
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                period === days
                  ? "bg-accent text-white"
                  : "text-text-muted hover:bg-surface-muted",
              ].join(" ")}
            >
              {label}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardBody>
        <div className={loading ? "opacity-50 transition-opacity" : ""}>
          <TrendChart points={points} />
        </div>
      </CardBody>
    </Card>
  );
}
