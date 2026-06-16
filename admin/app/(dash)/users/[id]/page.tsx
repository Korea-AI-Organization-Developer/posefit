import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { GENDER_LABEL, USER_STATUS_LABEL, USER_STATUS_TONE } from "@/lib/labels";
import { formatDate, formatDateTime, formatNumber } from "@/lib/format";
import { getUserDetail } from "@/lib/mock/admin-api";
import { StatusControl } from "./status-control";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-2.5 text-sm">
      <span className="text-text-muted">{label}</span>
      <span className="text-right font-medium text-text">{value}</span>
    </div>
  );
}

export default async function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = await getUserDetail(Number(id));
  if (!user) notFound();

  return (
    <div className="space-y-5">
      <Link
        href="/users"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft className="size-4" aria-hidden />
        회원 목록
      </Link>

      <div className="flex items-center gap-3">
        <h2 className="text-xl font-semibold tracking-tight">{user.nickname}</h2>
        <Badge tone={USER_STATUS_TONE[user.status]}>
          {USER_STATUS_LABEL[user.status]}
        </Badge>
        <span className="font-mono text-sm text-text-subtle">#{user.id}</span>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">프로필 · 활동</h3>
          </CardHeader>
          <CardBody className="divide-y divide-border py-0">
            <Field label="이메일" value={user.email ?? "-"} />
            <Field label="가입일" value={formatDateTime(user.createdAt)} />
            <Field
              label="생년월일"
              value={user.birthdate ? formatDate(user.birthdate) : "-"}
            />
            <Field
              label="성별"
              value={user.gender ? (GENDER_LABEL[user.gender] ?? user.gender) : "-"}
            />
            <Field
              label="신체"
              value={
                user.height || user.weight
                  ? `${user.height ?? "-"}cm · ${user.weight ?? "-"}kg`
                  : "-"
              }
            />
            <Field
              label="얼굴 등록"
              value={
                user.faceRegistered ? (
                  <Badge tone="success">등록됨</Badge>
                ) : (
                  <Badge tone="neutral">미등록</Badge>
                )
              }
            />
            <Field
              label="마케팅 수신"
              value={user.marketingAgreed == null ? "-" : user.marketingAgreed ? "동의" : "거부"}
            />
            <Field
              label="누적 세션"
              value={`${formatNumber(user.sessionCount)}회`}
            />
            {user.withdrawnAt && (
              <Field label="탈퇴일" value={formatDateTime(user.withdrawnAt)} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-sm font-semibold">상태 관리</h3>
          </CardHeader>
          <CardBody>
            <StatusControl userId={user.id} initial={user.status} />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
