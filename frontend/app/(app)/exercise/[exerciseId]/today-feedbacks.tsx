import { Badge, Card, CardBody, CardHeader, type BadgeTone } from "@/components/ui";
import { getExerciseFeedbacks } from "@/lib/api/exercises";
import { formatFeedbackTime } from "@/lib/format";
import type { FeedbackSeverity } from "@/lib/api/exercises";

// 심각도 → 배지 톤/라벨. workout-live 결과 화면과 동일한 표기로 맞춘다.
const SEVERITY: Record<FeedbackSeverity, { tone: BadgeTone; label: string }> = {
  info: { tone: "neutral", label: "정보" },
  warning: { tone: "warning", label: "주의" },
  critical: { tone: "danger", label: "위험" },
};

/*
 * 종목별 "오늘(KST)" 피드백 목록 — GET /api/v1/exercises/{id}/feedbacks.
 * 서버 컴포넌트. 운동 상세 페이지에서 오늘 누적된 피드백을 id ASC 순으로 보여준다.
 * 오늘 기록이 없으면 안내 문구만 노출한다.
 */
export async function TodayFeedbacks({ exerciseId }: { exerciseId: number }) {
  const feedbacks = await getExerciseFeedbacks(exerciseId);

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">오늘의 피드백</h2>
        <p className="mt-0.5 text-xs text-text-subtle">
          오늘(KST) 이 운동에서 받은 분석 피드백이에요
        </p>
      </CardHeader>
      {feedbacks.length === 0 ? (
        <CardBody>
          <p className="text-sm text-text-subtle">
            오늘 받은 피드백이 아직 없어요. 운동을 마치면 여기에 쌓여요.
          </p>
        </CardBody>
      ) : (
        <CardBody className="p-0">
          <ul className="divide-y divide-border">
            {feedbacks.map((f) => (
              <li key={f.id} className="flex gap-3 px-6 py-3">
                <Badge tone={SEVERITY[f.severity].tone} className="shrink-0">
                  {SEVERITY[f.severity].label}
                </Badge>
                <div className="min-w-0 flex-1">
                  <p className="text-sm">{f.content}</p>
                  <p className="mt-0.5 text-xs text-text-subtle">
                    {f.generatedBy === "llm" ? "AI 분석" : "규칙 기반"} ·{" "}
                    {formatFeedbackTime(f.createdAt)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </CardBody>
      )}
    </Card>
  );
}
