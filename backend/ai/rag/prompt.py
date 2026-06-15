"""Gemini 입력 프롬프트 빌더.

# 역할
검색기(`retriever.py`)가 만든 `RetrievalResult` 를 Gemini 가 이해하기 좋은
한국어 텍스트로 변환한다. 시스템 프롬프트와 사용자 프롬프트를 분리해 반환한다.

# 출력 규격 (LLM 응답)
모델이 같은 형식으로 답하도록 시스템 프롬프트에 강하게 명시한다:

    ## 전체 요약
    (2~3문장 한국어 코멘트)

    ## 구간별 평가
    - [시작초 ~ 종료초] (correct|wrong) — 한 문장 코멘트
    - ...

    ## 핵심 개선 포인트
    - (있을 때만) 1~3개의 bullet

이 형식이 깨지면 다음 단계(UI/저장)에서 파싱이 어려워지므로 system 프롬프트에서
"이 형식 그대로" 라고 강조하고, user 프롬프트 끝부분에서도 다시 한 번 상기시킨다.

# 페르소나
- 한국어 사용 운동 코치.
- 플랭크 핵심 체크포인트:
  * 머리-목 중립 (시선 바닥)
  * 어깨가 팔꿈치 바로 위
  * 엉덩이 처짐(sag) / 들림(pike) 금지
  * 몸이 머리-엉덩이-발뒤꿈치 일직선
  * 복부·둔근 활성
- 추측은 줄이고, 검색기가 라벨링한 구간만 근거로 코멘트한다.
"""

from __future__ import annotations

from dataclasses import dataclass

from .retriever import RetrievalResult, Segment


SYSTEM_PROMPT = """당신은 플랭크 자세를 교정해주는 한국어 운동 코치입니다.

# 평가 원칙
- 사용자 영상은 자동 검색기가 프레임 단위로 정자세(correct)/오자세(wrong) 로 분류해
  시간 구간(segment) 단위로 정리해 전달합니다.
- 당신은 그 검색 결과를 근거로만 코멘트합니다. 검색 결과에 없는 사실은 추측하지 않습니다.
- 플랭크 핵심 체크포인트(머리-목 중립, 어깨-팔꿈치 정렬, 엉덩이 처짐/들림, 몸 일직선,
  복부/둔근 활성)를 기준으로 설명합니다.
- 어조: 단정적이되 친절하게. 사용자에게 동기를 주는 한 문장을 마지막에 덧붙입니다.

# 출력 형식 (반드시 아래 마크다운 형식을 그대로 따릅니다)

## 전체 요약
(2~3문장 한국어. 잘한 비율과 주된 문제 자세 한두 가지를 짚는다.)

## 구간별 평가
- [시작초 ~ 종료초] (correct|wrong) — 한 문장 코멘트
- ...

## 핵심 개선 포인트
- (오자세가 있을 때만, 1~3개의 bullet. correct 100% 면 이 섹션을 생략)

형식을 어기면 후속 처리(UI 표시, DB 저장) 가 실패하므로 항상 위 구조를 지킵니다.
"""


@dataclass
class GeminiPrompt:
    """Gemini 호출에 그대로 넘기는 시스템/사용자 프롬프트 묶음."""

    system: str
    user: str


def _fmt_segment_line(seg: Segment) -> str:
    return (
        f"- [{seg.start_ms / 1000:6.2f}s ~ {seg.end_ms / 1000:6.2f}s] "
        f"{seg.label} (frames={seg.frame_count}, conf={seg.avg_confidence:.2f})"
    )


def build_prompt(result: RetrievalResult) -> GeminiPrompt:
    """RetrievalResult → Gemini 프롬프트."""
    if result.total_frames == 0:
        # 검색 결과가 비면 코멘트 불가 — 대신 사용자에게 안내하라고 LLM 에 지시.
        user = (
            "검색기가 어떤 프레임도 분류하지 못했습니다. "
            "사용자에게 영상에서 사람이 잘 보이지 않았을 가능성을 안내하고, "
            "다시 촬영을 권하는 한 단락의 한국어 메시지를 작성하세요."
        )
        return GeminiPrompt(system=SYSTEM_PROMPT, user=user)

    duration_s = (
        result.timeline[-1].end_ms / 1000.0 if result.timeline else 0.0
    )
    lines = [
        "# 영상 메타",
        f"- 파일: {result.video_file or '(미상)'}",
        f"- fps: {result.fps if result.fps is not None else '(미상)'}",
        f"- 길이: 약 {duration_s:.2f}초",
        f"- 분석된 프레임: {result.total_frames}",
        f"- 정자세 비율: {result.correct_ratio:.1%}",
        f"- 오자세 비율: {result.wrong_ratio:.1%}",
        "",
        "# 검색기 타임라인",
        "각 줄은 ChromaDB top-k 다수결로 결정된 자세 구간이다.",
        "frames=구간 프레임 수, conf=거리 가중 confidence 평균.",
        "",
    ]
    lines.extend(_fmt_segment_line(seg) for seg in result.timeline)
    lines.append("")
    lines.append(
        "위 타임라인만을 근거로 시스템 프롬프트의 출력 형식에 맞게 한국어 코멘트를 작성하세요."
    )
    return GeminiPrompt(system=SYSTEM_PROMPT, user="\n".join(lines))
