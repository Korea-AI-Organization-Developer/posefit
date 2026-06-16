import Link from "next/link";

import { Pagination } from "@/components/pagination";
import { Badge, Table, THead, TBody, TR, TH, TD } from "@/components/ui";
import { USER_STATUS_LABEL, USER_STATUS_TONE } from "@/lib/labels";
import { formatDate } from "@/lib/format";
import { listUsers } from "@/lib/mock/admin-api";
import type { UserStatus } from "@/lib/api/types";
import { UsersFilter } from "./users-filter";

export const metadata = { title: "회원 관리" };

const SIZE = 10;

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ query?: string; status?: string; page?: string }>;
}) {
  const sp = await searchParams;
  const query = sp.query ?? "";
  const status = (sp.status ?? "") as UserStatus | "";
  const page = Math.max(1, Number(sp.page ?? 1) || 1);

  const result = await listUsers({ query, status, page, size: SIZE });

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">회원 관리</h2>
        <p className="mt-1 text-sm text-text-muted">
          회원을 검색·필터하고 상태(활성/정지/탈퇴)를 변경합니다.
        </p>
      </div>

      <UsersFilter query={query} status={status} />

      <Table>
        <THead>
          <TR>
            <TH>ID</TH>
            <TH>닉네임</TH>
            <TH>이메일</TH>
            <TH>상태</TH>
            <TH>가입일</TH>
            <TH className="text-right">관리</TH>
          </TR>
        </THead>
        <TBody>
          {result.items.length === 0 ? (
            <TR>
              <TD colSpan={6} className="py-10 text-center text-text-muted">
                조건에 맞는 회원이 없습니다.
              </TD>
            </TR>
          ) : (
            result.items.map((u) => (
              <TR key={u.id}>
                <TD className="font-mono text-text-muted">{u.id}</TD>
                <TD className="font-medium">{u.nickname}</TD>
                <TD className="text-text-muted">{u.email ?? "-"}</TD>
                <TD>
                  <Badge tone={USER_STATUS_TONE[u.status]}>
                    {USER_STATUS_LABEL[u.status]}
                  </Badge>
                </TD>
                <TD className="text-text-muted">{formatDate(u.createdAt)}</TD>
                <TD className="text-right">
                  <Link
                    href={`/users/${u.id}`}
                    className="text-sm text-accent hover:text-accent-active"
                  >
                    상세
                  </Link>
                </TD>
              </TR>
            ))
          )}
        </TBody>
      </Table>

      <Pagination page={result.page} size={result.size} total={result.total} />
    </div>
  );
}
