# AEG Hash 개발 계획 (Draft)

## 1. 범위 및 참조
- 플랫폼 전산 시스템 명세: `docs/planning/platform_system_plan.md`
- UI/UX 정책 및 세부 작업: `docs/planning/uiux_task_breakdown.md`
- 대상 범위: 사용자·관리자 웹앱, 보너스/조직 엔진, 자산·정산 모듈, 외부 API 연동, 운영 도구

### 공동 작업 원칙
- Codex Task1(백엔드·인프라)와 Codex Task2(프론트·UX)로 역할을 분리한다.
- Task1은 주로 `src/aeghash/`, `tests/`의 백엔드 로직, API 클라이언트, 데이터 처리 코드를 담당한다.
- Task2는 주로 `docs/`(UI 섹션), 프론트엔드 리포, 스토리북, 디자인 토큰 등 UI/UX 관련 산출물을 담당한다.
- 공통 산출물 변경이 필요할 경우, 먼저 상대 작업자에게 변경 범위를 공지하고 브랜치/파일 잠금 규칙을 따른다.

## 2. 선행 조건
- 인프라: Python 3.12 + Poetry 기반 백엔드, Next.js 혹은 유사 프론트엔드 프레임워크 선정
- 협업: 디자인 토큰 정의, API 명세, 데이터 모델 초안, 배포/모니터링 환경(Dev/Stage/Prod) 확립

## 3. 단계별 추진 계획

### 단계 0 — 준비 (2주)
- 프로젝트 구조 확정, 공용 라이브러리 설정, 기본 CI/CD 흐름 구성
- 디자인 토큰 정의 및 Figma/스토리북 연동 (`uiux_task_breakdown.md:7`~`uiux_task_breakdown.md:31`)

**Task1 (백엔드/인프라)**
- [x] 백엔드/프론트엔드 레포지토리 구조 초안 제안 및 합의 (`docs/planning/backend_structure_proposal.md`)
- [x] CI/CD 파이프라인(테스트·린트·빌드) 구성 (`.github/workflows/ci.yml`)
- [x] API 명세 초안 및 데이터 모델 워크숍 주관 (`docs/planning/api_data_model_outline.md`)
- [x] 런타임 환경 변수 템플릿 및 시크릿 관리 가이드 정리 (`.env.example`)

**Task2 (프론트/UX)**
- [x] 디자인 토큰 JSON 스키마 및 명명 규칙 합의
- [x] Figma 컴포넌트와 스토리북 토큰 매핑 검증
- [x] UI 산출물 버전 관리 정책 정의

### 단계 1 — 인증·보안 레이어 (3주)
- 소셜 로그인, Turnstile, 2FA, 감사 로그 파이프라인 구현 (`platform_system_plan.md:16`)
- 초기 관리자/사용자 권한 매트릭스와 접근 제어 적용 (`platform_system_plan.md:22`)

**Task1**
- [ ] Google/Kakao/Apple OAuth 연동 및 테스트
- [ ] Turnstile 적용(로그인/회원가입/비밀번호 찾기) 및 실패 케이스 처리
- [ ] 2FA(이메일/OTP) 설계 및 토큰 저장 정책 확정
- [ ] 로그인 감사 로그 및 보안 이벤트 트래킹 파이프라인 구축
- [ ] 역할/권한 매트릭스 적용과 초기 관리자 콘솔 접근 제어

**Task2**
- [x] 인증 UI 와이어프레임/프로토타입 제작 및 검수
- [x] Turnstile·2FA UX 안내 메시지와 오류 처리 가이드 작성

### 단계 2 — 자산·정산 모듈 (4주)
- 암호화폐/포인트 지갑 서비스, 출금 승인·보류 플로우 (`platform_system_plan.md:17`)
- 위험 탐지 룰, 알림 채널 및 감사 로그 연동
- 관리자 테이블/필터 UI 구현 (`uiux_task_breakdown.md:12`~`uiux_task_breakdown.md:16`)

**Task1**
- [ ] 지갑/포인트 도메인 모델 및 서비스 레이어 구현
- [x] MBlock Wallet API(`MBlock Docs v1.4`) 기반 지갑 생성·초기화 클라이언트 스켈레톤 구축 (`aeghash.adapters.mblock`)
- [x] MBlock Network/Transit API 연동(잔액 조회, 전송, 스왑/결제 시나리오) 준비: 트랜스포트/클라이언트 스켈레톤 및 단위 테스트 작성
- [x] Wallet Service 오케스트레이션 스켈레톤 (`aeghash.core.wallet_service`) 작성
- [x] Wallet Repository 인터페이스 정의(`aeghash.core.repositories`) 및 단위 테스트 작성 (`tests/unit/core/test_wallet_service.py`)
- [x] Wallet 통합 테스트 골격 (`tests/integration/test_wallet_flow.py`) 작성 및 InMemory 저장소 도입
- [x] SQLAlchemy 기반 Wallet Repository 구현(`aeghash.infrastructure.repositories`) 및 검증 테스트 (`tests/integration/test_sqlalchemy_repositories.py`)
- [x] SessionManager 컨텍스트(`src/aeghash/infrastructure/session.py`) 및 세션 단위 테스트 (`tests/unit/infrastructure/test_session_manager.py`)
- [x] DB/Alembic 전략 문서화 (`docs/planning/database_strategy.md`, `docs/planning/migration_strategy.md`)
- [x] 재시도/알림 워크플로 전략 문서화 (`docs/planning/retry_notification_strategy.md`)
- [ ] MBlock API Key/Value(문서 제공) 보안 저장 및 비밀 관리 정책 정의
- [ ] 출금 승인·보류·거절 워크플로 및 감사 로그 연계
- [ ] 위험 탐지 규칙(한도, IP, 디바이스) 정의 및 알림 채널 연결
- [ ] 통합 테스트 및 회귀 테스트 작성

**Task2**
- [ ] 관리자 대시보드 테이블/필터 컴포넌트 UI 제작
- [ ] 자산/정산 관련 UX 카피 및 사용자 알림 흐름 설계
- [ ] 출금/보류/위험 탐지 화면 시나리오 문서화

### 단계 3 — 조직·보너스 엔진 (4주)
- 유니레벨/바이너리 데이터 모델, 스필오버 로직, 보너스 배치 (`platform_system_plan.md:18`)
- 보너스 사후 정산/재시도 큐, KPI 대시보드 초안
- 관리자 조직도 뷰 UI 와이어프레임 → 구현

**Task1**
- [ ] 조직도 스키마(유니레벨/바이너리) 및 스필오버 알고리즘 구현
- [ ] 보너스 배치 파이프라인(추천/후원/공유/센터/센터추천) 개발
- [ ] 재시도 큐 및 실패 처리 전략 수립
- [ ] KPI 대시보드 초기 메트릭 정의 및 API 작성

**Task2**
- [ ] 조직도 뷰 UI(캔버스/줌/정보 패널) 프로토타입 및 개발
- [ ] KPI 대시보드 시각화 컴포넌트 설계
- [ ] 보너스 상태/경고 메시지 UX 가이드 작성

### 단계 4 — 커머스·채굴·가맹점 (5주)
- 쇼핑몰 상품/결제, PV 연동, AEGMALL·Hashdam API 통합 (`platform_system_plan.md:19`, `platform_system_plan.md:26`)
- 채굴 모니터링, 가맹점 POS/QR 결제, 직원 권한 관리
- 사용자 모바일 플로우 및 플로팅 내비 UI 구현 (`uiux_task_breakdown.md:18`~`uiux_task_breakdown.md:22`)

**Task1**
- [ ] 쇼핑몰 상품/결제 서버 로직 및 PV 반영 파이프 개발
- [x] HashDam Mining API(`HashDam API v1`) 연동 준비: 클라이언트 스켈레톤 및 응답 변환 유닛 테스트 (`aeghash.adapters.hashdam`)
- [x] Mining Service 스켈레톤 (`aeghash.core.mining_service`) 작성
- [x] Mining Repository 인터페이스 정의(`aeghash.core.repositories`) 및 단위 테스트 작성 (`tests/unit/core/test_mining_service.py`)
- [x] Mining 통합 테스트 골격 (`tests/integration/test_mining_flow.py`) 작성 및 InMemory 저장소 도입
- [x] SQLAlchemy 기반 Mining Repository 구현(`aeghash.infrastructure.repositories`) 및 검증 테스트 (`tests/integration/test_sqlalchemy_repositories.py`)
- [ ] AEGMALL·Hashdam API 멱등/재시도 전략 구현 및 통합 테스트
- [ ] HashDam API 인증 방식 확인(별도 Key Value 미제공 사항 코멘트) 및 호출 정책 정리
- [ ] HashDam 자산 인출 요청과 플랫폼 출금 승인 플로우 연동

**Task2**
- [ ] 채굴 현황(8종 자산) 대시보드 및 출금 요청 화면 제작
- [ ] 가맹점 POS/QR 결제, 정산 주기, 직원 권한 UI/UX 구현
- [ ] 모바일 플로우 와이어프레임을 반응형 UI로 구현 및 QA
- [ ] 가맹점/채굴 관련 사용자 교육 자료 및 인앱 가이드 작성

### 단계 5 — 운영 도구 및 안정화 (3주)
- 정산/출금 승인 워크플로, 감사·알림 정책, 필드 마스킹/RLS (`platform_system_plan.md:20`, `platform_system_plan.md:27`)
- 운영 대시보드 KPI, 반응형/접근성 QA, 회귀 테스트 자동화 (`uiux_task_breakdown.md:23`~`uiux_task_breakdown.md:28`)
- 문서화·릴리즈 프로세스 정비 (`uiux_task_breakdown.md:29`~`uiux_task_breakdown.md:31`)

**Task1**
- [ ] 정산/출금 승인 2인 검토 옵션 및 감사 로그 연동
- [ ] 필드 마스킹·RLS 정책 적용 및 운영자 권한 검토
- [ ] 운영 KPI 대시보드 백엔드 API 완성 및 모니터링 알림 연계

**Task2**
- [ ] 운영 대시보드 UI 완성 및 KPI 시각화 검수
- [ ] 반응형/접근성 테스트(contrast, 키보드 네비) 및 자동화 스크립트 실행
- [ ] 릴리즈 노트, 온보딩 자료, 협업 프로세스 문서화

## 4. 마일스톤 & 산출물
- M1 (단계 1 완료): 인증·보안 MVP + 관리자 기초 UI
- M2 (단계 2 완료): 지갑/정산 모듈, 관리자 대시보드 테이블
- M3 (단계 3 완료): 조직·보너스 엔진, KPI 대시보드 베타
- M4 (단계 4 완료): 쇼핑몰/가맹점/채굴 기능, 모바일 UX 베타
- GA (단계 5 완료): 운영 도구·QA·문서 마감, 전 기능 통합 테스트

## 5. 검증 계획
- 단계별 `poetry run pytest`, `ruff`, `mypy` 실행
- UI: 스토리북 시각 테스트, 접근성 검사(contrast, 키보드 네비게이션)
- API 통합: 샌드박스 환경에서 AEGMALL·Hashdam·BlockAPI 통합 테스트

## 6. 위험 및 대응
- 외부 API 변경: 계약 범위 명확화, Mock 서버 준비
- 조직/보너스 복잡도: 시뮬레이터 및 회귀 테스트 구축
- UI 일관성: 토큰 미정의 상태 방지 위해 단계 0에서 완료 후 착수
