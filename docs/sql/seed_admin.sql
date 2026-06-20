-- 관리자 초기 계정 (admin_accounts 테이블)
-- 비밀번호: Test1234!  (bcrypt, 운영 전 반드시 변경)
--
-- 실행 방법:
--   docker exec posefit-db mysql --default-character-set=utf8mb4 -u아이디 -p비밀번호 posefit < docs/sql/seed_admin.sql

INSERT INTO admin_accounts (email, password_hash, name, role, status, token_version)
VALUES (
  'admin@posefit.com',
  '$2b$12$EamQAm2c9lAElcwJZia3Re4t3/y0mYR.2TZPEhyxQ2stUtZS2Dc5y',
  '관리자',
  'super_admin',
  'active',
  0
);
