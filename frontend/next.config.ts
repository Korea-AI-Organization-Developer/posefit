import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 배포용 — .next/standalone 산출물로 경량 런타임 이미지 구성
  output: "standalone",
  images: {
    // 구글 OAuth 프로필 사진 호스트 (User.avatarUrl) — 외부 핫링크 허용
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
    ],
  },
};

export default nextConfig;
