"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupCompletePage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    if (countdown === 0) {
      router.push("/login");
      return;
    }
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md mx-4 text-center">
        {/* 성공 아이콘 */}
        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 mb-6">
          <div className="w-16 h-16 rounded-full bg-emerald-500 flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>

        {/* 메시지 */}
        <h1 className="text-2xl font-bold text-white mb-2">회원가입이 완료되었습니다!</h1>
        <p className="text-slate-400 text-sm mb-8 leading-relaxed">
          PoseFit에 오신 것을 환영합니다.<br />
          AI 자세 분석으로 더 건강한 운동을 시작해보세요.
        </p>

        {/* 카드 */}
        <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-6 shadow-2xl mb-6">
          <div className="flex items-center gap-3 justify-center text-slate-300 text-sm mb-4">
            <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI가 실시간으로 운동 자세를 분석해드립니다
          </div>
          <div className="flex items-center gap-3 justify-center text-slate-300 text-sm mb-4">
            <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            운동 기록과 점수를 한눈에 확인하세요
          </div>
          <div className="flex items-center gap-3 justify-center text-slate-300 text-sm">
            <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            얼굴 인식으로 자동 로그인도 지원 예정
          </div>
        </div>

        {/* 로그인 버튼 */}
        <button
          onClick={() => router.push("/login")}
          className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg hover:shadow-emerald-500/25 active:scale-[0.98] mb-4"
        >
          로그인하러 가기
        </button>

        {/* 자동 이동 카운트다운 */}
        <p className="text-slate-500 text-xs">
          {countdown}초 후 자동으로 로그인 화면으로 이동합니다
        </p>
      </div>
    </div>
  );
}
