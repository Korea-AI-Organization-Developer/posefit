"use client";

import { useState, useTransition } from "react";
import {
  Button,
  Card,
  CardBody,
  Checkbox,
  Dialog,
} from "@/components/ui";
import { submitAgreementsAction } from "./actions";

type Key = "tos" | "privacy" | "marketing";

interface Item {
  key: Key;
  label: string;
  required: boolean;
  doc: string;
}

const ITEMS: Item[] = [
  {
    key: "tos",
    label: "서비스 이용약관",
    required: true,
    doc: "제1조 (목적) 본 약관은 PoseFit이 제공하는 운동 자세 분석 서비스의 이용 조건 및 절차, 회사와 회원의 권리·의무를 규정함을 목적으로 합니다. (이하 더미 텍스트)",
  },
  {
    key: "privacy",
    label: "개인정보 수집·이용",
    required: true,
    doc: "회사는 회원 가입, 서비스 제공, 운동 기록 분석을 위해 닉네임·생년월일·신체정보 등을 수집·이용합니다. 보관 기간 및 파기 절차는 개인정보 처리방침을 따릅니다. (이하 더미 텍스트)",
  },
  {
    key: "marketing",
    label: "마케팅 정보 수신",
    required: false,
    doc: "신규 기능·이벤트 등 마케팅 정보를 이메일로 받아보는 데 동의합니다. 선택 항목이며 동의하지 않아도 서비스 이용에 제한이 없습니다. (이하 더미 텍스트)",
  },
];

const REQUIRED_KEYS: Key[] = ["tos", "privacy"];

export function TermsForm() {
  const [checked, setChecked] = useState<Record<Key, boolean>>({
    tos: false,
    privacy: false,
    marketing: false,
  });
  const [openDoc, setOpenDoc] = useState<Item | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const values = Object.values(checked);
  const allChecked = values.every(Boolean);
  const someChecked = values.some(Boolean);
  const requiredMet = REQUIRED_KEYS.every((k) => checked[k]);

  function toggleAll(next: boolean) {
    setChecked({ tos: next, privacy: next, marketing: next });
  }

  function submit() {
    setError(null);
    startTransition(async () => {
      const res = await submitAgreementsAction({
        tosAgreed: checked.tos,
        privacyAgreed: checked.privacy,
        marketingAgreed: checked.marketing,
      });
      if (res?.error) setError(res.error);
    });
  }

  return (
    <Card>
      <CardBody className="space-y-6">
        <div className="space-y-1.5">
          <h1 className="text-lg font-semibold">약관에 동의해 주세요</h1>
          <p className="text-sm text-text-muted">
            서비스 이용을 위해 아래 약관 동의가 필요해요.
          </p>
        </div>

        <Checkbox
          label="약관 전체 동의"
          className="font-medium"
          checked={allChecked}
          indeterminate={someChecked && !allChecked}
          onChange={(e) => toggleAll(e.target.checked)}
        />

        <div className="space-y-3 border-t border-border pt-5">
          {ITEMS.map((item) => (
            <div key={item.key} className="flex items-center justify-between gap-3">
              <Checkbox
                label={`${item.required ? "(필수)" : "(선택)"} ${item.label}`}
                checked={checked[item.key]}
                onChange={(e) =>
                  setChecked((prev) => ({ ...prev, [item.key]: e.target.checked }))
                }
              />
              <button
                type="button"
                onClick={() => setOpenDoc(item)}
                className="shrink-0 text-sm text-text-muted underline-offset-4 hover:text-text hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                보기
              </button>
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <Button
          size="lg"
          className="w-full"
          disabled={!requiredMet}
          loading={pending}
          onClick={submit}
        >
          다음
        </Button>
      </CardBody>

      <Dialog
        open={openDoc !== null}
        onClose={() => setOpenDoc(null)}
        title={openDoc?.label}
        footer={
          <Button variant="ghost" onClick={() => setOpenDoc(null)}>
            닫기
          </Button>
        }
      >
        <p className="text-sm leading-relaxed text-text-muted">{openDoc?.doc}</p>
      </Dialog>
    </Card>
  );
}
