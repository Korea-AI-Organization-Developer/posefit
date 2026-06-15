import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // 구글 OAuth 프로필 사진 호스트 (회원 아바타) — 외부 핫링크 허용
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
    ],
  },
};

export default nextConfig;
