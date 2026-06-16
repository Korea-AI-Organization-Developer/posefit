/*
 * mock 키포인트 프레임 생성 — 내보내기 다운로드 데모용.
 * 백엔드 연동 시 GET /admin/exports/keypoints 스트리밍 응답으로 대체한다.
 * 출력 포맷은 docs/openapi.yaml 의 KeypointExport(JSONL 1줄=1프레임)와 동일.
 */

import type { AdminSessionListItem } from "@/lib/api/types";

const KEYPOINT_COUNT = 17; // ViTPose 관절 수

function frameKeypoints(frameIndex: number): number[][] {
  // 결정론적 합성 좌표(0~1) — 데모용
  return Array.from({ length: KEYPOINT_COUNT }, (_, k) => {
    const x = 0.5 + 0.2 * Math.sin((frameIndex + k) * 0.3);
    const y = 0.1 + (k / KEYPOINT_COUNT) * 0.8 + 0.02 * Math.cos(frameIndex * 0.4);
    return [Math.round(x * 1000) / 1000, Math.round(y * 1000) / 1000];
  });
}

export interface FrameRecord {
  sessionId: number;
  userId: number;
  exerciseId: number;
  exerciseNameKo: string;
  status: string;
  startedAt: string;
  score: number | null;
  frameIndex: number;
  timestampMs: number;
  keypoints: number[][];
  bbox: number[] | null;
}

export function generateFrames(
  session: AdminSessionListItem,
  count = 30,
): FrameRecord[] {
  return Array.from({ length: count }, (_, i) => ({
    sessionId: session.id,
    userId: session.userId,
    exerciseId: session.exercise.id,
    exerciseNameKo: session.exercise.nameKo,
    status: session.status,
    startedAt: session.startedAt,
    score: session.score,
    frameIndex: i,
    timestampMs: i * 33,
    keypoints: frameKeypoints(i),
    bbox: [0.3, 0.1, 0.4, 0.85],
  }));
}

export function toJsonl(records: FrameRecord[]): string {
  return records.map((r) => JSON.stringify(r)).join("\n");
}

export function toSessionJson(
  session: AdminSessionListItem,
  records: FrameRecord[],
): string {
  return JSON.stringify(
    {
      session: {
        sessionId: session.id,
        userId: session.userId,
        exerciseId: session.exercise.id,
        exerciseNameKo: session.exercise.nameKo,
        status: session.status,
        startedAt: session.startedAt,
        score: session.score,
      },
      frames: records.map((r) => ({
        frameIndex: r.frameIndex,
        timestampMs: r.timestampMs,
        keypoints: r.keypoints,
        bbox: r.bbox,
      })),
    },
    null,
    2,
  );
}
