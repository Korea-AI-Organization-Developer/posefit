"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";

import { Dialog } from "@/components/ui/dialog";
import {
  Badge,
  Button,
  Input,
  Table,
  THead,
  TBody,
  TR,
  TH,
  TD,
} from "@/components/ui";
import { buttonClasses } from "@/components/ui/button";
import { EXERCISE_TYPE_LABEL } from "@/lib/labels";
import type { AdminExercise, ExerciseType } from "@/lib/api/types";

type Draft = {
  nameKo: string;
  nameEn: string;
  exerciseType: ExerciseType;
  referenceVideoUrl: string;
  isActive: boolean;
};

const EMPTY: Draft = {
  nameKo: "",
  nameEn: "",
  exerciseType: "dynamic",
  referenceVideoUrl: "",
  isActive: false,
};

export function ExercisesManager({ initial }: { initial: AdminExercise[] }) {
  const router = useRouter();
  const [items, setItems] = useState(initial);
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditId(null);
    setDraft(EMPTY);
    setError(null);
    setOpen(true);
  }

  function openEdit(ex: AdminExercise) {
    setEditId(ex.id);
    setDraft({
      nameKo: ex.nameKo,
      nameEn: ex.nameEn ?? "",
      exerciseType: ex.exerciseType,
      referenceVideoUrl: ex.referenceVideoUrl ?? "",
      isActive: ex.isActive,
    });
    setError(null);
    setOpen(true);
  }

  async function save() {
    if (!draft.nameKo.trim()) return;
    setSaving(true);
    setError(null);

    try {
      if (editId == null) {
        const res = await fetch("/api/admin/exercises", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nameKo: draft.nameKo,
            nameEn: draft.nameEn || null,
            exerciseType: draft.exerciseType,
            referenceVideoUrl: draft.referenceVideoUrl || null,
          }),
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const created: AdminExercise = await res.json();
        setItems((prev) => [...prev, created]);
      } else {
        const res = await fetch(`/api/admin/exercises/${editId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nameKo: draft.nameKo,
            nameEn: draft.nameEn || null,
            exerciseType: draft.exerciseType,
            referenceVideoUrl: draft.referenceVideoUrl || null,
            isActive: draft.isActive,
          }),
        });
        if (!res.ok) throw new Error(`${res.status}`);
        const updated: AdminExercise = await res.json();
        setItems((prev) => prev.map((i) => (i.id === editId ? updated : i)));
      }
      setOpen(false);
      router.refresh();
    } catch {
      setError(
        editId == null
          ? "종목 등록에 실패했습니다. 다시 시도해주세요."
          : "종목 수정에 실패했습니다. 다시 시도해주세요.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">운동 종목</h2>
          <p className="mt-1 text-sm text-text-muted">
            종목 등록·수정, 노출 여부와 정답 영상 URL을 관리합니다.
          </p>
        </div>
        <Button leftIcon={<Plus aria-hidden />} onClick={openCreate}>
          종목 등록
        </Button>
      </div>

      <Table>
        <THead>
          <TR>
            <TH>ID</TH>
            <TH>이름</TH>
            <TH>유형</TH>
            <TH>정답 영상</TH>
            <TH>노출</TH>
            <TH className="text-right">관리</TH>
          </TR>
        </THead>
        <TBody>
          {items.map((ex) => (
            <TR key={ex.id}>
              <TD className="font-mono text-text-muted">{ex.id}</TD>
              <TD>
                <p className="font-medium">{ex.nameKo}</p>
                {ex.nameEn && (
                  <p className="text-xs text-text-subtle">{ex.nameEn}</p>
                )}
              </TD>
              <TD>{EXERCISE_TYPE_LABEL[ex.exerciseType]}</TD>
              <TD>
                {ex.referenceVideoUrl ? (
                  <Badge tone="success">등록됨</Badge>
                ) : (
                  <Badge tone="warning">미등록</Badge>
                )}
              </TD>
              <TD>
                <Badge tone={ex.isActive ? "success" : "neutral"}>
                  {ex.isActive ? "노출" : "숨김"}
                </Badge>
              </TD>
              <TD className="text-right">
                <button
                  type="button"
                  onClick={() => openEdit(ex)}
                  className={buttonClasses("ghost", "sm")}
                >
                  수정
                </button>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={editId == null ? "운동 종목 등록" : "운동 종목 수정"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)} disabled={saving}>
              취소
            </Button>
            <Button onClick={save} loading={saving}>
              저장
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="이름 (한글)"
            value={draft.nameKo}
            onChange={(e) => setDraft({ ...draft, nameKo: e.target.value })}
            placeholder="런지"
          />
          <Input
            label="이름 (영문)"
            value={draft.nameEn}
            onChange={(e) => setDraft({ ...draft, nameEn: e.target.value })}
            placeholder="Lunge"
          />
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-text">유형</span>
            <select
              value={draft.exerciseType}
              onChange={(e) =>
                setDraft({ ...draft, exerciseType: e.target.value as ExerciseType })
              }
              className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
            >
              <option value="dynamic">동적 (반복 횟수)</option>
              <option value="static">정적 (유지 시간)</option>
            </select>
          </label>
          <Input
            label="정답 영상 URL"
            value={draft.referenceVideoUrl}
            onChange={(e) =>
              setDraft({ ...draft, referenceVideoUrl: e.target.value })
            }
            placeholder="https://storage.posefit.dev/ref/..."
          />
          {editId != null && (
            <label className="flex cursor-pointer items-center gap-3">
              <span className="text-sm font-medium text-text">노출 여부</span>
              <button
                type="button"
                role="switch"
                aria-checked={draft.isActive}
                onClick={() => setDraft({ ...draft, isActive: !draft.isActive })}
                className={[
                  "relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent",
                  "transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
                  draft.isActive ? "bg-accent" : "bg-border",
                ].join(" ")}
              >
                <span
                  className={[
                    "pointer-events-none inline-block size-5 rounded-full bg-white shadow-sm",
                    "transition-transform duration-200",
                    draft.isActive ? "translate-x-5" : "translate-x-0",
                  ].join(" ")}
                />
              </button>
              <span className="text-sm text-text-muted">
                {draft.isActive ? "노출" : "숨김"}
              </span>
            </label>
          )}
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      </Dialog>
    </div>
  );
}
