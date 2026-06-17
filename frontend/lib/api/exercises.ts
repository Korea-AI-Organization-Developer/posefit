// apiFetch: 실제 네트워크 요청을 보내는 공통 도구(server.ts). 토큰을 붙이고, JSON으로 변환해 돌려준다.
import { apiFetch } from "./server";
// import type: "타입만" 가져온다는 표시(실행 코드 아님). 응답 모양 타입을 types.ts에서 빌려온다.
import type { ExerciseListResponse, ExerciseDetailResponse } from "./types";

// types.ts에 정의된 운동 관련 타입들을 이 파일을 통해 다시 내보낸다(re-export).
// 덕분에 화면 코드는 "@/lib/api/exercises" 한 곳에서 함수와 타입을 같이 가져올 수 있다.
export type { ExerciseType, ExerciseSummary, ExerciseListResponse, ExerciseDetailResponse } from "./types";

// getExercises: 운동 목록을 백엔드에서 가져오는 함수.
//   async  = 비동기 함수(네트워크 응답을 기다려야 하므로).
//   Promise<ExerciseListResponse> = "나중에 ExerciseListResponse 모양의 값을 돌려준다"는 반환 타입.
export async function getExercises(): Promise<ExerciseListResponse> {
  // GET /api/v1/exercises?activeOnly=true 를 호출. (API_BASE에 /api/v1 이 들어있어 "/exercises"만 적는다.)
  // activeOnly=true → 노출 중인 운동만 받는다.
  return apiFetch("/exercises?activeOnly=true");
}

export async function getExerciseDetail(id: number): Promise<ExerciseDetailResponse> {
  return apiFetch(`/exercises/${id}`);
}