# Decimal: 소수를 "오차 없이" 다루는 파이썬 타입. 점수(예: 83.08) 같은 돈/점수 계산에 씀.
#          float(부동소수)는 미세 오차가 생길 수 있어 DB의 DECIMAL 컬럼과 짝으로 Decimal을 쓴다.
from decimal import Decimal

# ExerciseType: "static" | "dynamic" 두 값만 허용하는 Enum(열거형). models/enums.py에 정의돼 있음.
#               여기서 타입으로 쓰면 엉뚱한 문자열이 들어오는 걸 막아준다.
from app.models.enums import ExerciseType

# CamelModel: 우리가 만든 공통 베이스(schemas/base.py).
#             파이썬 안에서는 name_ko(snake_case)로 쓰되, JSON으로 나갈 땐 nameKo(camelCase)로
#             자동 변환해주는 설정이 들어있다. 모든 API 입출력 스키마가 이걸 상속한다.
from app.schemas.base import CamelModel


# ExerciseSummary: "운동 한 개"의 요약 정보 형식. 목록(items)에 들어가는 한 칸의 모양.
#                  docs/openapi.yaml 의 ExerciseSummary 스키마를 그대로 파이썬으로 옮긴 것.
class ExerciseSummary(CamelModel):
    id: int                          # 운동 고유 번호 (DB exercises.id). 정수.
    name_ko: str                     # 한글 이름 (예: "런지"). 반드시 있음(str).
    name_en: str | None              # 영문 이름 (예: "Lunge"). 없을 수 있음(None 허용) → openapi의 nullable.
    exercise_type: ExerciseType      # 운동 종류. static(정적/자세유지) 또는 dynamic(동적/반복) 둘 중 하나만.
    is_active: bool                  # 노출 여부. True면 사용자에게 보이는 운동.
    user_avg_score: Decimal | None   # "이 API를 호출한 사용자"의 평균 점수. 한 번도 안 했으면 None.


# ExerciseListResponse: 목록 API(GET /exercises)의 "전체 응답" 형식.
#                       openapi의 ExerciseListResponse 와 동일.
class ExerciseListResponse(CamelModel):
    items: list[ExerciseSummary]     # ExerciseSummary(운동 요약)들을 담은 리스트(배열).
