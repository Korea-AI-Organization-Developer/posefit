import { ArrowRight, Search } from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  Input,
} from "@/components/ui";

/* 임시 UI 프리뷰 — 라우팅 골격(1-C)이 잡히면 교체한다 */
export default function Home() {
  return (
    <main className="mx-auto w-full max-w-2xl flex-1 space-y-6 px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">PoseFit UI</h1>

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold">Button</h2>
        </CardHeader>
        <CardBody className="flex flex-wrap items-center gap-3">
          <Button>운동 시작하기</Button>
          <Button variant="secondary">정답 영상 보기</Button>
          <Button variant="ghost">건너뛰기</Button>
          <Button variant="danger">회원 탈퇴</Button>
          <Button loading>분석 중</Button>
          <Button size="lg" rightIcon={<ArrowRight />}>
            다음
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold">Input</h2>
        </CardHeader>
        <CardBody className="space-y-4">
          <Input
            label="이름"
            placeholder="홍길동"
            helperText="OAuth 프로필에서 가져온 값을 수정할 수 있습니다"
          />
          <Input
            label="키 (cm)"
            placeholder="170"
            error="50~250 사이로 입력해 주세요"
          />
          <Input label="검색" placeholder="운동 종목 검색" leftIcon={<Search />} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold">Badge</h2>
        </CardHeader>
        <CardBody className="flex items-center gap-2">
          <Badge>대기</Badge>
          <Badge tone="success">92점</Badge>
          <Badge tone="warning">주의</Badge>
          <Badge tone="danger">중단됨</Badge>
        </CardBody>
      </Card>
    </main>
  );
}
