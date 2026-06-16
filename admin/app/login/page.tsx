import { ShieldCheck } from "lucide-react";

import { LoginForm } from "./login-form";

export const metadata = { title: "로그인" };

export default function AdminLoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="mx-auto flex size-12 items-center justify-center rounded-md bg-accent text-white">
            <ShieldCheck className="size-6" aria-hidden />
          </span>
          <h1 className="mt-4 text-xl font-semibold tracking-tight">
            PoseFit Admin
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            관리자 전용 이메일 계정으로 로그인합니다
          </p>
        </div>

        <LoginForm />
      </section>
    </main>
  );
}
