-- =====================================================================
-- PoseFit ERD (MySQL DDL)
-- Engine/Charset: InnoDB + utf8mb4 (한글/이모지 및 FK 지원)
-- 모든 datetime은 DATETIME(6)으로 통일, 모든 PK는 AUTO_INCREMENT
-- =====================================================================

CREATE TABLE `users` (
	`id`			BIGINT			NOT NULL AUTO_INCREMENT,
	`nickname`		VARCHAR(50)		NOT NULL	COMMENT '구글에서 받아온 이름이 기본',
	`role`			ENUM('user', 'admin')	NOT NULL	DEFAULT 'user'	COMMENT '사용자 | 관리자',
	`status`		ENUM('active', 'withdrawn')	NOT NULL	DEFAULT 'active'	COMMENT '활성 | 탈퇴',
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
	`embedding`		VARBINARY(1024)		NOT NULL	COMMENT '개인정보. dlib 128차원 float64 직렬화 (1024 bytes).',
	`model_version`		VARCHAR(50)		NOT NULL	COMMENT '임베딩 모델 버전. 동일 버전끼리만 비교 유효.',
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
