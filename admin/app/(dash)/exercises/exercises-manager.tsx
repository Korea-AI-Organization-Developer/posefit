"use client";

import { useState } from "react";
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
import { EXERCISE_TYPE_LABEL } from "@/lib/labels";
import type { AdminExercise, ExerciseType } from "@/lib/api/types";

type Draft = {
  nameKo: string;
  nameEn: string;
  exerciseType: ExerciseType;
  referenceVideoUrl: string;
};

const EMPTY: Draft = {
  nameKo: "",
  nameEn: "",
  exerciseType: "dynamic",
  referenceVideoUrl: "",
};

/*
 * 운동 종목 관리 — mock 단계라 로컬 상태로 동작.
 * 백엔드 연동 시: POST/PATCH /admin/exercises 호출 후 router.refresh().
 */
export function ExercisesManager({ initial }: { initial: AdminExercise[] }) {
  const [items, setItems] = useState(initial);
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);

  function openCreate() {
    setEditId(null);
    setDraft(EMPTY);
    setOpen(true);
  }

  function openEdit(ex: AdminExercise) {
    setEditId(ex.id);
    setDraft({
      nameKo: ex.nameKo,
      nameEn: ex.nameEn ?? "",
      exerciseType: ex.exerciseType,
      referenceVideoUrl: ex.referenceVideoUrl ?? "",
    });
    setOpen(true);
  }

  function save() {
    if (!draft.nameKo.trim()) return;
    if (editId == null) {
      const nextId = Math.max(0, ...items.map((i) => i.id)) + 1;
      setItems([
        ...items,
        {
          id: nextId,
          nameKo: draft.nameKo,
          nameEn: draft.nameEn || null,
          description: null,
          referenceVideoUrl: draft.referenceVideoUrl || null,
          exerciseType: draft.exerciseType,
          isActive: true,
        },
      ]);
    } else {
      setItems(
        items.map((i) =>
          i.id === editId
            ? {
                ...i,
                nameKo: draft.nameKo,
                nameEn: draft.nameEn || null,
                exerciseType: draft.exerciseType,
                referenceVideoUrl: draft.referenceVideoUrl || null,
              }
            : i,
        ),
      );
    }
    setOpen(false);
  }

  function toggleActive(id: number) {
    setItems(items.map((i) => (i.id === id ? { ...i, isActive: !i.isActive } : i)));
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
                <button
                  type="button"
                  onClick={() => toggleActive(ex.id)}
                  className="cursor-pointer"
                  aria-label="노출 토글"
                >
                  <Badge tone={ex.isActive ? "success" : "neutral"}>
                    {ex.isActive ? "노출" : "숨김"}
                  </Badge>
                </button>
              </TD>
              <TD className="text-right">
                <button
                  type="button"
                  onClick={() => openEdit(ex)}
                  className="text-sm text-accent hover:text-accent-active"
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
            <Button variant="secondary" onClick={() => setOpen(false)}>
              취소
            </Button>
            <Button onClick={save}>저장</Button>
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
        </div>
      </Dialog>
    </div>
  );
}
