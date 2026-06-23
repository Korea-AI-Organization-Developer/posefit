"""전체 API 테스트용 더미 데이터 시드 스크립트.

openapi.yaml 의 모든 API(사용자·리포트·관리자·통계·내보내기)가 풍부한 응답을 내도록
DB 를 채운다. ORM 모델을 재사용해 대상 DB 에 직접 INSERT 한다.

실행:
    cd backend
    SEED_DATABASE_URL="mysql+pymysql://posefit:<pw>@116.125.141.65:13306/posefitdb" \
        uv run python scripts/seed_dummy.py

옵션:
    --wipe-seed         seed 마커(provider_uid LIKE 'seed-%') 가 붙은 더미 유저·관리자·감사로그
                        및 그 종속 데이터만 삭제 후 재시드. (실제 가입 유저는 건드리지 않음)
    --backfill-user ID  이미 존재하는 실제 user_id 에 쇼케이스급 운동 이력을 추가(사용자 API 테스트용).

환경변수:
    SEED_DATABASE_URL   대상 DB(pymysql). 미지정 시 DATABASE_URL 의 aiomysql→pymysql 변환.
    JWT_SECRET_KEY      (선택) 있으면 더미 유저용 access 토큰을 출력해 사용자 API 를 바로 테스트.
                        ★ 서버(.env)와 동일한 값이어야 서버가 토큰을 인정한다.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

# backend/ 를 import 경로에 추가 (scripts/ 의 부모)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import AdminAccount, AdminAuditLog, LlmModel
from app.models.enums import (
    AdminRole,
    AdminStatus,
    ExerciseType,
    FeedbackSeverity,
    FeedbackSource,
    Gender,
    LlmProvider,
    SessionStatus,
    UserRole,
    UserStatus,
)
from app.models.exercise import Exercise
from app.models.mixins import KST
from app.models.user import Agreement, SocialAccount, User, UserDetail
from app.models.workout import (
    Feedback,
    KeypointFrame,
    WorkoutAnalysis,
    WorkoutDailyStat,
    WorkoutSession,
)

random.seed(42)

NOW = datetime.now(KST)
TODAY = NOW.date()

SEED_UID_PREFIX = "seed-"
ADMIN_PASSWORD = "poseLLM2026"
ADMIN_EMAILS = ["admin1@posefit.kr", "admin2@posefit.kr", "admin3@posefit.kr"]

# 활성 4종 — name_en 은 프론트 이미지 매핑(Lunge/Plank/Push-up/Overhead Press)과 일치시킨다.
ACTIVE_EXERCISES = [
    ("런지", "Lunge", ExerciseType.dynamic, "한 발을 앞으로 내딛어 무릎을 굽혔다 펴는 하체 운동."),
    ("플랭크", "Plank", ExerciseType.static, "코어 전체를 사용해 자세를 유지하는 정적 운동."),
    ("푸쉬업", "Push-up", ExerciseType.dynamic, "가슴·삼두를 단련하는 상체 밀기 운동."),
    ("오버헤드프레스", "Overhead Press", ExerciseType.dynamic, "어깨 위로 밀어 올리는 어깨 운동."),
]
INACTIVE_EXERCISES = [
    ("스쿼트", "Squat", ExerciseType.dynamic, "하체 전반을 단련하는 기본 운동."),
    ("사이드플랭크", "Side Plank", ExerciseType.static, "옆구리·코어 안정성을 기르는 정적 운동."),
    ("버피", "Burpee", ExerciseType.dynamic, "전신 유산소·근력 복합 운동."),
    ("점핑잭", "Jumping Jack", ExerciseType.dynamic, "팔다리를 벌렸다 모으는 전신 유산소 운동."),
]

KO_FAMILY = list("김이박최정강조윤장임한오서신권황안송류전홍")
KO_GIVEN = ["민준", "서연", "도윤", "하은", "지호", "수아", "예준", "지유", "주원", "채원",
            "건우", "다은", "현우", "soo", "지민", "유진", "준서", "서윤", "지안", "하준",
            "은우", "시우", "윤서", "지우", "민서", "성훈", "가은", "태양", "보검", "지원"]

COACH_MSGS = [
    ("무릎이 발끝을 넘지 않도록 주의하세요.", FeedbackSeverity.warning),
    ("허리를 곧게 편 상태를 유지했어요. 좋습니다!", FeedbackSeverity.info),
    ("골반이 한쪽으로 기울고 있어요. 중심을 잡아보세요.", FeedbackSeverity.warning),
    ("동작 속도가 너무 빨라요. 천천히 정확하게 수행하세요.", FeedbackSeverity.info),
    ("팔꿈치 각도가 부족합니다. 충분히 굽혀주세요.", FeedbackSeverity.critical),
    ("호흡이 안정적이고 자세가 일관됩니다.", FeedbackSeverity.info),
    ("어깨가 솟아 있어요. 긴장을 풀고 내려주세요.", FeedbackSeverity.warning),
    ("코어에 힘이 잘 들어가 자세가 흔들리지 않았어요.", FeedbackSeverity.info),
]

ERROR_TYPES = ["knee_over_toe", "hip_tilt", "back_round", "elbow_angle", "shoulder_shrug", "speed_too_fast"]

COCO_NAMES = ["nose", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
              "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee",
              "right_knee", "left_ankle", "right_ankle"]


# ─── 헬퍼 ──────────────────────────────────────────────────────────────────
def resolve_db_url() -> str:
    url = os.getenv("SEED_DATABASE_URL")
    if url:
        return url
    raw = os.getenv("DATABASE_URL")
    if not raw:
        sys.exit("SEED_DATABASE_URL 또는 DATABASE_URL 환경변수가 필요합니다.")
    return raw.replace("+aiomysql", "+pymysql").replace("mysql://", "mysql+pymysql://", 1) \
        if "+aiomysql" in raw else raw.replace("mysql://", "mysql+pymysql://", 1)


def bcrypt_hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def rand_dt_within(days_ago_max: int, days_ago_min: int = 0) -> datetime:
    """오늘 기준 [days_ago_min, days_ago_max] 일 전의 랜덤 KST 시각."""
    d = random.randint(days_ago_min, days_ago_max)
    base = NOW - timedelta(days=d)
    return base.replace(hour=random.randint(7, 22), minute=random.randint(0, 59),
                        second=random.randint(0, 59), microsecond=0)


def make_keypoints() -> dict:
    return {
        "keypoints": [
            {"name": n,
             "x": round(random.uniform(0.1, 0.9), 4),
             "y": round(random.uniform(0.1, 0.9), 4),
             "z": round(random.uniform(-0.3, 0.3), 4),
             "visibility": round(random.uniform(0.7, 1.0), 3)}
            for n in COCO_NAMES
        ]
    }


def make_bbox() -> list:
    x = round(random.uniform(0.1, 0.4), 4)
    y = round(random.uniform(0.05, 0.3), 4)
    return [x, y, round(random.uniform(0.3, 0.5), 4), round(random.uniform(0.5, 0.7), 4)]


def make_analysis(exercise_name: str, error_count: int) -> dict:
    errors = []
    for _ in range(error_count):
        errors.append({
            "type": random.choice(ERROR_TYPES),
            "severity": random.choice(["info", "warning", "critical"]),
            "occurrence_ratio": round(random.uniform(0.1, 0.8), 2),
        })
    status = "correct" if error_count == 0 else "needs_correction"
    return status, {"exercise": exercise_name, "overall_status": status, "errors": errors}


# ─── wipe ──────────────────────────────────────────────────────────────────
def wipe_seed(db: Session) -> None:
    seed_user_ids = [
        uid for (uid,) in db.execute(
            select(SocialAccount.user_id).where(SocialAccount.provider_uid.like(f"{SEED_UID_PREFIX}%"))
        ).all()
    ]
    admin_ids = [
        aid for (aid,) in db.execute(select(AdminAccount.id).where(AdminAccount.email.in_(ADMIN_EMAILS))).all()
    ]
    if seed_user_ids:
        for model in (WorkoutAnalysis, KeypointFrame, Feedback):
            # Feedback/KeypointFrame/Analysis 는 session 경유라 user_id 로 직접 못 지움 → 세션 id 수집
            pass
        sess_ids = [
            sid for (sid,) in db.execute(
                select(WorkoutSession.id).where(WorkoutSession.user_id.in_(seed_user_ids))
            ).all()
        ]
        if sess_ids:
            db.execute(delete(WorkoutAnalysis).where(WorkoutAnalysis.session_id.in_(sess_ids)))
            db.execute(delete(KeypointFrame).where(KeypointFrame.session_id.in_(sess_ids)))
            db.execute(delete(Feedback).where(Feedback.session_id.in_(sess_ids)))
        db.execute(delete(WorkoutDailyStat).where(WorkoutDailyStat.user_id.in_(seed_user_ids)))
        db.execute(delete(WorkoutSession).where(WorkoutSession.user_id.in_(seed_user_ids)))
        db.execute(delete(UserDetail).where(UserDetail.user_id.in_(seed_user_ids)))
        db.execute(delete(Agreement).where(Agreement.user_id.in_(seed_user_ids)))
        db.execute(delete(SocialAccount).where(SocialAccount.user_id.in_(seed_user_ids)))
        db.execute(delete(User).where(User.id.in_(seed_user_ids)))
    if admin_ids:
        db.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_id.in_(admin_ids)))
        db.execute(delete(AdminAccount).where(AdminAccount.id.in_(admin_ids)))
    db.commit()
    print(f"[wipe] 더미 유저 {len(seed_user_ids)}명, 관리자 {len(admin_ids)}명 및 종속 데이터 삭제 완료")


# ─── 시드 ──────────────────────────────────────────────────────────────────
def ensure_reference(db: Session) -> tuple[list[Exercise], list[AdminAccount]]:
    """exercises / admin_accounts / llm_models — 이미 있으면 재사용(비파괴)."""
    # exercises
    existing = {e.name_en: e for e in db.execute(select(Exercise)).scalars().all()}
    exercises: list[Exercise] = []
    for name_ko, name_en, etype, desc in ACTIVE_EXERCISES:
        e = existing.get(name_en) or Exercise(
            name_ko=name_ko, name_en=name_en, description=desc,
            exercise_type=etype, is_active=True,
            reference_video_url=None,
        )
        if name_en not in existing:
            db.add(e)
        exercises.append(e)
    for name_ko, name_en, etype, desc in INACTIVE_EXERCISES:
        if name_en not in existing:
            db.add(Exercise(name_ko=name_ko, name_en=name_en, description=desc,
                            exercise_type=etype, is_active=False, reference_video_url=None))

    # admin_accounts (지정 3개)
    admins: list[AdminAccount] = []
    existing_admins = {a.email: a for a in db.execute(select(AdminAccount)).scalars().all()}
    roles = [AdminRole.super_admin, AdminRole.admin, AdminRole.admin]
    for email, role in zip(ADMIN_EMAILS, roles):
        a = existing_admins.get(email)
        if a is None:
            a = AdminAccount(
                email=email, password_hash=bcrypt_hash(ADMIN_PASSWORD),
                name=email.split("@")[0], role=role, status=AdminStatus.active,
                last_login_at=NOW - timedelta(days=random.randint(0, 5)),
            )
            db.add(a)
        admins.append(a)

    # llm_models (활성 정확히 1)
    if not db.execute(select(LlmModel)).scalars().first():
        db.add_all([
            LlmModel(provider=LlmProvider.google, model_name="gemini-2.0-flash",
                     display_name="Gemini 2.0 Flash", params={"temperature": 0.7}, is_active=True),
            LlmModel(provider=LlmProvider.openai, model_name="gpt-4o-mini",
                     display_name="GPT-4o mini", params={"temperature": 0.5}, is_active=False),
            LlmModel(provider=LlmProvider.anthropic, model_name="claude-sonnet-4-6",
                     display_name="Claude Sonnet 4.6", params={"temperature": 0.6}, is_active=False),
        ])

    db.flush()
    return exercises, admins


def make_users(db: Session) -> tuple[list[User], User]:
    """50명: 1 쇼케이스 + 37 active + 8 suspended + 4 withdrawn."""
    statuses = ([UserStatus.active] * 38) + ([UserStatus.suspended] * 8) + ([UserStatus.withdrawn] * 4)
    users: list[User] = []
    for i, status in enumerate(statuses):
        created = rand_dt_within(120, 1)
        nick = random.choice(KO_FAMILY) + random.choice(KO_GIVEN) if i != 0 else "쇼케이스데모"
        u = User(nickname=nick, role=UserRole.user, status=status,
                 created_at=created, updated_at=created, token_version=0)
        if status == UserStatus.withdrawn:
            u.withdrawn_at = created + timedelta(days=random.randint(5, 30))
        db.add(u)
        users.append(u)
    db.flush()  # user.id 확보

    for i, u in enumerate(users):
        db.add(SocialAccount(
            user_id=u.id, provider="google",
            provider_uid=f"{SEED_UID_PREFIX}{u.id:06d}",
            provider_email=f"user{u.id}@gmail.com",
            provider_avatar_url=None, created_at=u.created_at, updated_at=u.created_at,
        ))
        db.add(Agreement(
            user_id=u.id, tos_agreed=True, privacy_agreed=True,
            marketing_agreed=random.random() < 0.5, agreed_at=u.created_at,
        ))
        # 탈퇴 유저도 가입은 완료했었다고 보고 detail 부여(registration complete)
        db.add(UserDetail(
            user_id=u.id,
            height=round(random.uniform(150, 190), 1),
            weight=round(random.uniform(45, 95), 1),
            birthdate=(NOW - timedelta(days=random.randint(18 * 365, 55 * 365))).date(),
            gender=random.choice([Gender.M, Gender.F, Gender.U]),
            created_at=u.created_at, updated_at=u.created_at,
        ))
    db.flush()
    return users, users[0]


def make_history(db: Session, users: list[User], showcase: User, exercises: list[Exercise]):
    """세션 + 피드백 + 프레임 + 일별집계 + 분석 생성."""
    daily: dict[tuple, dict] = {}  # (user_id, ex_id, date) -> 집계
    sessions: list[WorkoutSession] = []
    session_meta: list[dict] = []  # 각 세션의 부가정보(분석/프레임 생성용)

    def add_session(user, ex, started, completed=True, age_days=0):
        is_static = ex.exercise_type == ExerciseType.static
        dur = random.randint(40, 90) if is_static else random.randint(60, 180)
        ended = started + timedelta(seconds=dur) if completed else None
        score = round(random.uniform(60, 98), 2) if completed else None
        s = WorkoutSession(
            user_id=user.id, exercise_id=ex.id,
            status=SessionStatus.completed if completed else random.choice(
                [SessionStatus.in_progress, SessionStatus.aborted]),
            started_at=started, ended_at=ended, score=score,
            rep_count=None if is_static else (random.randint(8, 25) if completed else None),
            hold_sec=(dur if (is_static and completed) else None),
            saved=(completed and random.random() < 0.3),
            created_at=started, updated_at=ended or started,
        )
        if s.saved:
            s.video_url = f"/uploads/workout_sessions/seed-{user.id}-{int(started.timestamp())}.mp4"
        db.add(s)
        sessions.append(s)
        session_meta.append({"user": user, "ex": ex, "started": started,
                             "dur": dur, "score": score, "completed": completed,
                             "age_days": age_days})
        if completed:
            key = (user.id, ex.id, started.date())
            agg = daily.setdefault(key, {"count": 0, "dur": 0, "scores": []})
            agg["count"] += 1
            agg["dur"] += dur
            agg["scores"].append(float(score))

    # 쇼케이스: 최근 75일, 주 4~5회, 다종목 + 오늘 세션
    for d in range(75, -1, -1):
        if random.random() < 0.62:  # 활동일
            for _ in range(random.randint(1, 3)):
                ex = random.choice(exercises)
                started = (NOW - timedelta(days=d)).replace(
                    hour=random.randint(7, 22), minute=random.randint(0, 59), second=0, microsecond=0)
                add_session(showcase, ex, started, completed=True, age_days=d)
    # 오늘 2~3종목 보장
    for ex in random.sample(exercises, k=random.randint(2, 3)):
        started = NOW.replace(minute=random.randint(0, 59), second=0, microsecond=0) - timedelta(hours=random.randint(0, 6))
        add_session(showcase, ex, started, completed=True, age_days=0)

    # 나머지 유저
    for u in users[1:]:
        if u.status == UserStatus.withdrawn:
            n = random.randint(0, 5)
            span = 90
        elif u.status == UserStatus.suspended:
            n = random.randint(5, 15)
            span = 80
        else:  # active
            n = random.randint(8, 30)
            span = 60
        for _ in range(n):
            ex = random.choice(exercises)
            age = random.randint(0, span)
            started = (NOW - timedelta(days=age)).replace(
                hour=random.randint(7, 22), minute=random.randint(0, 59), second=0, microsecond=0)
            add_session(u, ex, started, completed=(random.random() < 0.85), age_days=age)

    db.flush()  # session.id 확보

    # 피드백 (완료 세션) + 프레임(일부) + 분석(일부)
    frame_session_pool = [m for m, s in zip(session_meta, sessions)
                          if m["completed"]]
    random.shuffle(frame_session_pool)
    frame_targets = set(id(m) for m in frame_session_pool[:18])  # 18개 세션에 프레임

    for s, m in zip(sessions, session_meta):
        if not m["completed"]:
            continue
        # 피드백 1~3
        for content, sev in random.sample(COACH_MSGS, k=random.randint(1, 3)):
            db.add(Feedback(
                session_id=s.id, content=content, severity=sev,
                generated_by=random.choice([FeedbackSource.rule, FeedbackSource.llm]),
                created_at=m["started"] + timedelta(seconds=m["dur"]),
            ))
        # 프레임
        if id(m) in frame_targets:
            for fi in range(random.randint(15, 30)):
                db.add(KeypointFrame(
                    session_id=s.id, frame_index=fi,
                    timestamp_ms=fi * 33, keypoints=make_keypoints(), bbox=make_bbox()))

    # 분석: 쇼케이스 최근 + active 유저 일부 (과거=오류많음/최근=오류적음)
    analyses_meta = [(s, m) for s, m in zip(sessions, session_meta)
                     if m["completed"] and (m["user"].id == showcase.id or random.random() < 0.15)]
    for s, m in analyses_meta:
        # age_days 클수록 오류 많게
        err = max(0, round((m["age_days"] / 75) * 5 + random.uniform(-1, 1)))
        err = min(err, 6)
        status, result = make_analysis(m["ex"].name_en, err)
        db.add(WorkoutAnalysis(
            session_id=s.id, user_id=m["user"].id, exercise_id=m["ex"].id,
            overall_status=status, analysis_result=result,
            created_at=m["started"] + timedelta(seconds=m["dur"]),
        ))

    # 일별 집계
    for (uid, eid, d), agg in daily.items():
        scores = agg["scores"]
        db.add(WorkoutDailyStat(
            user_id=uid, exercise_id=eid, stat_date=d,
            session_count=agg["count"], total_duration_sec=agg["dur"],
            avg_score=round(sum(scores) / len(scores), 2) if scores else None,
            best_score=round(max(scores), 2) if scores else None,
        ))

    db.flush()
    return len(sessions), len(daily)


def make_audit_logs(db: Session, admins: list[AdminAccount]):
    super_admin = admins[0]
    actions = [
        ("export_keypoints", "session", lambda: str(random.randint(1, 200)),
         lambda: {"format": random.choice(["json", "jsonl"]), "frameCount": random.randint(0, 30)}),
        ("activate_llm", "llm_model", lambda: str(random.randint(1, 3)),
         lambda: {"model": random.choice(["gemini-2.0-flash", "gpt-4o-mini"])}),
        ("update_user_status", "user", lambda: str(random.randint(1, 50)),
         lambda: {"from": "active", "to": random.choice(["suspended", "active"])}),
    ]
    for _ in range(60):
        action, ttype, tid_fn, detail_fn = random.choice(actions)
        db.add(AdminAuditLog(
            admin_id=super_admin.id, action=action, target_type=ttype, target_id=tid_fn(),
            detail=detail_fn(), ip_address=f"127.0.0.{random.randint(1, 50)}",
            created_at=rand_dt_within(20, 0),
        ))
    db.flush()


def mint_jwt(user_id: int) -> str | None:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        return None
    from jose import jwt
    alg = os.getenv("JWT_ALGORITHM", "HS256")
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "type": "access", "exp": exp}, secret, algorithm=alg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe-seed", action="store_true")
    parser.add_argument("--backfill-user", type=int, default=None)
    args = parser.parse_args()

    engine = create_engine(resolve_db_url(), pool_pre_ping=True)
    with Session(engine) as db:
        if args.wipe_seed:
            wipe_seed(db)

        if args.backfill_user is not None:
            u = db.get(User, args.backfill_user)
            if u is None:
                sys.exit(f"user_id={args.backfill_user} 없음")
            exercises = [e for e in db.execute(select(Exercise).where(Exercise.is_active.is_(True))).scalars().all()]
            n, d = make_history(db, [u], u, exercises)
            db.commit()
            print(f"[backfill] user_id={u.id} 에 세션 {n}건, 일별집계 {d}건 추가")
            return

        # 이미 시드돼 있으면 중단(비파괴) — 재시드하려면 --wipe-seed
        if db.execute(select(AdminAccount).where(AdminAccount.email == ADMIN_EMAILS[0])).scalars().first():
            sys.exit("이미 시드된 것으로 보입니다(admin1 존재). 재시드하려면 --wipe-seed 를 사용하세요.")

        exercises, admins = ensure_reference(db)
        users, showcase = make_users(db)
        n_sessions, n_daily = make_history(db, users, showcase, exercises)
        make_audit_logs(db, admins)
        db.commit()

        # 요약 출력
        print("\n=== 시드 완료 ===")
        print(f"exercises   : {len(ACTIVE_EXERCISES)} 활성 + {len(INACTIVE_EXERCISES)} 비활성")
        print(f"admins      : {', '.join(ADMIN_EMAILS)}  (비번 {ADMIN_PASSWORD})")
        print(f"users       : {len(users)}  (active 38 / suspended 8 / withdrawn 4)")
        print(f"sessions    : {n_sessions}")
        print(f"daily_stats : {n_daily}")
        print(f"showcase    : user_id={showcase.id} ({showcase.nickname})")
        tok = mint_jwt(showcase.id)
        if tok:
            print(f"\n쇼케이스 사용자 토큰(7일):\n  Authorization: Bearer {tok}")
        else:
            print("\n(JWT_SECRET_KEY 미설정 → 사용자 토큰 미출력. 서버와 동일한 키로 실행하면 토큰을 출력합니다.)")


if __name__ == "__main__":
    main()
