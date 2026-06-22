import { apiFetch } from "@/lib/api/server";
import type { AdminSessionListItem, Page, SessionStatus } from "@/lib/api/types";

export async function listSessions(params: {
  status?: SessionStatus;
  exerciseId?: number;
  from?: string;
  to?: string;
  page?: number;
  size?: number;
}): Promise<Page<AdminSessionListItem>> {
  const { status, exerciseId, from, to, page = 1, size = 10 } = params;

  const qs = new URLSearchParams();
  if (status) qs.set("status", status);
  if (exerciseId) qs.set("exerciseId", String(exerciseId));
  if (from) qs.set("from", from);
  if (to) qs.set("to", to);
  qs.set("page", String(page));
  qs.set("size", String(size));

  return apiFetch<Page<AdminSessionListItem>>(
    `/admin/workout-sessions?${qs.toString()}`,
  );
}
