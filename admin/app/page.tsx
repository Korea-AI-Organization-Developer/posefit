import Link from "next/link";
import type { ReactNode } from "react";
import {
  Activity,
  BarChart3,
  Brain,
  Database,
  Dumbbell,
  FileDown,
  ShieldCheck,
  Users,
} from "lucide-react";

import { formatDateTime, formatNumber, formatScore } from "@/lib/format";

const navItems = [
  { label: "대시보드", icon: BarChart3 },
  { label: "회원", icon: Users },
  { label: "운동", icon: Dumbbell },
  { label: "LLM", icon: Brain },
  { label: "내보내기", icon: FileDown },
  { label: "감사 로그", icon: ShieldCheck },
];

const overview = [
  { label: "전체 회원", value: 1284, delta: "+42 이번 주" },
  { label: "활성 회원", value: 1038, delta: "80.8%" },
  { label: "정지 회원", value: 7, delta: "관리 확인 필요" },
  { label: "누적 세션", value: 9342, delta: "평균 86점" },
];

const users = [
  {
    id: 50231,
    nickname: "홍길동",
    email: "hong@example.com",
    status: "active",
    sessions: 23,
    score: 88.5,
    joinedAt: "2026-06-10T09:12:00+09:00",
  },
  {
    id: 50204,
    nickname: "김포즈",
    email: "pose@example.com",
    status: "suspended",
    sessions: 6,
    score: 71.2,
    joinedAt: "2026-06-08T18:30:00+09:00",
  },
  {
    id: 50190,
    nickname: "이운동",
    email: "fit@example.com",
    status: "active",
    sessions: 15,
    score: 91.1,
    joinedAt: "2026-06-04T08:40:00+09:00",
  },
];

const exercises = [
  { name: "런지", type: "dynamic", active: true, video: "등록됨" },
  { name: "플랭크", type: "static", active: true, video: "등록됨" },
  { name: "푸쉬업", type: "dynamic", active: true, video: "미등록" },
  { name: "오버헤드프레스", type: "dynamic", active: false, video: "등록됨" },
];

const auditLogs = [
  {
    action: "update_user_status",
    target: "user:50204",
    admin: "admin@posefit.dev",
    at: "2026-06-15T10:40:00+09:00",
  },
  {
    action: "activate_llm",
    target: "llm:gpt-5-mini",
    admin: "ops@posefit.dev",
    at: "2026-06-15T09:25:00+09:00",
  },
  {
    action: "export_keypoints",
    target: "exercise:1",
    admin: "research@posefit.dev",
    at: "2026-06-14T20:11:00+09:00",
  },
];

const statusLabel: Record<string, string> = {
  active: "활성",
  suspended: "정지",
  withdrawn: "탈퇴",
};

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-bg">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-border bg-surface lg:block">
        <div className="flex h-14 items-center gap-2 border-b border-border px-5">
          <span className="flex size-8 items-center justify-center rounded-md bg-accent text-sm font-semibold text-white">
            P
          </span>
          <div>
            <p className="text-sm font-semibold">PoseFit Admin</p>
            <p className="text-xs text-text-subtle">운영 콘솔</p>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4" aria-label="관리자 메뉴">
          {navItems.map((item, index) => (
            <a
              key={item.label}
              href="#"
              className={`flex h-10 items-center gap-3 rounded-sm px-3 text-sm ${
                index === 0
                  ? "bg-accent-muted text-accent"
                  : "text-text-muted hover:bg-surface-muted hover:text-text"
              }`}
            >
              <item.icon className="size-4" aria-hidden />
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
      <div className="lg:pl-60">
        <header className="sticky top-0 z-10 border-b border-border bg-surface">
          <div className="flex h-14 items-center justify-between px-6">
            <div>
              <p className="text-sm font-semibold">운영 대시보드</p>
              <p className="text-xs text-text-subtle">
                회원, 운동, LLM, 내보내기 상태를 관리합니다
              </p>
            </div>
            <Link
              href="/login"
              className="rounded-sm border border-border px-3 py-1.5 text-sm text-text-muted hover:bg-surface-muted hover:text-text"
            >
              로그인 화면
            </Link>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}

function Panel({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: string;
}) {
  return (
    <section className="rounded-md border border-border bg-surface shadow-xs">
      <div className="flex min-h-12 items-center justify-between border-b border-border px-5 py-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {action && <span className="text-xs text-text-subtle">{action}</span>}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export default function AdminDashboardPage() {
  return (
    <Shell>
      <main className="mx-auto w-full max-w-7xl px-6 py-6">
        <div className="grid gap-4 md:grid-cols-4">
          {overview.map((item) => (
            <section
              key={item.label}
              className="rounded-md border border-border bg-surface p-5 shadow-xs"
            >
              <p className="text-sm text-text-muted">{item.label}</p>
              <p className="mt-2 font-mono text-3xl font-semibold tabular-nums">
                {formatNumber(item.value)}
              </p>
              <p className="mt-1 text-xs text-text-subtle">{item.delta}</p>
            </section>
          ))}
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_1fr]">
          <Panel title="회원 관리" action="검색·상태 필터·페이지네이션">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="text-xs text-text-subtle">
                  <tr className="border-b border-border">
                    <th className="pb-3 font-medium">회원</th>
                    <th className="pb-3 font-medium">상태</th>
                    <th className="pb-3 font-medium">세션</th>
                    <th className="pb-3 font-medium">평균 점수</th>
                    <th className="pb-3 font-medium">가입일</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="py-3">
                        <p className="font-medium">{user.nickname}</p>
                        <p className="text-xs text-text-subtle">{user.email}</p>
                      </td>
                      <td className="py-3">
                        <span
                          className={`rounded-sm px-2 py-0.5 text-xs font-medium ${
                            user.status === "suspended"
                              ? "bg-warning-soft text-warning"
                              : "bg-success-soft text-success"
                          }`}
                        >
                          {statusLabel[user.status]}
                        </span>
                      </td>
                      <td className="py-3 font-mono tabular-nums">
                        {formatNumber(user.sessions)}
                      </td>
                      <td className="py-3 font-mono tabular-nums">
                        {formatScore(user.score)}
                      </td>
                      <td className="py-3 text-text-muted">
                        {formatDateTime(user.joinedAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="RAG LLM 모델" action="활성 모델 1개 유지">
            <div className="rounded-sm border border-border bg-surface-muted p-4">
              <div className="flex items-center gap-3">
                <Brain className="size-5 text-accent" aria-hidden />
                <div>
                  <p className="text-sm font-medium">gemini-3.5-flash</p>
                  <p className="text-xs text-text-subtle">
                    활성 · temperature 0.4 · 운영 반영 즉시
                  </p>
                </div>
              </div>
            </div>
            <button className="mt-4 h-10 w-full rounded-md bg-accent text-sm font-medium text-white hover:bg-accent-hover">
              모델 교체
            </button>
          </Panel>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-3">
          <Panel title="운동 종목" action="노출·정답 영상 관리">
            <ul className="space-y-3">
              {exercises.map((exercise) => (
                <li
                  key={exercise.name}
                  className="flex items-center justify-between gap-3"
                >
                  <div>
                    <p className="text-sm font-medium">{exercise.name}</p>
                    <p className="text-xs text-text-subtle">
                      {exercise.type} · 정답 영상 {exercise.video}
                    </p>
                  </div>
                  <span
                    className={`rounded-sm px-2 py-0.5 text-xs font-medium ${
                      exercise.active
                        ? "bg-success-soft text-success"
                        : "bg-surface-muted text-text-muted"
                    }`}
                  >
                    {exercise.active ? "노출" : "숨김"}
                  </span>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="좌표 데이터 내보내기" action="JSONL/JSON">
            <div className="flex items-start gap-3">
              <Database className="mt-0.5 size-5 text-accent" aria-hidden />
              <div>
                <p className="text-sm font-medium">최근 30일 completed 세션</p>
                <p className="mt-1 text-sm text-text-muted">
                  keypoint_frames를 학습 데이터셋으로 스트리밍 다운로드합니다.
                </p>
              </div>
            </div>
            <button className="mt-5 h-10 w-full rounded-md border border-border text-sm font-medium hover:bg-surface-muted">
              내보내기 생성
            </button>
          </Panel>

          <Panel title="감사 로그" action="append-only">
            <ul className="space-y-3">
              {auditLogs.map((log) => (
                <li key={`${log.action}-${log.at}`} className="text-sm">
                  <div className="flex items-center gap-2">
                    <Activity className="size-4 text-text-subtle" aria-hidden />
                    <p className="font-medium">{log.action}</p>
                  </div>
                  <p className="mt-1 text-xs text-text-subtle">
                    {log.target} · {log.admin}
                  </p>
                  <p className="text-xs text-text-subtle">
                    {formatDateTime(log.at)}
                  </p>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </main>
    </Shell>
  );
}
