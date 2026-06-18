import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api/server";
import type { FaceGateMode } from "@/lib/api/types";
import { FaceGateClient } from "./face-gate-client";

interface FaceGateStatusResponse {
  mode: FaceGateMode;
}

export default async function FaceGatePage({
  searchParams,
}: {
  searchParams: Promise<{ reregister?: string; verify?: string }>;
}) {
  const cookieStore = await cookies();
  const token = cookieStore.get("accessToken")?.value;

  if (!token) {
    redirect("/");
  }

  const params = await searchParams;
  const isReregister = params.reregister === "1";
  const isVerify     = params.verify      === "1";

  // DB 조회 — 얼굴 등록 여부에 따라 초기 모드 결정
  let dbMode: FaceGateMode = "registration";
  try {
    const { mode } = await apiFetch<FaceGateStatusResponse>(
      "/workout/face-gate/status",
    );
    dbMode = mode;
  } catch {
    // API 실패 시 등록 모드로 기본값 유지
  }

  // 얼굴이 이미 등록돼 있고 특별 요청이 아니면 바로 운동 화면으로
  if (dbMode === "verification" && !isReregister && !isVerify) {
    redirect("/workout");
  }

  // 재등록 요청이면 강제로 등록 모드 + 완료 후 설정 복귀
  const clientMode: FaceGateMode = isReregister ? "registration" : dbMode;
  const returnTo = isReregister ? "/settings" : "/workout";

  return (
    <FaceGateClient
      token={token}
      initialMode={clientMode}
      returnTo={returnTo}
      reregister={isReregister}
    />
  );
}
