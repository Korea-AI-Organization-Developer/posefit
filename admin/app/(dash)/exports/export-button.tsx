"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui";
import type { AdminSessionListItem } from "@/lib/api/types";
import {
  generateFrames,
  toJsonl,
  toSessionJson,
} from "@/lib/mock/frames";

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** 단일 세션 내보내기 (JSONL / JSON) */
export function ExportButton({ session }: { session: AdminSessionListItem }) {
  const frames = () => generateFrames(session);

  return (
    <div className="flex justify-end gap-1.5">
      <Button
        size="sm"
        variant="secondary"
        leftIcon={<Download aria-hidden />}
        onClick={() =>
          download(
            `keypoints_session_${session.id}.jsonl`,
            toJsonl(frames()),
            "application/x-ndjson",
          )
        }
      >
        JSONL
      </Button>
      <Button
        size="sm"
        variant="secondary"
        onClick={() =>
          download(
            `keypoints_session_${session.id}.json`,
            toSessionJson(session, frames()),
            "application/json",
          )
        }
      >
        JSON
      </Button>
    </div>
  );
}

/** 여러 세션을 하나의 JSONL 로 묶어 내보내기 (학습 데이터셋) */
export function BulkExportButton({
  sessions,
}: {
  sessions: AdminSessionListItem[];
}) {
  function exportAll() {
    const all = sessions.flatMap((s) => generateFrames(s));
    const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "");
    download(`keypoints_${ts}.jsonl`, toJsonl(all), "application/x-ndjson");
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
