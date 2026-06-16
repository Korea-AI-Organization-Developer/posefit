"use client";

import { useState } from "react";
import { Plus, Sparkles, Check } from "lucide-react";

import { Dialog } from "@/components/ui/dialog";
import { Badge, Button, Card, CardBody, Input } from "@/components/ui";
import { PROVIDER_LABEL } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import type { LlmModel, LlmProvider } from "@/lib/api/types";

/*
 * RAG LLM 모델 관리 — mock 단계라 로컬 상태로 동작.
 * 백엔드 연동 시:
 *   - 활성 교체: POST /admin/llm/models/{id}:activate
 *   - 등록:     POST /admin/llm/models
 */
export function LlmManager({ initial }: { initial: LlmModel[] }) {
  const [models, setModels] = useState(initial);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({
    provider: "google" as LlmProvider,
    modelName: "",
    displayName: "",
  });

  async function activate(id: number) {
    setPendingId(id);
    await new Promise((r) => setTimeout(r, 350));
    setModels((prev) => prev.map((m) => ({ ...m, isActive: m.id === id })));
    setPendingId(null);
  }

  function addModel() {
    if (!draft.modelName.trim() || !draft.displayName.trim()) return;
    const nextId = Math.max(0, ...models.map((m) => m.id)) + 1;
    const now = new Date().toISOString();
    setModels([
      ...models,
      {
        id: nextId,
        provider: draft.provider,
        modelName: draft.modelName,
        displayName: draft.displayName,
        params: null,
        isActive: false,
        createdAt: now,
        updatedAt: now,
      },
    ]);
    setDraft({ provider: "google", modelName: "", displayName: "" });
    setOpen(false);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">RAG LLM 모델</h2>
          <p className="mt-1 text-sm text-text-muted">
            피드백 생성용 모델을 등록하고, 활성 모델을 런타임에 교체합니다 (1개만 활성).
          </p>
        </div>
        <Button leftIcon={<Plus aria-hidden />} onClick={() => setOpen(true)}>
          모델 등록
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {models.map((m) => (
          <Card key={m.id} className={m.isActive ? "ring-1 ring-accent" : ""}>
            <CardBody className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="flex size-9 items-center justify-center rounded-md bg-accent-soft text-accent">
                    <Sparkles className="size-4" aria-hidden />
                  </span>
                  <div>
                    <p className="text-sm font-medium">{m.displayName}</p>
                    <p className="text-xs text-text-subtle">
                      {PROVIDER_LABEL[m.provider]}
                    </p>
                  </div>
                </div>
                {m.isActive && <Badge tone="success">활성</Badge>}
              </div>

              <p className="font-mono text-xs text-text-muted">{m.modelName}</p>
              <p className="text-xs text-text-subtle">
                갱신 {formatDateTime(m.updatedAt)}
              </p>

              <Button
                size="sm"
                variant={m.isActive ? "secondary" : "primary"}
                disabled={m.isActive}
                loading={pendingId === m.id}
                onClick={() => activate(m.id)}
                leftIcon={m.isActive ? <Check aria-hidden /> : undefined}
                className="w-full"
              >
                {m.isActive ? "활성 모델" : "이 모델로 교체"}
              </Button>
            </CardBody>
          </Card>
        ))}
      </div>

      <p className="text-xs text-text-subtle">
        ⚠️ mock 동작 — 백엔드 연동 시 활성 교체가 감사 로그에 기록되고 RAG 서비스에 즉시 반영됩니다.
      </p>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="LLM 모델 등록"
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              취소
            </Button>
            <Button onClick={addModel}>등록</Button>
          </>
        }
      >
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-text">
              제공자
            </span>
            <select
              value={draft.provider}
              onChange={(e) =>
                setDraft({ ...draft, provider: e.target.value as LlmProvider })
              }
              className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
            >
              <option value="google">Google</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </label>
          <Input
            label="모델 식별자"
            value={draft.modelName}
            onChange={(e) => setDraft({ ...draft, modelName: e.target.value })}
            placeholder="gemini-3.5-flash"
          />
          <Input
            label="표시 이름"
            value={draft.displayName}
            onChange={(e) => setDraft({ ...draft, displayName: e.target.value })}
            placeholder="Gemini 3.5 Flash"
          />
        </div>
      </Dialog>
    </div>
  );
}
