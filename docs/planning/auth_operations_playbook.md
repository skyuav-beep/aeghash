# Auth Operations Playbook

## 1. 목적
- 운영 환경에서 OAuth 사용자 매핑과 TOTP 기반 2단계 인증을 안전하게 초기화하기 위한 절차를 정리합니다.

## 2. 사전 준비
- `DATABASE_URL` 환경 변수 또는 명시적인 DB URL
- Turnstile 테스트/운영 시크릿 (`TURNSTILE_SECRET`)
- OAuth Provider 자격 증명 (client id / secret / redirect URI)
- Poetry 가상환경 및 Alembic, FastAPI 종속성 설치

## 3. 마이그레이션 실행
```bash
poetry run python - <<'PY'
from alembic import command
from alembic.config import Config

config = Config('alembic.ini')
config.set_main_option('sqlalchemy.url', 'postgresql+psycopg://user:pass@host/db')
command.upgrade(config, 'head')
PY
```

## 4. 사용자 OAuth 매핑 시드
```bash
poetry run python scripts/seed_user_identities.py \
  --database-url postgresql+psycopg://user:pass@host/db \
  --user-id admin-1 \
  --provider google \
  --subject 1234567890 \
  --roles admin,member
```

## 5. TOTP 시크릿 발급
```bash
poetry run python scripts/enable_two_factor.py \
  --database-url postgresql+psycopg://user:pass@host/db \
  --user-id admin-1 \
  --issuer "AEG Hash" \
  --label "Admin"
```
모니터링:
```bash
poetry run python - <<'PY'
from sqlalchemy import text
from aeghash.infrastructure.session import SessionManager

manager = SessionManager('postgresql+psycopg://user:pass@host/db')
with manager.session_scope() as session:
    identities = session.execute(text('SELECT provider, subject FROM user_identities')).fetchall()
    two_factor = session.execute(text('SELECT user_id, secret FROM two_factor_secrets')).fetchall()
print('Identities:', identities)
print('Two-factor:', two_factor)
manager.dispose()
PY
```

## 6. FastAPI 엔드포인트 검증
```bash
poetry run uvicorn aeghash.api.http:create_http_app --host 0.0.0.0 --port 8000
```
TURNSTile 더미/실제 토큰을 이용해 `/oauth/callback` 호출:
```bash
curl -X POST http://localhost:8000/oauth/callback \
  -H "Content-Type: application/json" \
  -d '{
        "provider": "google",
        "code": "<auth code>",
        "state": "<state>",
        "expected_state": "<state>",
        "turnstile_token": "<turnstile token>",
        "two_factor_code": "<OTP optional>"
      }'
```

일반 회원가입 `/signup` 흐름:
```bash
curl -X POST http://localhost:8000/signup \
  -H "Content-Type: application/json" \
  -d '{
        "email": "user@example.com",
        "password": "strong-password",
        "password_confirm": "strong-password",
        "turnstile_token": "<turnstile token>"
      }'
```

비밀번호 로그인 `/login/password`:
```bash
curl -X POST http://localhost:8000/login/password \
  -H "Content-Type: application/json" \
  -d '{
        "email": "user@example.com",
        "password": "strong-password",
        "turnstile_token": "<turnstile token>",
        "two_factor_code": "<OTP optional>"
      }'
```

로그인 감사 로그 조회(`/audit/logins`):
```bash
curl "http://localhost:8000/audit/logins?limit=50" \
  -H "X-Roles: admin,member"
```

## 7. 운영 체크리스트
- [ ] Alembic `head` 적용 여부 확인
- [ ] 최소 한 명의 관리자 계정이 `user_identities`에 등록되어 있는지 확인
- [ ] 필요 계정 TOTP 발급 및 otpauth URI 전달
- [ ] Turnstile 성공/실패/중복 케이스를 테스트 환경에서 재현
- [ ] `/oauth/callback` 200 응답 및 세션 발급 로그 확인
