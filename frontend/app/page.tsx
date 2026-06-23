import Image from "next/image";
import { Camera, Dumbbell, Gauge, PersonStanding } from "lucide-react";

import { Badge } from "@/components/ui";
import { GoogleLoginButton } from "./google-login-button";

/* 콜백 실패 시 /?error=... 로 돌아온다 */
const ERROR_MESSAGES: Record<string, string> = {
  state: "로그인 요청이 만료되었어요. 다시 시도해 주세요.",
  login: "구글 로그인에 실패했어요. 다시 시도해 주세요.",
  server: "일시적인 오류가 발생했어요. 잠시 후 다시 시도해 주세요.",
};

const STEPS = [
  {
    icon: Dumbbell,
    title: "운동 선택",
    desc: "런지·플랭크·푸쉬업 등 원하는 운동을 고르고 정답 영상을 먼저 확인해요.",
  },
  {
    icon: Camera,
    title: "웹캠 앞에서 따라하기",
    desc: "카메라 앞에서 운동하면 관절 키포인트를 추적해요. 별도 장비는 필요 없어요.",
  },
  {
    icon: Gauge,
    title: "점수와 피드백",
    desc: "정답 자세와 비교해 점수를 매기고, 어디를 어떻게 고치면 되는지 짚어줘요.",
  },
];

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  const message = error ? (ERROR_MESSAGES[error] ?? ERROR_MESSAGES.server) : null;

  return (
    <div className="flex min-h-full flex-col">
      {/* ── Nav ── */}
      <header className="sticky top-0 z-20 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-6">
          <span className="flex items-center gap-2">
            <Image
              src="/brand/posefit-logo.svg"
              alt=""
              width={19}
              height={20}
              className="h-5 w-auto"
            />
            <span className="text-base font-semibold tracking-tight">
              PoseFit
            </span>
          </span>
          <GoogleLoginButton size="sm" hint={false} />
        </div>
      </header>

      <main className="flex-1">
        {/* ── Hero ── */}
        <section className="mx-auto w-full max-w-2xl px-6 pt-20 pb-14 text-center sm:pt-28">
          <p className="text-sm font-medium text-accent">AI 운동 자세 분석</p>
          <h1 className="mt-4 text-4xl font-semibold leading-[1.12] tracking-tight sm:text-5xl">
            웹캠 앞에서 운동하면,
            <br />
            자세를 점수로 알려드려요.
          </h1>
          <p className="mx-auto mt-5 max-w-md text-base text-text-muted">
            정답 영상과 비교해 관절 움직임을 분석하고, 어디를 어떻게 고치면 되는지
            짚어드려요. 별도 장비 없이 카메라 하나면 충분해요.
          </p>

          {message && (
            <p className="mx-auto mt-8 w-full max-w-sm rounded-sm border border-border bg-danger-soft px-4 py-2.5 text-sm text-danger">
              {message}
            </p>
          )}

          <div className="mt-9 flex flex-col items-center">
            <GoogleLoginButton />
            <p className="mt-4 text-xs text-text-subtle">
              가입 시 서비스 약관과 개인정보 처리방침에 동의하게 됩니다.
            </p>
          </div>
        </section>

        {/* ── Product preview ── */}
        <section className="mx-auto w-full max-w-4xl px-6 pb-24">
          <ProductPreview />
        </section>

        {/* ── How it works ── */}
        <section className="mx-auto w-full max-w-5xl px-6 pb-24">
          <div className="text-center">
            <h2 className="text-2xl font-semibold tracking-tight">
              어떻게 동작하나요
            </h2>
            <p className="mt-2 text-sm text-text-muted">세 단계면 충분해요.</p>
          </div>
          <ol className="mt-10 grid gap-4 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <li
                key={step.title}
                className="rounded-md border border-border bg-surface p-6 shadow-xs"
              >
                <span className="inline-flex size-10 items-center justify-center rounded-md border border-border text-accent [&_svg]:size-5">
                  <step.icon aria-hidden />
                </span>
                <p className="mt-4 font-mono text-xs text-text-subtle">
                  0{i + 1}
                </p>
                <h3 className="mt-1 text-base font-semibold">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-text-muted">
                  {step.desc}
                </p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-border">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-6 py-8 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-2">
            <Image
              src="/brand/posefit-logo.svg"
              alt=""
              width={19}
              height={20}
              className="h-4 w-auto"
            />
            <span className="text-sm font-medium">PoseFit</span>
          </span>
          <p className="text-xs text-text-subtle">
            © 2026 PoseFit — AI 운동 자세 분석
          </p>
        </div>
      </footer>
    </div>
  );
}

/* 제품 한눈에 — 실제 UI 토큰으로 그린 결과 화면 미리보기(정적) */
function ProductPreview() {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface shadow-sm">
      <div className="grid sm:grid-cols-[1.5fr_1fr]">
        {/* 카메라/추적 패널 */}
        <div className="relative aspect-[4/3] border-b border-border bg-surface-muted sm:border-r sm:border-b-0">
          <div className="absolute inset-0 flex items-center justify-center text-text-subtle/30 [&_svg]:size-28">
            <PersonStanding aria-hidden />
          </div>
          <div className="absolute inset-[12%] rounded-md border-2 border-dashed border-accent/60" />
          <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-sm bg-black/70 px-2 py-1 font-mono text-[10px] text-white">
            <span className="size-1.5 rounded-full bg-accent" />
            분석 · 17/17
          </div>
        </div>

        {/* 결과 패널 */}
        <div className="flex flex-col justify-center gap-5 p-6">
          <div>
            <p className="font-mono text-xs text-text-subtle">SCORE</p>
            <p className="mt-1 font-mono text-4xl font-semibold tabular-nums">
              92
              <span className="ml-0.5 text-lg font-normal text-text-subtle">
                /100
              </span>
            </p>
          </div>
          <ul className="space-y-2.5">
            <li className="flex items-start gap-2 text-sm">
              <Badge tone="neutral" className="mt-0.5 shrink-0">
                정보
              </Badge>
              <span className="text-text-muted">자세가 대체로 안정적이에요.</span>
            </li>
            <li className="flex items-start gap-2 text-sm">
              <Badge tone="warning" className="mt-0.5 shrink-0">
                주의
              </Badge>
              <span className="text-text-muted">
                앞 무릎이 발끝을 살짝 넘었어요.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
