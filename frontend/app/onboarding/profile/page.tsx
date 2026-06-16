import { Card, CardBody } from "@/components/ui";
import { ProfileForm } from "@/components/forms/profile-form";
import { requireStep } from "@/lib/auth/guard";
import { saveOnboardingProfileAction } from "./actions";

/* SCR-03 기본 정보 — 가입 2단계. detail_required 단계에서만 머문다. */
export default async function ProfilePage() {
  const me = await requireStep("detail_required");

  return (
    <Card>
      <CardBody className="space-y-6">
        <div className="space-y-1.5">
          <h1 className="text-lg font-semibold">기본 정보를 입력해 주세요</h1>
          <p className="text-sm text-text-muted">
            운동 분석에 사용할 정보예요. 키·체중은 나중에 입력해도 돼요.
          </p>
        </div>
        <ProfileForm
          initial={{
            nickname: me.nickname,
            birthdate: me.detail?.birthdate,
            gender: me.detail?.gender,
            height: me.detail?.height,
            weight: me.detail?.weight,
          }}
          action={saveOnboardingProfileAction}
          submitLabel="다음"
        />
      </CardBody>
    </Card>
  );
}
