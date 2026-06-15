"use client";

import { useState, useTransition } from "react";

import { Button, Input, Segmented } from "@/components/ui";
import type { Gender } from "@/lib/api/types";

export interface ProfileFormValues {
  nickname: string;
  birthdate: string;
  gender: Gender;
  height: number | null;
  weight: number | null;
}

export interface ProfileFormProps {
  initial: {
    nickname: string;
    birthdate?: string;
    gender?: Gender;
    height?: number | null;
    weight?: number | null;
  };
  /** 서버 액션 — 성공 시 내부에서 redirect하거나 {error}를 반환한다 */
  action: (values: ProfileFormValues) => Promise<{ error?: string }>;
  submitLabel: string;
  /** 설정에서처럼 화면에 머무는 경우, 성공 시 보여줄 메시지(있으면) */
  successMessage?: string;
}

const GENDER_OPTIONS = [
  { value: "M" as const, label: "남성" },
  { value: "F" as const, label: "여성" },
  { value: "U" as const, label: "선택 안 함" },
];

/* 온보딩 기본정보(SCR-03)와 설정 신체정보(SET-02)가 공유하는 폼. Card·제목은 호출부가 감싼다. */
export function ProfileForm({
  initial,
  action,
  submitLabel,
  successMessage,
}: ProfileFormProps) {
  const [maxDate] = useState(() => new Date().toISOString().slice(0, 10));

  const [nickname, setNickname] = useState(initial.nickname);
  const [birthdate, setBirthdate] = useState(initial.birthdate ?? "");
  const [gender, setGender] = useState<Gender>(initial.gender ?? "U");
  const [height, setHeight] = useState(initial.height?.toString() ?? "");
  const [weight, setWeight] = useState(initial.weight?.toString() ?? "");

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function parseOptional(value: string): number | null | "invalid" {
    const t = value.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : "invalid";
  }

  function submit() {
    setError(null);
    setSuccess(null);

    if (nickname.trim() === "") {
      setError("닉네임을 입력해 주세요.");
      return;
    }
    if (birthdate === "") {
      setError("생년월일을 입력해 주세요.");
      return;
    }
    const h = parseOptional(height);
    const w = parseOptional(weight);
    if (h === "invalid" || w === "invalid") {
      setError("키·체중은 숫자로 입력해 주세요.");
      return;
    }

    startTransition(async () => {
      const res = await action({
        nickname: nickname.trim(),
        birthdate,
        gender,
        height: h,
        weight: w,
      });
      if (res?.error) setError(res.error);
      else if (successMessage) setSuccess(successMessage);
    });
  }

  return (
    <div className="space-y-5">
      <Input
        label="닉네임"
        value={nickname}
        maxLength={50}
        onChange={(e) => setNickname(e.target.value)}
      />
      <Input
        label="생년월일"
        type="date"
        max={maxDate}
        value={birthdate}
        onChange={(e) => setBirthdate(e.target.value)}
      />

      <div className="space-y-1.5">
        <span className="block text-sm font-medium text-text">성별</span>
        <Segmented
          aria-label="성별"
          value={gender}
          onChange={setGender}
          options={GENDER_OPTIONS}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="키 (cm)"
          type="number"
          inputMode="decimal"
          placeholder="선택"
          value={height}
          onChange={(e) => setHeight(e.target.value)}
        />
        <Input
          label="체중 (kg)"
          type="number"
          inputMode="decimal"
          placeholder="선택"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {success && <p className="text-sm text-success">{success}</p>}

      <Button
        size="lg"
        className="w-full"
        loading={pending}
        onClick={submit}
      >
        {submitLabel}
      </Button>
    </div>
  );
}
