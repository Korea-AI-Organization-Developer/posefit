import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { getCurrentAdmin } from "@/lib/mock/admin-api";

/*
 * 인증된 관리자 공통 셸 — 좌측 사이드바 + 상단바.
 * proxy.ts 가 1차로 미인증 접근을 /login 으로 보낸다.
 * 백엔드 연동 시 getCurrentAdmin() 을 apiFetch("/admin/me") 로 교체하고,
 * 실패 시 redirect("/login") 한다.
 */
export default async function DashLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const admin = await getCurrentAdmin();

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar admin={admin} />
        <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
