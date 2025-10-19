# Repository Guidelines / 저장소 가이드라인

## Project Structure & Module Organization / 프로젝트 구조와 모듈 구성
- Place runtime modules under `src/aeghash/` with feature subpackages (e.g., `hashers.py`). / 런타임 모듈은 기능별 서브패키지와 함께 `src/aeghash/`에 둡니다.
- Keep shared helpers in `src/aeghash/utils/` and integration adapters in `src/aeghash/adapters/`. / 공용 헬퍼는 `src/aeghash/utils/`, 연동용 어댑터는 `src/aeghash/adapters/`에 배치합니다.
- Store unit and integration suites in `tests/unit/` and `tests/integration/`; fixtures live in `tests/resources/`. / 단위·통합 테스트는 `tests/unit/`, `tests/integration/`에 두고, 픽스처는 `tests/resources/`에 둡니다.
- Scripts belong in `scripts/`; keep `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml` at the root. / 스크립트는 `scripts/`, 설정 파일은 저장소 루트에 유지합니다.

## Build, Test, and Development Commands / 빌드·테스트·개발 명령
- Use Python 3.12 via Poetry for dependency isolation. / 의존성 격리를 위해 Python 3.12와 Poetry를 사용합니다.
- `poetry install` — install dependencies and create the virtualenv. / `poetry install` — 의존성 설치와 가상환경 생성을 수행합니다.
- `poetry run pytest` — run the full test matrix; prefer `-n auto` for quick unit runs. / `poetry run pytest` — 전체 테스트를 실행하며, 빠른 단위 실행에는 `-n auto`를 권장합니다.
- `poetry run ruff check src tests` and `poetry run ruff format` — lint then format. / `poetry run ruff check src tests`, `poetry run ruff format` — 린트 후 포맷을 적용합니다.
- `poetry run mypy src` — enforce typing on public modules. / `poetry run mypy src` — 공개 모듈의 타입을 검증합니다.

## Coding Style & Naming Conventions / 코딩 스타일과 네이밍 규칙
- Follow PEP 8 with 4-space indentation and ≤100-char lines. / PEP 8을 따르고 들여쓰기는 4칸, 줄 길이는 100자 이하로 유지합니다.
- Name modules descriptively (`hash_strategy.py`), classes PascalCase, functions snake_case, constants UPPER_SNAKE_CASE. / 모듈은 의미 있게, 클래스는 PascalCase, 함수·변수는 snake_case, 상수는 UPPER_SNAKE_CASE로 명명합니다.
- Prefer dataclasses over ad-hoc tuples; document tricky logic with concise comments. / 임시 튜플보다 dataclass를 우선 사용하고 복잡한 로직은 간결하게 주석 처리합니다.
- Run `poetry run ruff format` before committing; avoid manual edits to generated code. / 커밋 전 `poetry run ruff format`을 실행하고 생성 코드에는 수동 수정을 피합니다.

## Testing Guidelines / 테스트 지침
- Use Pytest with pytest-cov; every bugfix adds a regression test. / Pytest와 pytest-cov를 사용하며 모든 버그 수정에는 회귀 테스트를 추가합니다.
- Target ≥90% statement coverage across `src/aeghash/`. / `src/aeghash/` 전반에서 구문 커버리지 90% 이상을 목표로 합니다.
- Name files `test_<feature>.py`; tag long runs with `@pytest.mark.slow`. / 테스트 파일은 `test_<feature>.py`로 지정하고 긴 실행은 `@pytest.mark.slow`로 태깅합니다.
- Use shared fixtures from `tests/conftest.py`; mock outbound calls instead of hitting live services. / 공용 픽스처는 `tests/conftest.py`에서 불러오고 외부 호출은 실서비스 대신 모킹합니다.

## Commit & Pull Request Guidelines / 커밋 및 PR 지침
- Follow Conventional Commits (`feat:`, `fix:`, `chore:`) and keep one logical change per commit. / Conventional Commits(`feat:`, `fix:`, `chore:`)를 따르고 커밋에는 하나의 논리 변경만 포함합니다.
- Rebase before opening PRs to maintain linear history. / PR 생성 전 리베이스로 선형 히스토리를 유지합니다.
- PR description must cover problem, solution, validation (`poetry run pytest`), and screenshots for UI updates. / PR 설명에는 문제, 해결책, 검증(`poetry run pytest`), UI 변경 시 스크린샷을 포함해야 합니다.
- Link issues with `Closes #123`, request maintainer review, and wait for green CI. / `Closes #123` 형식으로 이슈를 연결하고, 관리자 리뷰 후 CI 성공을 확인합니다.

## Security & Configuration Tips / 보안 및 설정 팁
- Keep secrets out of VCS; load via `.env` ignored by git. / 비밀값은 VCS에 올리지 말고 git에서 제외된 `.env`로 로드합니다.
- Run `poetry run safety check` at least quarterly to review dependencies. / 분기마다 `poetry run safety check`로 의존성을 점검합니다.
- Document new hash algorithms in `docs/architecture.md` with threat considerations. / 새로운 해시 알고리즘은 위협 분석과 함께 `docs/architecture.md`에 문서화합니다.
