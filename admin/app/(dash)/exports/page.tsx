import { Database } from "lucide-react";

import { Pagination } from "@/components/pagination";
import {
  Badge,
  Card,
  CardBody,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { SESSION_STATUS_LABEL, SESSION_STATUS_TONE } from "@/lib/labels";
import { formatDateTime, formatScore } from "@/lib/format";
import { listExercises, listSessions } from "@/lib/mock/admin-api";
import { BulkExportButton, ExportButton } from "./export-button";
import { ExportsFilter } from "./exports-filter";

export const metadata = { title: "좌표 내보내기" };

const SIZE = 10;

export default async function ExportsPage({
  searchParams,
}: {
  searchParams: Promise<{ exerciseId?: string; page?: string }>;
}) {
  const sp = await searchParams;
  const exerciseId = sp.exerciseId ?? "";
  const page = Math.max(1, Number(sp.page ?? 1) || 1);

  const [result, exercises] = await Promise.all([
    listSessions({
      exerciseId: exerciseId ? Number(exerciseId) : undefined,
      page,
      size: SIZE,
    }),
    listExercises(),
  ]);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">운동 좌표 내보내기</h2>
        <p className="mt-1 text-sm text-text-muted">
          keypoint_frames를 JSONL/JSON으로 내려받아 분석 모델 학습 데이터셋을 구축합니다.
        </p>
      </div>

      <Card>
        <CardBody className="flex items-start gap-3">
          <Database className="mt-0.5 size-5 text-accent" aria-hidden />
          <div className="text-sm text-text-muted">
            <p>
              종목·세션 단위로 정규화된 관절 좌표(0~1, 17개)를 내보냅니다.
              JSONL은 프레임 1건이 1줄(세션 메타 포함), JSON은 단일 세션의 전체 프레임입니다.
            </p>
            <p className="mt-1 text-xs text-text-subtle">
              ⚠️ mock 데이터 — 백엔드 연동 시 실제 keypoint_frames 스트리밍으로 대체되며 내보내기 행위가 감사 로그에 기록됩니다.
            </p>
          </div>
        </CardBody>
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <ExportsFilter exercises={exercises} exerciseId={exerciseId} />
        <BulkExportButton sessions={result.items} />
      </div>

      <Table>
        <THead>
          <TR>
            <TH>세션</TH>
            <TH>회원</TH>
            <TH>종목</TH>
            <TH>상태</TH>
            <TH>점수</TH>
            <TH>시작</TH>
            <TH className="text-right">내보내기</TH>
          </TR>
        </THead>
        <TBody>
          {result.items.map((s) => (
            <TR key={s.id}>
              <TD className="font-mono text-text-muted">{s.id}</TD>
              <TD className="font-mono text-text-muted">#{s.userId}</TD>
              <TD className="font-medium">{s.exercise.nameKo}</TD>
              <TD>
                <Badge tone={SESSION_STATUS_TONE[s.status]}>
                  {SESSION_STATUS_LABEL[s.status]}
                </Badge>
              </TD>
              <TD className="font-mono tabular-nums">{formatScore(s.score)}</TD>
              <TD className="text-text-muted">{formatDateTime(s.startedAt)}</TD>
              <TD>
                <ExportButton session={s} />
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Pagination page={result.page} size={result.size} total={result.total} />
    </div>
  );
}
