"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import FaceCapture from "../components/FaceCapture";

type Mode = "select" | "face";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("select");
  const [faceStatus, setFaceStatus] = useState<"idle" | "trying" | "success" | "fail">("idle");
  const [statusMsg, setStatusMsg] = useState("얼굴을 화면 중앙에 맞춰주세요");

  const handleAutoDetect = useCallback(async (base64: string) => {
    if (faceStatus === "trying" || faceStatus === "success") return;
    setFaceStatus("trying");
    setStatusMsg("인식 중...");

    try {
      const res = await fetch("http://localhost:8000/api/face/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: base64 }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        setFaceStatus("success");
        setStatusMsg(`${data.nickname}님, 환영합니다!`);
        setTimeout(() => router.push("/"), 1200);
      } else {
        setFaceStatus("fail");
        setStatusMsg("얼굴을 찾지 못했습니다. 다시 시도합니다...");
        setTimeout(() => setFaceStatus("idle"), 2000);
      }
    } catch {
      setFaceStatus("fail");
      setStatusMsg("연결 오류. 다시 시도합니다...");
      setTimeout(() => setFaceStatus("idle"), 2000);
    }
  }, [faceStatus, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md mx-4">
        {/* 로고 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-500 mb-4">
            <svg className="w-9 h-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">PoseFit</h1>
          <p className="mt-1 text-slate-400 text-sm">AI 운동 자세 분석 서비스</p>
        </div>

        <div className="bg-slate-800/60 backdrop-blur border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {mode === "select" && (
            <>
              <h2 className="text-xl font-semibold text-white mb-1">로그인</h2>
              <p className="text-slate-400 text-sm mb-8">방법을 선택해주세요</p>

              {/* 구글 로그인 */}
              <a
                href="http://localhost:8000/api/auth/google"
                className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-white hover:bg-gray-50 text-gray-800 font-medium rounded-xl transition-all duration-200 shadow-md hover:shadow-lg active:scale-[0.98] mb-3"
              >
                <GoogleIcon />
                Google로 로그인
              </a>

              {/* 얼굴 인식 로그인 */}
              <button
                onClick={() => setMode("face")}
                className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-slate-700/60 hover:bg-slate-700 border border-slate-600 text-slate-200 font-medium rounded-xl transition-all duration-200 active:scale-[0.98]"
              >
                <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
                </svg>
                얼굴 인식으로 로그인
              </button>

              <div className="mt-6 pt-6 border-t border-slate-700">
                <p className="text-center text-xs text-slate-500 leading-relaxed">
                  로그인 시{" "}
                  <span className="text-emerald-400 cursor-pointer hover:underline">서비스 이용약관</span>
                  {" "}및{" "}
                  <span className="text-emerald-400 cursor-pointer hover:underline">개인정보처리방침</span>에 동의하게 됩니다.
                </p>
              </div>
            </>
          )}

          {mode === "face" && (
            <>
              <div className="flex items-center gap-3 mb-4">
                <button onClick={() => setMode("select")} className="text-slate-400 hover:text-white transition-colors">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <h2 className="text-xl font-semibold text-white">얼굴 인식 로그인</h2>
              </div>

              <FaceCapture
                autoDetect
                onAutoDetect={handleAutoDetect}
                detectInterval={2500}
              />

              {/* 상태 메시지 */}
              <div className={`mt-4 flex items-center justify-center gap-2 text-sm font-medium ${
                faceStatus === "success" ? "text-emerald-400"
                : faceStatus === "fail" ? "text-red-400"
                : faceStatus === "trying" ? "text-blue-400"
                : "text-slate-400"
              }`}>
                {faceStatus === "trying" && (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                )}
                {faceStatus === "success" && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {statusMsg}
              </div>

              <button
                onClick={() => setMode("select")}
                className="mt-4 w-full py-2.5 rounded-xl border border-slate-600 text-slate-400 hover:bg-slate-700/60 transition-colors text-sm"
              >
                다른 방법으로 로그인
              </button>
            </>
          )}
        </div>

        <p className="text-center mt-6 text-slate-500 text-sm">
          처음 방문이신가요?{" "}
          <a href="/signup" className="text-emerald-400 font-medium hover:text-emerald-300 transition-colors">
            회원가입
          </a>
        </p>
      </div>
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
