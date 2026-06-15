import Image from "next/image";

import { OnboardingStepper } from "./stepper";

/*
 * 가입 퍼널 전용 레이아웃 — (app) 셸(Navbar/Footer) 밖.
 * 중앙 정렬 미니멀 + 단계 스텝퍼. 각 단계 화면(terms/profile/face)은 U4에서 채운다.
 */
export default function OnboardingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="flex min-h-full flex-col items-center px-6 py-12">
      <span className="flex items-center gap-2">
        <Image
          src="/brand/posefit-logo.svg"
          alt=""
          width={19}
          height={20}
          className="h-5 w-auto"
        />
        <span className="text-base font-semibold tracking-tight">PoseFit</span>
      </span>

      <div className="mt-10">
        <OnboardingStepper />
      </div>

      <main className="mt-10 w-full max-w-md">{children}</main>
    </div>
  );
}
