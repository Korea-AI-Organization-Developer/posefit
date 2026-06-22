import { Pagination } from "@/components/pagination";
import { Badge, Table, THead, TBody, TR, TH, TD } from "@/components/ui";
import { auditActionLabel } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import { listAuditLogs } from "@/lib/api/admin-audit";

export const metadata = { title: "감사 로그" };

const SIZE = 10;

function summarize(detail: Record<string, unknown> | null): string {
  if (!detail) return "-";
  return Object.entries(detail)
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(", ");
}

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page ?? 1) || 1);
  const result = await listAuditLogs({ page, size: SIZE });

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">감사 로그</h2>
        <p className="mt-1 text-sm text-text-muted">
          관리자의 변경·내보내기 행위 기록 (append-only). 최고 관리자만 열람합니다.
        </p>
      </div>

      <Table>
        <THead>
          <TR>
            <TH>시각</TH>
            <TH>행위</TH>
            <TH>대상</TH>
            <TH>상세</TH>
            <TH>IP</TH>
          </TR>
        </THead>
        <TBody>
          {result.items.map((log) => (
            <TR key={log.id}>
              <TD className="text-text-muted">{formatDateTime(log.createdAt)}</TD>
              <TD>
                <Badge tone="accent">{auditActionLabel(log.action)}</Badge>
              </TD>
              <TD className="font-mono text-xs text-text-muted">
                {log.targetType ? `${log.targetType}:${log.targetId}` : "-"}
              </TD>
              <TD className="max-w-xs truncate text-xs text-text-subtle" title={summarize(log.detail)}>
                {summarize(log.detail)}
              </TD>
              <TD className="font-mono text-xs text-text-subtle">
                {log.ipAddress ?? "-"}
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Pagination page={result.page} size={result.size} total={result.total} />
    </div>
  );
}
