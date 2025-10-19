# 디자인 토큰 변경 PR 체크리스트 템플릿

> PR 본문에 아래 섹션을 복사해 사용하세요. 모든 항목을 채워야 승인됩니다.

## 1. 변경 요약
- 영향 범위:
- 변경 유형: <!-- MAJOR / MINOR / PATCH -->

## 2. 토큰/문서 업데이트
- [ ] `tokens/*.json` 업데이트
- [ ] `scripts/export_design_tokens.py` 실행 후 `tokens/dist/*` 반영
- [ ] `docs/uiux/figma_storybook_mapping.md` 매핑 로그 업데이트 (링크 또는 영향 없음 기재)
- [ ] 관련 문서 업데이트 (예: `docs/uiux/codex_task2_delivery.md`, 아키텍처 문서 등)

## 3. 검증 자료
- Chromatic 빌드 링크: <!-- https://www.chromatic.com/build?appId=... -->
- Playwright 시각 테스트: <!-- 테스트 파일/로그 경로 또는 스크린샷 -->
- 수동 QA (선택): <!-- 기기/브라우저, 테스트 시나리오 요약 -->

## 4. 버전 관리
- 적용 버전: `ui-vX.Y.Z`
- 태깅/배포 메모:

## 5. 체크리스트
- [ ] `poetry run pytest`
- [ ] `pnpm run storybook:build`
- [ ] `pnpm run test:visual`
- [ ] `needs-ux-review` 라벨 지정 및 담당자 멘션

## 6. 참고 링크
- Figma 페이지: <!-- https://www.figma.com/file/... -->
- Notion/회의 노트: <!-- 필요 시 -->

