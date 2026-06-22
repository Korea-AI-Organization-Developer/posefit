"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui";
import type { AdminSessionListItem } from "@/lib/api/types";

function triggerDownload(url: string) {
  const a = document.createElement("a");
  a.href = url;
  a.click();
}

/** 단일 세션 내보내기 (JSONL / JSON) */
export function ExportButton({ session }: { session: AdminSessionListItem }) {
  const base = `/api/admin/exports/keypoints?sessionId=${session.id}`;

  return (
    <div className="flex justify-end gap-1.5">
      <Button
        size="sm"
        variant="secondary"
        leftIcon={<Download aria-hidden />}
        onClick={() => triggerDownload(`${base}&format=jsonl`)}
      >
        JSONL
      </Button>
      <Button
        size="sm"
        variant="secondary"
        onClick={() => triggerDownload(`${base}&format=json`)}
      >
        JSON
      </Button>
    </div>
  );
}

/** 현재 필터 기준 전체 세션을 하나의 JSONL 로 내보내기 */
export function BulkExportButton({
  sessions,
  exerciseId,
  from,
  to,
}: {
  sessions: AdminSessionListItem[];
  exerciseId: string;
  from: string;
  to: string;
}) {
  function exportAll() {
    const qs = new URLSearchParams({ format: "jsonl" });
    if (exerciseId) qs.set("exerciseId", exerciseId);
    if (from) qs.set("from", new Date(from).toISOString());
    if (to) qs.set("to", new Date(to).toISOString());
    triggerDownload(`/api/admin/exports/keypoints?${qs.toString()}`);
  }

  return (
    <Button
      variant="primary"
      leftIcon={<Download aria-hidden />}
      onClick={exportAll}
      disabled={sessions.length === 0}
    >
      현재 목록 JSONL 내보내기
    </Button>
  );
}
