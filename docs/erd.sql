-- =====================================================================
-- PoseFit ERD (MySQL DDL)
-- Engine/Charset: InnoDB + utf8mb4 (한글/이모지 및 FK 지원)
-- 모든 datetime은 DATETIME(6)으로 통일, 모든 PK는 AUTO_INCREMENT
-- =====================================================================

CREATE TABLE `users` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`nickname`		VARCHAR(50)		NOT NULL	COMMENT '구글에서 받아온 이름이 기본',
	`role`			ENUM('user', 'admin')	NOT NULL	DEFAULT 'user'	COMMENT '사용자 | 관리자',
	`status`		ENUM('active', 'suspended', 'withdrawn')	NOT NULL	DEFAULT 'active'	COMMENT '활성 | 정지(관리자) | 탈퇴',
	`withdrawn_at`		DATETIME(6)		NULL,
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_details` (
	`user_id`		BIGINT			NOT NULL,
	`height`		DECIMAL(4,1)		NULL	COMMENT 'cm (50~250)',
	`weight`		DECIMAL(4,1)		NULL	COMMENT 'kg (20~300)',
	`birthdate`		DATE			NOT NULL,
	`gender`		ENUM('M', 'F', 'U')	NOT NULL	COMMENT '남성 | 여성 | 선택 안 함',
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `social_accounts` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`user_id`		BIGINT			NOT NULL,
	`provider`		VARCHAR(20)		NOT NULL	COMMENT 'google',
	`provider_uid`		VARCHAR(255)		NOT NULL	COMMENT '개인정보. 소셜 제공자 측 사용자 식별자.',
	`provider_email`	VARCHAR(255)		NULL		COMMENT '개인정보. 소셜 제공자 이메일(없을 수 있음).',
	`provider_avatar_url`	VARCHAR(512)		NULL		COMMENT '개인정보. 소셜 제공자 프로필 사진 URL(없을 수 있음, 로그인 시 갱신).',
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`),
	UNIQUE KEY `uq_provider_uid` (`provider`, `provider_uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `agreements` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`user_id`		BIGINT			NOT NULL,
	`tos_agreed`		BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '서비스 이용약관(필수)',
	`privacy_agreed`	BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '개인정보 수집·이용(필수)',
	`biometric_agreed`	BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '바이오정보(얼굴) 처리(필수)',
	`marketing_agreed`	BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '마케팅 수신(선택)',
	`agreed_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `face_embeddings` (
	`user_id`		BIGINT			NOT NULL,
	`embedding`		VARBINARY(2048)		NOT NULL	COMMENT '개인정보. 직렬화된 임베딩 벡터(가능하면 애플리케이션 단에서 암호화).',
	`model_version`		VARCHAR(50)		NOT NULL	COMMENT '임베딩 모델 버전. 동일 버전끼리만 비교 유효.',
	`bin_file_url`		VARCHAR(255)		NULL		COMMENT '원본 임베딩/이미지 파일의 오브젝트 스토리지 URL(선택).',
	`registered_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6)	COMMENT '등록날짜',
	PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `exercises` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`name_ko`		VARCHAR(100)		NOT NULL	COMMENT '표시 이름(한글).',
	`name_en`		VARCHAR(100)		NULL		COMMENT '표시 이름(영문).',
	`description`		TEXT			NULL,
	`reference_video_url`	VARCHAR(500)		NULL		COMMENT '정답(모범) 영상 URL.',
	`exercise_type`		ENUM('static', 'dynamic')	NOT NULL	DEFAULT 'dynamic'	COMMENT '정적운동 static | 동적운동 dynamic',
	`is_active`		BOOLEAN			NOT NULL	DEFAULT TRUE	COMMENT '운동 종목 노출 여부',
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `workout_sessions` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`user_id`		BIGINT			NOT NULL,
	`exercise_id`		BIGINT			NOT NULL,
	`status`		ENUM('in_progress', 'completed', 'aborted')	NOT NULL	DEFAULT 'in_progress',
	`started_at`		DATETIME(6)		NOT NULL	COMMENT '세션 시작 시각(UTC).',
	`ended_at`		DATETIME(6)		NULL		COMMENT '세션 종료 시각(UTC). 진행 중이면 NULL.',
	`score`			DECIMAL(5,2)		NULL		COMMENT '0~100점. 완료 시에만 채워짐.',
	`rep_count`		INT UNSIGNED		NULL		COMMENT '반복 횟수(횟수 기반 운동).',
	`hold_sec`		INT UNSIGNED		NULL		COMMENT '자세 유지 시간(초)(시간 기반 운동).',
	`saved`			BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '사용자가 영상을 저장했는지 여부.',
	`video_url`		VARCHAR(500)		NULL		COMMENT '개인정보. saved=true일 때 오브젝트 스토리지 URL.',
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`),
	KEY `idx_user_started` (`user_id`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `keypoint_frames` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`session_id`		BIGINT			NOT NULL,
	`frame_index`		INT			NOT NULL	COMMENT '세션 내 프레임 인덱스(0부터 시작).',
	`timestamp_ms`		BIGINT UNSIGNED		NOT NULL	COMMENT 'started_at 기준 경과 밀리초.',
	`keypoints`		JSON			NOT NULL	COMMENT '정규화된 관절 키포인트(0~1).',
	`bbox`			JSON			NULL		COMMENT '사람 바운딩 박스 [x, y, w, h].',
	PRIMARY KEY (`id`),
	UNIQUE KEY `uq_session_frame` (`session_id`, `frame_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `feedbacks` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`session_id`		BIGINT			NOT NULL,
	`content`		TEXT			NOT NULL	COMMENT '사용자에게 보여줄 자연어 피드백.',
	`severity`		ENUM('info', 'warning', 'critical')	NOT NULL	DEFAULT 'info',
	`generated_by`		ENUM('rule', 'llm')	NOT NULL,
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `workout_daily_stats` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`user_id`		BIGINT			NOT NULL,
	`exercise_id`		BIGINT			NOT NULL,
	`stat_date`		DATE			NOT NULL,
	`session_count`		INT UNSIGNED		NOT NULL	DEFAULT 0,
	`total_duration_sec`	INT UNSIGNED		NOT NULL	DEFAULT 0,
	`avg_score`		DECIMAL(5,2)		NULL,
	`best_score`		DECIMAL(5,2)		NULL,
	PRIMARY KEY (`id`),
	UNIQUE KEY `uq_user_exercise_date` (`user_id`, `exercise_id`, `stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- 관리자(운영) 도메인 — 소비자(users)와 신원/인증을 완전히 분리한다.
-- =====================================================================

CREATE TABLE `admin_accounts` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`email`			VARCHAR(255)		NOT NULL	COMMENT '로그인 ID(이메일).',
	`password_hash`		VARCHAR(255)		NOT NULL	COMMENT 'passlib bcrypt 해시.',
	`name`			VARCHAR(50)		NOT NULL,
	`role`			ENUM('super_admin', 'admin')	NOT NULL	DEFAULT 'admin'	COMMENT 'super_admin 만 관리자 계정·감사 로그 관리 가능.',
	`status`		ENUM('active', 'disabled')	NOT NULL	DEFAULT 'active'	COMMENT '활성 | 비활성',
	`token_version`		INT			NOT NULL	DEFAULT 0	COMMENT 'refresh 토큰 무효화용. 로그아웃 시 +1.',
	`last_login_at`		DATETIME(6)		NULL,
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`),
	UNIQUE KEY `uq_admin_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `llm_models` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`provider`		ENUM('google', 'openai', 'anthropic')	NOT NULL,
	`model_name`		VARCHAR(100)		NOT NULL	COMMENT 'API 식별자. 예: gemini-3.5-flash',
	`display_name`		VARCHAR(100)		NOT NULL	COMMENT 'UI 표시명.',
	`params`		JSON			NULL		COMMENT '기본 호출 파라미터(temperature 등).',
	`is_active`		BOOLEAN			NOT NULL	DEFAULT FALSE	COMMENT '활성 모델 여부. 정확히 1개 행만 true 유지(교체 시 트랜잭션). RAG 서비스가 활성 모델을 읽는다.',
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6),
	`updated_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `admin_audit_logs` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`admin_id`		BIGINT			NOT NULL,
	`action`		VARCHAR(50)		NOT NULL	COMMENT '예: export_keypoints, activate_llm, update_user_status',
	`target_type`		VARCHAR(50)		NULL		COMMENT 'user | exercise | session | llm_model',
	`target_id`		VARCHAR(64)		NULL,
	`detail`		JSON			NULL		COMMENT '필터 조건·변경 전후값 등 부가 정보.',
	`ip_address`		VARCHAR(45)		NULL,
	`created_at`		DATETIME(6)		NOT NULL	DEFAULT CURRENT_TIMESTAMP(6)	COMMENT 'append-only(생성만).',
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- 외래 키 (Foreign Keys)
-- =====================================================================

ALTER TABLE `user_details` ADD CONSTRAINT `FK_users_TO_user_details_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `social_accounts` ADD CONSTRAINT `FK_users_TO_social_accounts_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `agreements` ADD CONSTRAINT `FK_users_TO_agreements_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `face_embeddings` ADD CONSTRAINT `FK_users_TO_face_embeddings_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `workout_sessions` ADD CONSTRAINT `FK_users_TO_workout_sessions_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `workout_sessions` ADD CONSTRAINT `FK_exercises_TO_workout_sessions_1` FOREIGN KEY (
	`exercise_id`
)
REFERENCES `exercises` (
	`id`
);

ALTER TABLE `keypoint_frames` ADD CONSTRAINT `FK_workout_sessions_TO_keypoint_frames_1` FOREIGN KEY (
	`session_id`
)
REFERENCES `workout_sessions` (
	`id`
);

ALTER TABLE `feedbacks` ADD CONSTRAINT `FK_workout_sessions_TO_feedbacks_1` FOREIGN KEY (
	`session_id`
)
REFERENCES `workout_sessions` (
	`id`
);

ALTER TABLE `workout_daily_stats` ADD CONSTRAINT `FK_users_TO_workout_daily_stats_1` FOREIGN KEY (
	`user_id`
)
REFERENCES `users` (
	`id`
);

ALTER TABLE `workout_daily_stats` ADD CONSTRAINT `FK_exercises_TO_workout_daily_stats_1` FOREIGN KEY (
	`exercise_id`
)
REFERENCES `exercises` (
	`id`
);

ALTER TABLE `admin_audit_logs` ADD CONSTRAINT `FK_admin_accounts_TO_admin_audit_logs_1` FOREIGN KEY (
	`admin_id`
)
REFERENCES `admin_accounts` (
	`id`
);
