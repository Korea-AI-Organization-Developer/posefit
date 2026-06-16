import Image from "next/image";
import Link from "next/link";
import { NavLinks } from "./nav-links";
import { UserMenu } from "./user-menu";

export interface NavbarProps {
  /** 로그인 사용자 이름 — 인증 연동 전까지 목업 기본값 */
  userName?: string;
  /** 구글 프로필 사진 URL. 없으면 이니셜 아바타로 대체 */
  avatarUrl?: string | null;
}

export function Navbar({ userName = "홍길동", avatarUrl }: NavbarProps) {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-10 px-6">
        <Link href="/dashboard" className="flex items-center gap-2">
          {/* 마크 비율 706×764 — 높이만 고정하고 너비는 비율 유지 */}
          <Image
            src="/brand/posefit-logo.svg"
            alt=""
            width={19}
            height={20}
            className="h-5 w-auto"
          />
          <span className="text-base font-semibold tracking-tight">
            PoseFit
          </span>
        </Link>

        <NavLinks />

        <UserMenu userName={userName} avatarUrl={avatarUrl} />
      </div>
    </header>
  );
}
