/*
 * 본인 프로필 목업 — docs/openapi.yaml User 스키마의 일부 필드만 사용.
 *   getMe() → GET /api/v1/users/me
 * API 준비 후 lib/api/user.ts 로 교체 (시그니처 동일).
 */

export interface Me {
  id: number;
  nickname: string;
  /** 구글 프로필 사진 URL — social_accounts.provider_avatar_url 에서 derived. 없으면 null */
  avatarUrl: string | null;
}

const me: Me = {
  id: 1,
  nickname: "홍길동",
  // 구글 사진 미연동 목업 → null 이면 navbar 가 이니셜 아바타로 대체
  avatarUrl: null,
};

export async function getMe(): Promise<Me> {
  return me;
}
