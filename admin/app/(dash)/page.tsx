import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";

import { TrendChart } from "@/components/charts/trend-chart";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { PROVIDER_LABEL } from "@/lib/labels";
import { formatNumber, formatScore } from "@/lib/format";
import {
  getStatsOverview,
  getTimeseries,
  listLlmModels,
} from "@/lib/mock/admin-api";

export const metadata = { title: "대시보드" };

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card className="p-5">
      <p className="text-sm text-text-muted">{label}</p>
      <p className="mt-2 font-mono text-3xl font-semibold tabular-nums">{value}</p>
      {sub && <p className="mt-1 text-xs text-text-subtle">{sub}</p>}
    </Card>
  );
}

export default async function DashboardPage() {
  const [overview, points, models] = await Promise.all([
    getStatsOverview(),
    getTimeseries(),
    listLlmModels(),
  ]);
  const activeModel = models.find((m) => m.isActive);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">운영 대시보드</h2>
        <p className="mt-1 text-sm text-text-muted">
          회원·세션·LLM·데이터 내보내기 현황을 한눈에 봅니다.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="전체 회원"
          value={formatNumber(overview.totalUsers)}
          sub={`활성 ${formatNumber(overview.activeUsers)} · 정지 ${overview.suspendedUsers} · 탈퇴 ${overview.withdrawnUsers}`}
        />
        <StatCard
          label="활성 회원"
          value={formatNumber(overview.activeUsers)}
          sub={`전체의 ${Math.round((overview.activeUsers / overview.totalUsers) * 100)}%`}
        />
        <StatCard
          label="누적 세션"
          value={formatNumber(overview.totalSessions)}
          sub={`평균 점수 ${formatScore(overview.avgScore)}점`}
        />
        <StatCard
          label="정지 회원"
          value={formatNumber(overview.suspendedUsers)}
          sub="관리 확인 필요"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">최근 30일 추이</h3>
            <span className="text-xs text-text-subtle">가입 · 세션</span>
          </CardHeader>
          <CardBody>
            <TrendChart points={points} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">활성 RAG LLM 모델</h3>
            <Link
              href="/llm"
              className="text-xs text-accent hover:text-accent-active"
            >
              관리
            </Link>
          </CardHeader>
          <CardBody className="space-y-4">
            {activeModel ? (
              <div className="rounded-sm border border-border bg-surface-muted p-4">
                <div className="flex items-center gap-3">
                  <Sparkles className="size-5 text-accent" aria-hidden />
                  <div>
                    <p className="text-sm font-medium">
                      {activeModel.displayName}
                    </p>
                    <p className="text-xs text-text-subtle">
                      {PROVIDER_LABEL[activeModel.provider]} ·{" "}
                      <span className="font-mono">{activeModel.modelName}</span>
                    </p>
                  </div>
                  <Badge tone="success" className="ml-auto">
                    활성
                  </Badge>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted">활성 모델이 없습니다.</p>
            )}
            <Link
              href="/exports"
              className="flex items-center justify-between rounded-sm border border-border px-4 py-3 text-sm font-medium transition-colors hover:bg-surface-muted"
            >
              운동 좌표 데이터 내보내기
              <ArrowRight className="size-4 text-text-subtle" aria-hidden />
            </Link>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
