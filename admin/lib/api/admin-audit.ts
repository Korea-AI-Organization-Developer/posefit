import { apiFetch } from "@/lib/api/server";
import type { AuditLog, Page } from "@/lib/api/types";

export async function listAuditLogs(params: {
  page?: number;
  size?: number;
}): Promise<Page<AuditLog>> {
  const { page = 1, size = 20 } = params;
  const qs = new URLSearchParams({ page: String(page), size: String(size) });
  return apiFetch<Page<AuditLog>>(`/admin/audit-logs?${qs.toString()}`);
}
