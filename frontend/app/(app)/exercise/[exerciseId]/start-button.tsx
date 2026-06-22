"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { Play } from "lucide-react";

import { Button } from "@/components/ui";
import { createSession } from "@/lib/api/workout-session";

/* SCR-07 "운동 시작하기" — createSession(POST /workout-sessions) 후 실행 화면으로 */
export function StartButton({ exerciseId }: { exerciseId: number }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function go() {
    startTransition(async () => {
      const session = await createSession(exerciseId);
      router.push(`/exercise/${exerciseId}/session?s=${session.id}`);
    });
  }

  return (
    <Button
      size="lg"
      className="w-full"
      leftIcon={<Play />}
      loading={pending}
      onClick={go}
    >
      운동 시작하기
    </Button>
  );
}
