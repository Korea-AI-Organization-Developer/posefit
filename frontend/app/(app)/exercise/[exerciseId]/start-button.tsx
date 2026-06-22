"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { Play } from "lucide-react";

import { Button } from "@/components/ui";

/*
 * SCR-07 "운동 시작하기" — 실행 화면으로 이동.
 * 세션은 미리 만들지 않는다. 각 세트의 STOP(:stop)이 그때 세션을 생성·채점한다.
 */
export function StartButton({ exerciseId }: { exerciseId: number }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function go() {
    startTransition(() => {
      router.push(`/exercise/${exerciseId}/session`);
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
