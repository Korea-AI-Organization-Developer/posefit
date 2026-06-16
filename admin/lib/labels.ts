/* enum → 한국어 라벨·뱃지 톤 매핑 (화면 표시 전용) */

import type { BadgeTone } from "@/components/ui";
import type {
  ExerciseType,
  LlmProvider,
  SessionStatus,
  UserStatus,
} from "@/lib/api/types";

export const USER_STATUS_LABEL: Record<UserStatus, string> = {
  active: "활성",
  suspended: "정지",
  withdrawn: "탈퇴",
};
export const USER_STATUS_TONE: Record<UserStatus, BadgeTone> = {
  active: "success",
  suspended: "warning",
  withdrawn: "neutral",
};

export const SESSION_STATUS_LABEL: Record<SessionStatus, string> = {
  in_progress: "진행중",
  completed: "완료",
  aborted: "중단",
};
export const SESSION_STATUS_TONE: Record<SessionStatus, BadgeTone> = {
  in_progress: "accent",
  completed: "success",
  aborted: "neutral",
};

export const EXERCISE_TYPE_LABEL: Record<ExerciseType, string> = {
  static: "정적",
  dynamic: "동적",
};

export const PROVIDER_LABEL: Record<LlmProvider, string> = {
  google: "Google",
  openai: "OpenAI",
  anthropic: "Anthropic",
};

export const GENDER_LABEL: Record<string, string> = {
  M: "남성",
  F: "여성",
  U: "선택 안 함",
};

export const AUDIT_ACTION_LABEL: Record<string, string> = {
  update_user_status: "회원 상태 변경",
  create_exercise: "운동 종목 등록",
  update_exercise: "운동 종목 수정",
  create_llm_model: "LLM 모델 등록",
  update_llm_model: "LLM 모델 수정",
  activate_llm: "활성 LLM 교체",
  export_keypoints: "좌표 내보내기",
};

export function auditActionLabel(action: string): string {
  return AUDIT_ACTION_LABEL[action] ?? action;
}
