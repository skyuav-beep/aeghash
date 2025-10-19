# Figma 리뷰 요청 메시지 초안 (단계 3 · Task2)

안녕하세요, Task2 팀 산출물 관련해서 Figma 업데이트 및 검토 요청드립니다.

## 변경 요약
- **조직도 뷰 UX**: `docs/uiux/organization_tree_ui.md`에 3분할 레이아웃, 줌/미니맵, 모바일 fallback 리스트 규칙을 정의했습니다.
- **KPI 대시보드**: `docs/uiux/kpi_dashboard_design.md`에 KPI 카드 4종, 그래프 위젯, 필터/자동 새로고침 정책을 정리했습니다.
- **보너스 상태/경고 메시지**: `docs/uiux/bonus_status_messaging.md`에서 상태 배지, 배너, 토스트 톤앤매너를 문서화했습니다.
- 스토리북 POC: `Admin/Organization`, `Admin/KPI`, `Admin/Bonus` 카테고리에 대응 컴포넌트 스토리를 추가했으며 `npm run storybook:build`로 정적 빌드를 생성했습니다. (`examples/frontend-storybook/storybook-static`)

## 요청 사항
1. Figma 파일
   - `Admin/OrganizationTree`: 문서 내용 반영 후 캔버스/미니맵/정보 패널 인터랙션 확인.
   - `Admin/KPI Dashboard`: KPI 카드·그래프 구조 및 반응형 대응 검토.
   - `Admin/Bonus Messaging`: 상태 배지/배너 스타일, 카피 가이드 적용.
2. UI/UX 피드백
   - 조직도 대기열 경고 임계값(50건)과 상태바 정보 노출 방식 적합성 확인.
   - KPI 자동 새로고침 주기(기본 5분)에 대한 의견.
   - 보너스 Critical/Warning 우선순위 정책, 이메일/푸시 템플릿 보강 필요 여부 공유.
3. 피드백 기한
   - 가능하다면 **10/18(금) EOD**까지 코멘트 부탁드립니다. 일정이 빠듯하다면 조정 제안 주세요.

감사합니다! 리뷰 완료 후 `docs/uiux/stage3_task2_review_notes.md`에 피드백 결과를 정리하겠습니다.***
