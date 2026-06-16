-- 운동 종목 초기 데이터 (exercises 테이블)
-- reference_video_url: 자세 설명 유튜브 영상
--
-- 실행 방법 (한글 깨짐 방지를 위해 반드시 --default-character-set=utf8mb4 옵션 사용):
--   docker exec posefit-db mysql --default-character-set=utf8mb4 -uhamin -p1234 posefit < docs/seed_exercises.sql

INSERT INTO exercises (name_ko, name_en, description, reference_video_url, exercise_type, is_active) VALUES
  ('런지',          'Lunge',          '한 발을 앞으로 내딛어 양 무릎을 90도로 굽혔다 펴는 하체 운동이에요. 앞 무릎이 발끝을 넘지 않게 하고, 상체는 곧게 세워 시선은 정면을 봅니다.', 'https://www.youtube.com/watch?v=BUkMLNHRpM0', 'dynamic', 1),
  ('플랭크',        'Plank',          '팔꿈치와 발끝으로 몸을 일직선으로 버티는 코어 운동이에요. 허리가 꺼지거나 엉덩이가 솟지 않도록 배에 힘을 주고 호흡을 일정하게 유지합니다.',       'https://www.youtube.com/watch?v=Zq8nRY9P_cM', 'static',  1),
  ('푸쉬업',        'Push-up',        '어깨너비로 손을 짚고 팔을 굽혀 가슴을 바닥 가까이 내렸다 미는 상체 운동이에요. 몸통을 일직선으로 유지하고 팔꿈치는 약 45도로 벌립니다.',        'https://www.youtube.com/watch?v=-_DUjHxgmWk', 'dynamic', 1),
  ('오버헤드프레스', 'Overhead Press', '덤벨이나 바벨을 머리 위로 밀어 올리는 어깨 운동이에요. 허리를 과도하게 젖히지 않도록 코어에 힘을 주고, 팔을 끝까지 곧게 폅니다.',               'https://www.youtube.com/watch?v=DgS7Y2bj2NM', 'dynamic', 1);
