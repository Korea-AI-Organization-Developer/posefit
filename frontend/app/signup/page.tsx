"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import FaceCapture from "../components/FaceCapture";

type Step = "social" | "profile" | "agreement" | "face";

interface ProfileForm {
  nickname: string;
  birthdate: string;
  gender: "M" | "F" | "U" | "";
  height: string;
  weight: string;
}

interface AgreementForm {
  tos: boolean;
  privacy: boolean;
  biometric: boolean;
  marketing: boolean;
}

function SignupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tempToken = searchParams.get("temp_token") ?? "";

  const [step, setStep] = useState<Step>(tempToken ? "profile" : "social");
  const [profile, setProfile] = useState<ProfileForm>({
    nickname: "",
    birthdate: "",
    gender: "",
    height: "",
    weight: "",
  });
  const [agreements, setAgreements] = useState<AgreementForm>({
    tos: false,
    privacy: false,
    biometric: false,
    marketing: false,
  });
  const [accessToken, setAccessToken] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const requiredAgreed = agreements.tos && agreements.privacy && agreements.biometric;
  const profileValid =
    profile.nickname.trim().length >= 2 &&
    profile.birthdate !== "" &&
    profile.gender !== "";

  const steps: { key: Step; label: string }[] = [
    { key: "social", label: "소셜 연동" },
    { key: "profile", label: "기본 정보" },
    { key: "agreement", label: "약관 동의" },
    { key: "face", label: "얼굴 등록" },
  ];
  const stepIndex = steps.findIndex((s) => s.key === step);

  async function handleSignupComplete() {
    if (!requiredAgreed || submitting) return;
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/api/auth/signup/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temp_token: tempToken,
          nickname: profile.nickname.trim(),
          birthdate: profile.birthdate,
          gender: profile.gender,
          height: profile.height ? parseFloat(profile.height) : null,
          weight: profile.weight ? parseFloat(profile.weight) : null,
          tos_agreed: agreements.tos,
          privacy_agreed: agreements.privacy,
          biometric_agreed: agreements.biometric,
          marketing_agreed: agreements.marketing,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "회원가입 중 오류가 발생했습니다");
      }

      const { access_token } = await res.json();
      localStorage.setItem("access_token", access_token);
      setAccessToken(access_token);
      setStep("face");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "오류가 발생했습니다");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFaceRegister(base64: string) {
    try {
      const res = await fetch("http://localhost:8000/api/face/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ image: base64 }),
      });
      if (!res.ok) throw new Error("얼굴 등록 실패");
    } catch {
      // 얼굴 등록 실패해도 완료 페이지로 이동
    }
    router.push("/signup/complete");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md mx-4">
        {/* 로고 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-500 mb-3">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">PoseFit 회원가입</h1>
        </div>

        {/* 스텝 인디케이터 */}
        <div className="flex items-center mb-6 px-2">
          {steps.map((s, i) => (
            <div key={s.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                    i < stepIndex
                      ? "bg-emerald-500 text-white"
                      : i === stepIndex
                      ? "bg-emerald-500 text-white ring-4 ring-emerald-500/30"
                      : "bg-slate-700 text-slate-400"
                  }`}
                >
                  {i < stepIndex ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span className={`mt-1 text-xs font-medium ${i === stepIndex ? "text-emerald-400" : "text-slate-500"}`}>
                  {s.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className={`h-0.5 flex-1 mx-1 mb-4 rounded ${i < stepIndex ? "bg-emerald-500" : "bg-slate-700"}`} />
              )}
            </div>
          ))}
        </div>

        {/* 카드 */}
        <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {error && (
            <div className="mb-4 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}

          {step === "social" && <StepSocial />}
          {step === "profile" && (
            <StepProfile
              form={profile}
              onChange={setProfile}
              onNext={() => setStep("agreement")}
              onBack={() => setStep("social")}
              valid={profileValid}
              hasTempToken={!!tempToken}
            />
          )}
          {step === "agreement" && (
            <StepAgreement
              form={agreements}
              onChange={setAgreements}
              onBack={() => setStep("profile")}
              requiredAgreed={requiredAgreed}
              onComplete={handleSignupComplete}
              submitting={submitting}
            />
          )}
          {step === "face" && (
            <StepFace
              onCapture={handleFaceRegister}
              onSkip={() => router.push("/signup/complete")}
            />
          )}
        </div>

        <p className="text-center mt-6 text-slate-500 text-sm">
          이미 계정이 있으신가요?{" "}
          <a href="/login" className="text-emerald-400 font-medium hover:text-emerald-300 transition-colors">
            로그인
          </a>
        </p>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense>
      <SignupContent />
    </Suspense>
  );
}

/* ── Step 1: 소셜 연동 ── */
function StepSocial() {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-1">소셜 계정 연동</h2>
      <p className="text-slate-400 text-sm mb-8">구글 계정으로 가입을 시작합니다</p>
      <a
        href="http://localhost:8000/api/auth/google"
        className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-white hover:bg-gray-50 text-gray-800 font-medium rounded-xl transition-all duration-200 shadow-md hover:shadow-lg active:scale-[0.98]"
      >
        <GoogleIcon />
        Google로 계속하기
      </a>
      <p className="mt-6 text-center text-xs text-slate-500">구글 계정의 이름과 이메일을 가져옵니다</p>
    </div>
  );
}

/* ── Step 2: 기본 정보 ── */
function StepProfile({
  form, onChange, onNext, onBack, valid, hasTempToken,
}: {
  form: ProfileForm;
  onChange: (f: ProfileForm) => void;
  onNext: () => void;
  onBack: () => void;
  valid: boolean;
  hasTempToken: boolean;
}) {
  const set = (key: keyof ProfileForm) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onChange({ ...form, [key]: e.target.value });

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-1">기본 정보 입력</h2>
      <p className="text-slate-400 text-sm mb-6">
        {hasTempToken ? "구글 연동 완료! 추가 정보를 입력해주세요" : "운동 분석에 활용됩니다"}
      </p>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            닉네임 <span className="text-emerald-400">*</span>
          </label>
          <input type="text" value={form.nickname} onChange={set("nickname")} placeholder="2자 이상 입력" maxLength={20}
            className="w-full px-4 py-2.5 bg-slate-700/60 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            생년월일 <span className="text-emerald-400">*</span>
          </label>
          <input type="date" value={form.birthdate} onChange={set("birthdate")} max={new Date().toISOString().split("T")[0]}
            className="w-full px-4 py-2.5 bg-slate-700/60 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors text-sm [color-scheme:dark]" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            성별 <span className="text-emerald-400">*</span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[{ value: "M", label: "남성" }, { value: "F", label: "여성" }, { value: "U", label: "선택 안 함" }].map((opt) => (
              <button key={opt.value} type="button"
                onClick={() => onChange({ ...form, gender: opt.value as "M" | "F" | "U" })}
                className={`py-2.5 rounded-xl text-sm font-medium border transition-all ${form.gender === opt.value ? "bg-emerald-500 border-emerald-500 text-white" : "bg-slate-700/60 border-slate-600 text-slate-300 hover:border-slate-500"}`}>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">키 <span className="text-slate-500 font-normal text-xs">(선택, cm)</span></label>
            <input type="number" value={form.height} onChange={set("height")} placeholder="예: 170" min={50} max={250}
              className="w-full px-4 py-2.5 bg-slate-700/60 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">몸무게 <span className="text-slate-500 font-normal text-xs">(선택, kg)</span></label>
            <input type="number" value={form.weight} onChange={set("weight")} placeholder="예: 65" min={20} max={300}
              className="w-full px-4 py-2.5 bg-slate-700/60 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors text-sm" />
          </div>
        </div>
      </div>
      <div className="flex gap-3 mt-8">
        {!hasTempToken && (
          <button onClick={onBack} className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700/60 transition-colors text-sm font-medium">이전</button>
        )}
        <button onClick={onNext} disabled={!valid}
          className="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium transition-colors text-sm">
          다음
        </button>
      </div>
    </div>
  );
}

/* ── Step 3: 약관 동의 ── */
function StepAgreement({
  form, onChange, onBack, requiredAgreed, onComplete, submitting,
}: {
  form: AgreementForm;
  onChange: (f: AgreementForm) => void;
  onBack: () => void;
  requiredAgreed: boolean;
  onComplete: () => void;
  submitting: boolean;
}) {
  const allChecked = form.tos && form.privacy && form.biometric && form.marketing;
  const toggleAll = () => {
    const next = !allChecked;
    onChange({ tos: next, privacy: next, biometric: next, marketing: next });
  };
  const items = [
    { key: "tos" as keyof AgreementForm, label: "서비스 이용약관 동의", required: true },
    { key: "privacy" as keyof AgreementForm, label: "개인정보 수집·이용 동의", required: true },
    { key: "biometric" as keyof AgreementForm, label: "바이오정보(얼굴) 처리 동의", required: true, desc: "자세 분석 및 얼굴 인식 기능에 활용됩니다" },
    { key: "marketing" as keyof AgreementForm, label: "마케팅 수신 동의", required: false, desc: "운동 팁, 업데이트 등 유용한 소식을 받습니다" },
  ];

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-1">약관 동의</h2>
      <p className="text-slate-400 text-sm mb-6">서비스 이용을 위해 동의가 필요합니다</p>
      <button type="button" onClick={toggleAll}
        className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl border transition-all mb-4 ${allChecked ? "bg-emerald-500/10 border-emerald-500/50" : "bg-slate-700/40 border-slate-600"}`}>
        <Checkbox checked={allChecked} />
        <span className="text-white font-semibold text-sm">전체 동의</span>
      </button>
      <div className="space-y-2">
        {items.map((item) => (
          <button key={item.key} type="button" onClick={() => onChange({ ...form, [item.key]: !form[item.key] })}
            className="flex items-start gap-3 w-full px-4 py-3 rounded-xl hover:bg-slate-700/40 transition-colors text-left">
            <Checkbox checked={form[item.key]} className="mt-0.5" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-slate-200 text-sm">{item.label}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${item.required ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-600 text-slate-400"}`}>
                  {item.required ? "필수" : "선택"}
                </span>
              </div>
              {item.desc && <p className="text-slate-500 text-xs mt-0.5">{item.desc}</p>}
            </div>
          </button>
        ))}
      </div>
      <div className="flex gap-3 mt-8">
        <button onClick={onBack} className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-300 hover:bg-slate-700/60 transition-colors text-sm font-medium">이전</button>
        <button disabled={!requiredAgreed || submitting} onClick={onComplete}
          className="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium transition-colors text-sm flex items-center justify-center gap-2">
          {submitting && <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" /></svg>}
          {submitting ? "처리 중..." : "다음"}
        </button>
      </div>
    </div>
  );
}

/* ── Step 4: 얼굴 등록 ── */
function StepFace({ onCapture, onSkip }: { onCapture: (base64: string) => void; onSkip: () => void }) {
  const [captured, setCaptured] = useState(false);
  const [capturedImage, setCapturedImage] = useState("");
  const [uploading, setUploading] = useState(false);

  async function handleConfirm() {
    setUploading(true);
    await onCapture(capturedImage);
    setUploading(false);
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-1">얼굴 등록</h2>
      <p className="text-slate-400 text-sm mb-4">
        다음 로그인부터 얼굴 인식으로 자동 로그인됩니다
      </p>

      <FaceCapture
        label="얼굴 촬영"
        onCapture={(base64) => {
          setCapturedImage(base64);
          setCaptured(true);
        }}
      />

      <div className="flex gap-3 mt-6">
        <button onClick={onSkip} className="flex-1 py-2.5 rounded-xl border border-slate-600 text-slate-400 hover:bg-slate-700/60 transition-colors text-sm">
          나중에 등록
        </button>
        <button
          disabled={!captured || uploading}
          onClick={handleConfirm}
          className="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium transition-colors text-sm flex items-center justify-center gap-2"
        >
          {uploading && <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" /></svg>}
          {uploading ? "등록 중..." : "등록 완료"}
        </button>
      </div>
    </div>
  );
}

/* ── 공통 컴포넌트 ── */
function Checkbox({ checked, className = "" }: { checked: boolean; className?: string }) {
  return (
    <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 border transition-colors ${checked ? "bg-emerald-500 border-emerald-500" : "bg-transparent border-slate-500"} ${className}`}>
      {checked && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}
