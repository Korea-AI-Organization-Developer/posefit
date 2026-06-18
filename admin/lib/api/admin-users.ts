import { ApiError, apiFetch } from "@/lib/api/server";
import type { AdminUserDetail, AdminUserListItem, Page, UserStatus } from "@/lib/api/types";

export async function listUsers(params: {
  query?: string;
  status?: UserStatus | "";
  page?: number;
  size?: number;
}): Promise<Page<AdminUserListItem>> {
  const { query = "", status = "", page = 1, size = 10 } = params;

  const qs = new URLSearchParams();
  if (query) qs.set("query", query);
  if (status) qs.set("status", status);
  qs.set("page", String(page));
  qs.set("size", String(size));

  return apiFetch<Page<AdminUserListItem>>(`/admin/users?${qs.toString()}`);
}

export async function getUserDetail(id: number): Promise<AdminUserDetail | null> {
  try {
    return await apiFetch<AdminUserDetail>(`/admin/users/${id}`);
  } catch (e: unknown) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
