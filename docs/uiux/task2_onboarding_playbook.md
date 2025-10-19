# Codex Task2 온보딩 플레이북 (v1.0)

## 1. 목적
- Stage 5 Task2 요구사항에 따라 신규 Task2 참여자가 1주 이내에 UI/UX 워크플로에 적응하도록 지원한다.
- 디자인 토큰, 스토리북, 접근성 테스트 등 필수 산출물의 진입 장벽을 낮춘다.

## 2. 온보딩 키트
| 항목 | 위치 | 메모 |
| --- | --- | --- |
| UI/UX 정책 | `aeg_hash_uiux_policy.md` | 전사 컬러/타이포/컴포넌트 기준 |
| 디자인 토큰 | `tokens/*.json`, `tokens/dist/*` | `python scripts/export_design_tokens.py`로 동기화 |
| KPI 대시보드 스펙 | `docs/uiux/operations_dashboard_ui_review.md`, `docs/uiux/kpi_dashboard_design.md` | Stage 5 기준 최신 |
| 접근성 체크리스트 | `docs/uiux/accessibility_qa_checklist.md` | 자동화 테스트 실행 로그 포함 |
| Storybook 샘플 | `examples/frontend-storybook` | `npm run storybook`으로 로컬 프리뷰 |

## 3. 기본 워크플로
1. 저장소 클론 후 `poetry install`, `npm install`(스토리북 예제) 실행.
2. 디자인 토큰 동기화: `npm run tokens:sync` (또는 `python scripts/export_design_tokens.py`).
3. 스토리북 빌드: `npm run storybook:build` → 결과물 `storybook-static/`.
4. 접근성/시각 회귀 테스트
   - 접근성: `npx http-server storybook-static -p 6006 & npx @storybook/test-runner --failOnConsole --coverage`
   - 시각 회귀: `npm run chromatic` (토큰 필요).
5. 문서 업데이트 시 `docs/uiux/codex_task2_delivery.md` 릴리즈 노트 섹션에 반영.

## 4. 첫 주 체크리스트
- [ ] `docs/uiux/codex_task2_delivery.md` + `versioning_policy.md` 숙지.
- [ ] Storybook 접근성 테스트를 로컬에서 실행 후 결과 공유(`docs/uiux/a11y_responsive_test_report.md` 참조).
- [ ] KPI 대시보드 Figma 링크 확인 및 Variant 구조 이해.
- [ ] PR 템플릿(`docs/uiux/pr_token_change_template.md`) 기반 샘플 PR 작성.
- [ ] Slack `#codex-sync` 채널에 온보딩 완료 보고(템플릿: `docs/planning/task2_communication_templates.md` 3장).

## 5. 협업/리뷰 프로세스
- 주간 스탠드업: 월/수/금 10:00 KST, Task2 진행 상황 공유(2분 이내). 주요 이슈는 `#codex-standup`.
- Figma 하이라이트: 금요일 16:00 KST 전까지 변경 페이지에 `@Task1 Lead` 멘션.
- Storybook 리뷰: PR 제출 후 Chromatic 링크 첨부, QA는 24시간 내 승인/피드백.
- 문서 변경: 공용 파일 편집 전 `docs/planning/task2_communication_templates.md` 양식으로 사전 공지.

## 6. 참고 링크
- 릴리즈 노트: `docs/uiux/codex_task2_delivery.md#9-릴리즈-노트`
- 자동화 테스트 리포트: `docs/uiux/a11y_responsive_test_report.md`
- 교육 자료: `docs/uiux/education_content_outline.md`, `docs/uiux/inapp_tutorial_qc_plan.md`
