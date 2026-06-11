import { Footer, Navbar } from "@/components/layout";
import { getMe } from "@/lib/mock/user";

/* 로그인 후 화면 그룹의 공통 셸 — 온보딩/로그인은 이 그룹 밖에 둔다 */
export default async function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const me = await getMe();

  return (
    <>
      <Navbar userName={me.nickname} avatarUrl={me.avatarUrl} />
      <main className="flex flex-1 flex-col">{children}</main>
      <Footer />
    </>
  );
}
