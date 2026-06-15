"""Gemini 호출 래퍼.

# 역할
프롬프트(시스템 + 사용자) 를 받아 Gemini 응답 텍스트를 돌려준다.
파이프라인의 다른 모듈은 API 키 관리·재시도·SDK 세부사항을 신경 쓸 필요가 없다.

# 설계 결정
1. **모델: gemini-2.5-flash**
   응답 지연이 짧고 충분한 한국어 품질. 더 정교한 코멘트가 필요하면 호출 시
   `model` 인자로 `gemini-2.5-pro` 등으로 손쉽게 교체할 수 있다.

2. **SDK: google-genai (신형)**
   2025년부터 권장되는 통합 SDK. `from google import genai` 로 import.

3. **API 키 로드**
   - `.env` 의 `GEMINI_API_KEY` 우선.
   - 환경변수에 직접 지정한 경우도 인정.
   - 없으면 즉시 `MissingApiKeyError` 를 raise — 잘못된 키로 호출하다가 뒤늦게
     실패하는 것보다 호출 전에 확실히 막는다.

4. **간단한 재시도**
   네트워크/일시 오류에 대비해 지수 backoff 로 최대 `max_retries` 회 재시도.
   `429`/`5xx` 가 명시적으로 잡히지 않더라도 어떤 예외든 동일하게 재시도한다
   (RAG 파이프라인은 한 번 호출/한 번 답이라 단순한 정책으로 충분).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from .prompt import GeminiPrompt

# .env 를 SDK 호출 전에 한 번 로드한다.
try:
    from dotenv import load_dotenv

    _BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
    if _BACKEND_ENV.exists():
        load_dotenv(_BACKEND_ENV)
except Exception:  # dotenv 가 없거나 로드 실패해도 환경변수만으로 동작 가능.
    pass


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_RETRIES = 2  # 총 호출 횟수 = 1 + retries.


class MissingApiKeyError(RuntimeError):
    """GEMINI_API_KEY 가 비어있을 때 발생."""


@dataclass
class LlmResponse:
    """LLM 답변 + 메타."""

    text: str
    model: str
    elapsed_s: float
    retries: int


def _get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise MissingApiKeyError(
            "GEMINI_API_KEY 가 비어있습니다. backend/.env 에 키를 채워주세요."
        )
    return key


def call_gemini(
    prompt: GeminiPrompt,
    model: str = DEFAULT_MODEL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> LlmResponse:
    """Gemini 한 번 호출.

    Args:
        prompt: `prompt.build_prompt()` 의 결과물.
        model:  Gemini 모델 이름.
        timeout_s: SDK 자체 타임아웃 (SDK 가 직접 지원하지 않으면 무시될 수 있음).
        max_retries: 실패 시 최대 재시도 횟수.

    Returns:
        LlmResponse — 답변 텍스트와 호출 메타.
    """
    # google-genai 는 import 비용이 약간 있어 호출 시점에 로드.
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_api_key())

    config = types.GenerateContentConfig(
        system_instruction=prompt.system,
        # 결정적인 형식을 원하므로 temperature 를 약간 낮춰둔다.
        temperature=0.4,
    )

    last_err: Exception | None = None
    start = time.monotonic()
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt.user,
                config=config,
            )
            text = (response.text or "").strip()
            return LlmResponse(
                text=text,
                model=model,
                elapsed_s=time.monotonic() - start,
                retries=attempt,
            )
        except Exception as e:  # 재시도 정책: 모든 예외에 대해 지수 backoff.
            last_err = e
            if attempt >= max_retries:
                break
            # 지수 backoff: 0.5, 1.0, 2.0 ...
            time.sleep(0.5 * (2**attempt))

    # 여기까지 왔다면 모든 재시도 실패.
    raise RuntimeError(
        f"Gemini 호출 실패 (재시도 {max_retries}회 포함): {last_err}"
    )
