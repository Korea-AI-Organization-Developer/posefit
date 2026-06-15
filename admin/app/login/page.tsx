import Link from "next/link";
import { LockKeyhole, ShieldCheck } from "lucide-react";

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

        <form className="rounded-md border border-border bg-surface p-6 shadow-xs">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium">이메일</span>
            <input
              type="email"
              placeholder="admin@posefit.dev"
              className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none transition-colors placeholder:text-text-subtle focus:border-accent focus:ring-2 focus:ring-accent-soft"
            />
          </label>

          <label className="mt-4 block">
            <span className="mb-1.5 block text-sm font-medium">비밀번호</span>
            <input
              type="password"
              placeholder="비밀번호"
              className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none transition-colors placeholder:text-text-subtle focus:border-accent focus:ring-2 focus:ring-accent-soft"
            />
          </label>

          <button
            type="button"
            className="mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent text-sm font-medium text-white hover:bg-accent-hover"
          >
            <LockKeyhole className="size-4" aria-hidden />
            로그인
          </button>
        </form>

        <div className="mt-4 text-center">
          <Link href="/" className="text-sm text-text-muted hover:text-text">
            대시보드 미리보기
          </Link>
        </div>
      </section>
    </main>
  );
}
