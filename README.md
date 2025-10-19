# aeghash

## 인증 CLI 체험하기

- 환경 변수로 백엔드 설정을 준비한 뒤 `scripts/auth_cli.py`를 실행하면 OAuth 공급자와 코드 값을 받아 인증을 시뮬레이션할 수 있습니다.
- 메트릭 출력을 보고 싶다면 `--metrics` 플래그를 추가하세요.

## 개발 모드 실행

- `AEGHASH_DEV_MODE=1`을 설정하면 필수 환경 변수가 안전한 기본값으로 채워지고, OAuth 클라이언트가 스텁 트랜스포트를 통해 동작합니다.
- 이 모드에서는 실제 계정/키 없이도 `scripts/auth_cli.py`로 Google/Kakao/Apple 인증 흐름을 로컬에서 검증할 수 있습니다.
- Turnstile 검증도 자동으로 통과하므로 프런트엔드에서 토큰 없이 개발 플로를 진행할 수 있습니다.

## 비밀 관리

- 운영 환경의 `MBLOCK_API_KEY` 등 MBlock 자격 증명은 AWS Secrets Manager(또는 동등한 KMS 기반 비밀 저장소)에 저장하고, 런타임 시 환경 변수로 주입합니다.
- `.env.example`은 로컬 개발 참고용이며 실제 키는 커밋하거나 공유하지 않습니다. 자세한 정책은 `docs/planning/integration_strategy.md` 6장을 참조하세요.

### Chromatic 토큰 설정

- UI 시각 회귀 테스트를 위해 Chromatic을 사용한다면 프로젝트 토큰을 발급받아 `.env`에 `CHROMATIC_PROJECT_TOKEN=<발급받은 토큰>`을 설정하세요.
- 1회 설정 후에는 `npx chromatic --project-token=$CHROMATIC_PROJECT_TOKEN`으로 Storybook 빌드를 업로드할 수 있습니다.
- 로컬에서는 `export CHROMATIC_PROJECT_TOKEN=...` 형태로 세션에 주입하거나, `direnv`/`dotenv` 도구로 자동 로딩하세요.
- GitHub Actions CI에서는 저장소 시크릿으로 `CHROMATIC_PROJECT_TOKEN`을 추가하면 `.github/workflows/chromatic.yml`이 자동으로 시각 회귀 테스트를 실행합니다.

## OAuth API 연동

- `aeghash.api.AuthenticationAPI`를 사용하면 OAuth 콜백(코드, state, Turnstile 토큰, 2FA 코드)을 처리해 `OAuthFlowService`를 실행할 수 있습니다.
- 컨테이너에 Turnstile 검증기가 활성화된 상태면 자동으로 `turnstile_token`과 `remote_ip`를 검증하고, 개발 모드(`AEGHASH_DEV_MODE=1`)에서는 토큰 없이도 흐름이 진행됩니다.
- API 계층에서는 프런트엔드에서 전달한 Turnstile 토큰과 요청 IP를 `authenticate(..., remote_ip=...)`로 넘겨주세요.
- 기본 SQLAlchemy 저장소를 활용하려면 `AuthenticationAPI.from_container(container)` 헬퍼를 사용하세요. 컨테이너의 세션 매니저를 통해 사용자 조회·세션 발급·2FA 저장소가 자동 배선됩니다.
- HTTP 서버가 필요하다면 `aeghash.api.http.create_http_app()`으로 FastAPI 인스턴스를 만들 수 있으며, `/oauth/callback`·`/signup`·`/login/password`·`/audit/logins` 엔드포인트를 사용할 수 있습니다.
- 2FA를 활성화한 사용자는 첫 호출에서 `requires_two_factor=true`가 반환되고, `two_factor_code`에 TOTP 값을 전달하면 세션이 발급됩니다.

## 일반 회원가입 API

- `/signup` 엔드포인트는 이메일/비밀번호를 받아 `user_accounts`와 `user_identities`에 레코드를 생성하고 기본 역할(`member`)을 부여합니다.
- 프로덕션 모드에서는 `/signup` 호출 시 Turnstile 토큰을 필수로 전달해야 하며, 검증 실패 시 `turnstile_failed` 오류가 반환됩니다.
- `/login/password` 엔드포인트는 이메일/비밀번호를 검증한 뒤 세션을 발급하며, `login_audit_logs`에 STARTED/FAILED/SUCCEEDED 이벤트를 기록합니다. `/audit/logins` 호출 시에는 로그인 응답으로 받은 세션 토큰을 `Authorization: Bearer <token>` 헤더에 포함하세요.
- 비밀번호 로그인 역시 Turnstile 토큰을 요구하며, 2FA가 설정된 사용자는 첫 호출에서 `requires_two_factor=true` 응답을 받고 `two_factor_code`로 TOTP 값을 제출해야 완료됩니다.
- 비밀번호는 `src/aeghash/security/passwords.py`의 PBKDF2 해시로 저장되며, 중복 이메일은 400(`email_already_exists`) 응답을 반환합니다.
- 2FA 활성화를 위해서는 `scripts/enable_two_factor.py`로 TOTP 시크릿을 발급한 뒤 `/oauth/callback` 흐름에서 검증할 수 있습니다.
- 출금 요청 시 위험 탐지 서비스(`src/aeghash/security/risk.py`)가 한도/신뢰 IP/새 디바이스 여부를 평가하고, 필요 시 `withdrawal_audit_logs`에 플래그/자동 취소 내역과 함께 알림을 발송합니다.
- 조직 트리(`src/aeghash/core/organization.py`)는 유니레벨/바이너리 구조와 스필오버 로깅을 지원하며, 보너스 엔진(`src/aeghash/core/bonus.py`)은 구성원의 경로를 따라 레벨별 퍼센티지를 적용해 `bonus_entries`에 기록합니다.

## DB 마이그레이션 & 시드

- Alembic 마이그레이션(`migrations/versions/202502141045_create_user_identities_table.py`)으로 `user_identities` 테이블을 생성합니다.
- 최초 사용자 바인딩은 `scripts/seed_user_identities.py`를 사용하세요. 예:

```bash
poetry run python scripts/seed_user_identities.py \
  --user-id admin-1 \
  --provider google \
  --subject 1234567890 \
  --roles admin,member
```
- 스크립트는 중복 항목을 건너뛰며 `DATABASE_URL` 환경 변수를 기본으로 사용합니다.
- 기존 계정에 KPI 스코프나 추가 역할을 부여하려면 `scripts/manage_identity_roles.py --provider google --subject 1234567890 --add-roles scope:kpi:node:binary:node-1`처럼 실행해 역할 리스트를 갱신할 수 있습니다. `--remove-roles` 옵션으로 불필요한 토큰을 제거할 수 있습니다.
- TOTP 활성화와 전체 운영 절차는 `docs/planning/auth_operations_playbook.md`를 참고하세요.

## KPI 알림 설정

- 운영 환경에서 KPI 최신 값이 하한선보다 낮아질 때 알림을 보내고 싶다면 `.env`에 `KPI_ALERT_PERSONAL_VOLUME_FLOOR`, `KPI_ALERT_GROUP_VOLUME_FLOOR`를 설정하세요.
- 두 값 중 하나라도 지정되면 FastAPI 컨테이너가 값을 읽어 `NotificationMessage`를 발송합니다. 기본 알림 채널은 컨테이너에 주입된 `Notifier` 구현(Webhook 등)에 따라 달라집니다.
