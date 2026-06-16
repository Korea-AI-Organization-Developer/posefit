/*
 * 저장 영상 합계·일괄삭제 목업 — docs/openapi.yaml 기준. 백엔드 미구현.
 *   getVideosSummary() → GET  /api/v1/users/me/videos:summary
 *   purgeVideos()      → POST /api/v1/users/me/videos:purge (202, 비동기)
 * API 준비 후 lib/api/videos.ts 로 교체 (시그니처 동일).
 */

export interface VideosSummary {
  count: number;
  totalBytes: number;
}

export interface PurgeAccepted {
  purgedSessionsCount: number;
  freedBytes: number;
}

const summary: VideosSummary = {
  count: 12,
  totalBytes: 260_046_848, // ≈ 248 MB
};

export async function getVideosSummary(): Promise<VideosSummary> {
  return summary;
}

/** 일괄 삭제 — 실제로는 202 후 비동기 cleanup. 목업이라 합계만 돌려준다. */
export async function purgeVideos(): Promise<PurgeAccepted> {
  return { purgedSessionsCount: summary.count, freedBytes: summary.totalBytes };
}
