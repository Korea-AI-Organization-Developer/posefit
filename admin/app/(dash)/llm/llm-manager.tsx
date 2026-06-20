"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Sparkles, Check, Pencil, Trash2 } from "lucide-react";

import { Dialog } from "@/components/ui/dialog";
import { Badge, Button, Card, CardBody, Input } from "@/components/ui";
import { buttonClasses } from "@/components/ui/button";
import { PROVIDER_LABEL } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import type { LlmModel, LlmProvider } from "@/lib/api/types";

const EMPTY_DRAFT = {
  provider: "google" as LlmProvider,
  modelName: "",
  displayName: "",
  paramsRaw: "",
};

export function LlmManager({ initial }: { initial: LlmModel[] }) {
  const router = useRouter();
  const [models, setModels] = useState(initial);
  const [pendingId, setPendingId] = useState<number | null>(null);

  // 등록 다이얼로그
  const [createOpen, setCreateOpen] = useState(false);
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [draft, setDraft] = useState(EMPTY_DRAFT);

  // 수정 다이얼로그
  const [editTarget, setEditTarget] = useState<LlmModel | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState({ modelName: "", displayName: "", paramsRaw: "" });

  function openEdit(m: LlmModel) {
    setEditTarget(m);
    setEditDraft({
      modelName: m.modelName,
      displayName: m.displayName,
      paramsRaw: m.params ? JSON.stringify(m.params, null, 2) : "",
    });
    setEditError(null);
  }

  async function deleteModel(id: number) {
    if (!window.confirm("모델을 삭제하시겠습니까?")) return;
    try {
      const res = await fetch(`/api/admin/llm/models/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        alert(body.detail ?? "삭제에 실패했습니다.");
        return;
      }
      setModels((prev) => prev.filter((m) => m.id !== id));
      router.refresh();
    } catch {
      alert("삭제에 실패했습니다.");
    }
  }

  async function activate(id: number) {
    setPendingId(id);
    try {
      const res = await fetch(`/api/admin/llm/models/${id}/activate`, { method: "POST" });
      if (!res.ok) throw new Error(`${res.status}`);
      const updated: LlmModel = await res.json();
      setModels((prev) =>
        prev.map((m) => (m.id === updated.id ? updated : { ...m, isActive: false })),
      );
      router.refresh();
    } catch {
      // 실패 시 버튼 로딩만 해제
    } finally {
      setPendingId(null);
    }
  }

  function parseParams(raw: string): [Record<string, unknown> | null, string | null] {
    if (!raw.trim()) return [null, null];
    try {
      return [JSON.parse(raw), null];
    } catch {
      return [null, "params 가 올바른 JSON 형식이 아닙니다."];
    }
  }

  async function addModel() {
    if (!draft.modelName.trim() || !draft.displayName.trim()) return;
    const [params, parseErr] = parseParams(draft.paramsRaw);
    if (parseErr) { setCreateError(parseErr); return; }

    setCreateSaving(true);
    setCreateError(null);
    try {
      const res = await fetch("/api/admin/llm/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: draft.provider, modelName: draft.modelName, displayName: draft.displayName, params }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const created: LlmModel = await res.json();
      setModels((prev) => [...prev, created]);
      setDraft(EMPTY_DRAFT);
      setCreateOpen(false);
      router.refresh();
    } catch {
      setCreateError("모델 등록에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setCreateSaving(false);
    }
  }

  async function saveEdit() {
    if (!editTarget) return;
    if (!editDraft.modelName.trim() || !editDraft.displayName.trim()) return;
    const [params, parseErr] = parseParams(editDraft.paramsRaw);
    if (parseErr) { setEditError(parseErr); return; }

    setEditSaving(true);
    setEditError(null);
    try {
      const res = await fetch(`/api/admin/llm/models/${editTarget.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modelName: editDraft.modelName, displayName: editDraft.displayName, params }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const updated: LlmModel = await res.json();
      setModels((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setEditTarget(null);
      router.refresh();
    } catch {
      setEditError("모델 수정에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setEditSaving(false);
    }
  }

  const paramsField = (value: string, onChange: (v: string) => void) => (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-text">
        파라미터 <span className="font-normal text-text-subtle">(선택, JSON)</span>
      </span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={'{"temperature": 0.7, "top_p": 0.9}'}
        rows={3}
        className="w-full rounded-sm border border-border bg-surface px-3 py-2 font-mono text-xs outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      />
    </label>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">RAG LLM 모델</h2>
          <p className="mt-1 text-sm text-text-muted">
            피드백 생성용 모델을 등록하고, 활성 모델을 런타임에 교체합니다 (1개만 활성).
          </p>
        </div>
        <Button leftIcon={<Plus aria-hidden />} onClick={() => setCreateOpen(true)}>
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
                    <p className="text-xs text-text-subtle">{PROVIDER_LABEL[m.provider]}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {m.isActive && <Badge tone="success">활성</Badge>}
                  <button
                    type="button"
                    onClick={() => openEdit(m)}
                    className={buttonClasses("ghost", "sm")}
                    aria-label="수정"
                  >
                    <Pencil className="size-3.5" aria-hidden />
                  </button>
                  {!m.isActive && (
                    <button
                      type="button"
                      onClick={() => deleteModel(m.id)}
                      className={buttonClasses("ghost", "sm")}
                      aria-label="삭제"
                    >
                      <Trash2 className="size-3.5 text-red-400" aria-hidden />
                    </button>
                  )}
                </div>
              </div>

              <p className="font-mono text-xs text-text-muted">{m.modelName}</p>
              {m.params && (
                <p className="truncate font-mono text-xs text-text-subtle">
                  {JSON.stringify(m.params)}
                </p>
              )}
              <p className="text-xs text-text-subtle">갱신 {formatDateTime(m.updatedAt)}</p>

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

      {/* 등록 다이얼로그 */}
      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="LLM 모델 등록"
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateOpen(false)} disabled={createSaving}>취소</Button>
            <Button onClick={addModel} loading={createSaving}>등록</Button>
          </>
        }
      >
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-text">제공자</span>
            <select
              value={draft.provider}
              onChange={(e) => setDraft({ ...draft, provider: e.target.value as LlmProvider })}
              className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
            >
              <option value="google">Google</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </label>
          <Input label="모델 식별자" value={draft.modelName} onChange={(e) => setDraft({ ...draft, modelName: e.target.value })} placeholder="gemini-3.5-flash" />
          <Input label="표시 이름" value={draft.displayName} onChange={(e) => setDraft({ ...draft, displayName: e.target.value })} placeholder="Gemini 3.5 Flash" />
          {paramsField(draft.paramsRaw, (v) => setDraft({ ...draft, paramsRaw: v }))}
          {createError && <p className="text-xs text-red-500">{createError}</p>}
        </div>
      </Dialog>

      {/* 수정 다이얼로그 */}
      <Dialog
        open={editTarget !== null}
        onClose={() => setEditTarget(null)}
        title="LLM 모델 수정"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditTarget(null)} disabled={editSaving}>취소</Button>
            <Button onClick={saveEdit} loading={editSaving}>저장</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input label="모델 식별자" value={editDraft.modelName} onChange={(e) => setEditDraft({ ...editDraft, modelName: e.target.value })} placeholder="gemini-3.5-flash" />
          <Input label="표시 이름" value={editDraft.displayName} onChange={(e) => setEditDraft({ ...editDraft, displayName: e.target.value })} placeholder="Gemini 3.5 Flash" />
          {paramsField(editDraft.paramsRaw, (v) => setEditDraft({ ...editDraft, paramsRaw: v }))}
          {editError && <p className="text-xs text-red-500">{editError}</p>}
        </div>
      </Dialog>
    </div>
  );
}
