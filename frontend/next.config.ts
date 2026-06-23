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
  experimental: {
    // 운동 영상 업로드(:stop) 허용 크기 — Pages Router의 config.api.bodyParser는
    // App Router route handler에서 동작하지 않으므로 여기서 설정
    serverActions: {
      bodySizeLimit: "200mb",
    },
  },
};

export default nextConfig;
