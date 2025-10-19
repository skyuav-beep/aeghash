# UI 산출물 버전 관리 정책

## 1. 적용 범위
- 디자인 토큰 (`tokens/*.json`, `tokens/dist/*`)
- UI/UX 문서 (`docs/uiux/**`, 관련 계획 문서)
- 프론트엔드 컴포넌트 패키지 및 Storybook 산출물

## 2. 버전 규칙
- **Semantic Versioning (MAJOR.MINOR.PATCH)**를 기본으로 사용한다.
  - MAJOR: 컬러 스케일, 타이포 체계, 컴포넌트 API 등 파괴적 변경.
  - MINOR: 신규 토큰 추가, 컴포넌트 상태/옵션 확장, 문서/스토리 신규 작성.
  - PATCH: 오타 수정, 접근성 수치 조정, 문서화 보완 등 호환성을 깨지 않는 변경.
- 각 토큰 JSON의 `meta.version` 필드를 변경과 함께 업데이트하고, 변경 내용을 `docs/uiux/codex_task2_delivery.md`의 릴리즈 노트 섹션에 요약한다.

## 3. 브랜치 및 태깅 전략
- 작업 브랜치 네이밍: `ui/<scope>-<summary>` (예: `ui/tokens-focus-ring-update`).
- 릴리즈 준비 시 `release/ui-vX.Y.Z` 브랜치에서 QA 및 Chromatic 승인을 진행한다.
- 태그: `ui-vX.Y.Z` (토큰/스토리북 릴리즈)와 `ui-docs-vX.Y.Z` (문서 릴리즈)로 구분할 수 있으며, 필요 시 두 태그를 함께 달아 추적한다.

## 4. PR 체크리스트
- PR 본문에 `docs/uiux/pr_token_change_template.md`를 사용하고 아래 항목을 모두 충족한다.
  - [ ] `tokens/*.json` 변경 시 `scripts/export_design_tokens.py` 실행 및 `tokens/dist/*` 갱신 여부 확인.
  - [ ] `docs/uiux/figma_storybook_mapping.md`에 매핑 검증 로그 추가 또는 영향 없음 명시.
  - [ ] Chromatic 또는 Playwright 시각 회귀 테스트 결과 첨부.
  - [ ] 변경된 버전 번호 및 변경 유형(MAJOR/MINOR/PATCH) 명시.
  - [ ] 필요 시 `needs-ux-review` 라벨 추가 및 UX 승인자 할당.

## 5. 배포 프로세스
1. QA & 접근성 체크 완료 후 Main 브랜치에 머지.
2. `poetry run pytest`, `pnpm run storybook:build`, `pnpm run test:visual` 등 자동 검증을 통과했는지 확인.
3. Main 기준으로 Git 태그 생성 및 패키지/문서 배포.
4. 배포 후 `docs/uiux/codex_task2_delivery.md`의 릴리즈 노트 섹션에 링크와 주요 변경점을 기록.

## 6. 롤백 및 핫픽스
- 릴리즈 태그 기준으로 `git revert` 혹은 `git cherry-pick`을 활용해 Hotfix 브랜치를 생성한다.
- Hotfix는 `ui/hotfix-<issue>` 브랜치 네이밍을 사용하고, 패치 버전을 올린 뒤 즉시 태그(`ui-vX.Y.(Z+1)`)를 생성한다.
- 긴급 변경이라도 Chromatic 결과 또는 수동 캡처를 공유해 UI 회귀 여부를 확인한다.

## 7. 문서 유지보수
- 본 정책 문서는 변경 시 GitHub Wiki/Notion 등에 동시에 반영한다.
- 분기마다 정책 적합성 검토를 진행하고 필요 시 운영자 회의 후 개정한다.
