import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Card, CardBody, CardHeader } from "@/components/ui";
import { ProfileForm } from "@/components/forms/profile-form";
import { getLatestAgreement } from "@/lib/api/agreements";
import { getMe } from "@/lib/api/users";
import { getSocialAccounts } from "@/lib/mock/social-accounts";
import { getVideosSummary } from "@/lib/mock/videos";
import { saveProfileAction } from "./actions";
import { AccountSection } from "./account-section";
import { FaceSection } from "./face-section";
import { MarketingToggle } from "./marketing-toggle";
import { SocialSection } from "./social-section";
import { VideosSection } from "./videos-section";

export const metadata: Metadata = { title: "설정" };

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          {description && (
            <p className="mt-0.5 text-xs text-text-subtle">{description}</p>
          )}
        </div>
      </CardHeader>
      <CardBody>{children}</CardBody>
    </Card>
  );
}

/*
 * SCR-11 설정 (SET-01~08).
 * 인증/유저 도메인은 실제 API(@/lib/api/*, httpOnly 쿠키 BFF):
 *   getMe() · getLatestAgreement() — 프로필·신체정보·마케팅 동의 현재값
 * 소셜 연동·저장 영상은 백엔드 미구현이라 @/lib/mock/* 사용.
 */
export default async function SettingsPage() {
  const [me, agreement, social, videos] = await Promise.all([
    getMe(),
    getLatestAgreement(),
    getSocialAccounts(),
    getVideosSummary(),
  ]);

  // face_embeddings 유무는 registrationStep 으로 파생 (complete = 얼굴 등록됨)
  const faceRegistered = me.registrationStep === "complete";

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">설정</h1>
        <p className="mt-1 text-sm text-text-muted">
          프로필·인증·계정을 관리해요
        </p>
      </header>

      <div className="mt-8 space-y-6">
        {/* SET-01·02 — 프로필 + 신체정보 */}
        <Section title="프로필" description="닉네임과 신체 정보를 수정해요.">
          <div className="space-y-5">
            <div className="rounded-sm bg-surface-muted px-3 py-2">
              <p className="text-xs text-text-subtle">로그인 계정</p>
              <p className="text-sm">{me.email ?? "이메일 비공개"}</p>
            </div>
            <ProfileForm
              initial={{
                nickname: me.nickname,
                birthdate: me.detail?.birthdate,
                gender: me.detail?.gender,
                height: me.detail?.height,
                weight: me.detail?.weight,
              }}
              action={saveProfileAction}
              submitLabel="저장"
              successMessage="저장됐어요."
            />
          </div>
        </Section>

        {/* SET-03 — 마케팅 동의 */}
        <Section title="알림" description="마케팅 정보 수신 여부를 설정해요.">
          <MarketingToggle
            initialAgreed={agreement?.marketingAgreed ?? false}
          />
        </Section>

        {/* SET-04·05 — 얼굴 인증 */}
        <Section title="얼굴 인증">
          <FaceSection registered={faceRegistered} />
        </Section>

        {/* SET-06 — 연결된 소셜 계정 */}
        <Section title="연결된 계정" description="소셜 로그인 계정을 관리해요.">
          <SocialSection initial={social} />
        </Section>

        {/* SET-07 — 저장 영상 */}
        <Section title="저장 영상" description="저장한 운동 영상을 정리해요.">
          <VideosSection initial={videos} />
        </Section>

        {/* SET-08 — 계정 */}
        <Section title="계정">
          <AccountSection />
        </Section>
      </div>
    </div>
  );
}
