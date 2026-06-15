import { redirect } from "next/navigation";

import { Footer, Navbar } from "@/components/layout";
import { getMe } from "@/lib/api/users";

/* 로그인 후 화면 그룹의 공통 셸 — 온보딩/로그인은 이 그룹 밖에 둔다 */
export default async function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // proxy가 인증을 1차로 거르지만, 토큰 무효 등으로 getMe가 실패하면 랜딩으로 보낸다
  let me;
  try {
    me = await getMe();
  } catch {
    redirect("/");
  }

  return (
    <>
      <Navbar userName={me.nickname} avatarUrl={me.avatarUrl} />
      <main className="flex flex-1 flex-col">{children}</main>
      <Footer />
    </>
  );
}
