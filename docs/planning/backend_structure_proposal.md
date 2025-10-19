# 백엔드/프론트엔드 레포지토리 구조 제안 (Codex Task1)

## 목표
- `spec.md`와 관련 정책 문서에 맞추어 백엔드/프론트엔드 개발 경로를 명확히 구분하고, 공용 모듈의 위치를 정의한다.
- 2개의 Codex가 병렬 작업 시 충돌을 최소화한다.

## 백엔드(현재 저장소) 구조 제안
- `src/aeghash/`
  - `core/` — 도메인 서비스, 애플리케이션 로직
  - `adapters/` — 외부 API 연동 모듈(HashDam, MBlock, AEGMALL 등)
  - `utils/` — 공용 유틸리티, 공통 상수/도우미
  - `schemas/` — Pydantic/dataclass 기반 요청·응답·데이터 모델 정의
- `tests/`
  - `unit/` — 기능 단위 테스트 (`test_<feature>.py`)
  - `integration/` — 외부 API 모킹한 통합 테스트
  - `resources/` — 테스트 픽스처/샘플 JSON
- `scripts/` — 유지보수 스크립트(데이터 마이그레이션, 배치 등)
- `docs/` — 계획 및 아키텍처 문서(현재 경로 유지)
- 환경 구성: `pyproject.toml`, `.env.example`, `.ruff.toml`, `.pre-commit-config.yaml`

## 프론트엔드(분리 레포 예정) 구조 제안
- `apps/web/` — 사용자 웹앱(Next.js), 모바일 우선 레이아웃
- `apps/admin/` — 관리자 대시보드(Next.js/React)
- `packages/ui/` — 공통 UI 라이브러리(디자인 토큰, 컴포넌트)
- `packages/utils/` — 공통 훅·헬퍼
- `storybook/` — 컴포넌트 문서화
- `docs/` — UX 가이드 및 접근성 문서

## 분리 작업 가이드
- 백엔드와 프론트엔드 레포를 Git 모노레포 또는 서브모듈로 관리할 경우 CI 파이프라인을 분리하여 배포 충돌 방지.
- 공통 스키마/계약은 `docs/planning/api_data_model_outline.md` 등에 정의 후 백엔드/프론트에서 공유.
- 비밀값은 각각 `.env`와 시크릿 매니저로 분리 관리.
