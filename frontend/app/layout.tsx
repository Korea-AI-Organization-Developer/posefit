import type { Metadata } from "next";
import localFont from "next/font/local";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

/* 본문 한글 폰트 — Pretendard 가변 폰트 (npm 패키지에서 셀프호스팅) */
const pretendard = localFont({
  src: "../node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2",
  weight: "45 920",
  display: "swap",
  variable: "--font-pretendard",
});

/* 숫자(점수·횟수) 강조용 모노 폰트 */
const geistMono = Geist_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: {
    default: "PoseFit — AI 운동 자세 분석",
    template: "%s | PoseFit",
  },
  description:
    "웹캠으로 운동하면 AI가 자세를 분석해 점수와 피드백을 제공하는 홈트레이닝 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className={`${pretendard.variable} ${geistMono.variable} h-full`}
    >
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
