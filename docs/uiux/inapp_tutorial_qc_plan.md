# 인앱 튜토리얼 & FAQ 매핑 + QA 실행 계획 (v0.1)

## 1. 화면 매핑
- **채굴 대시보드 온보딩**
  - 트리거: 신규 사용자 첫 3회 접속 또는 업데이트 후 최초 접속.
  - 컴포넌트: `OnboardingCard` 슬라이더(최대 5장) → `채굴 요약`, `자산 카드 스와이프`, `출금 플로우`.
  - 위치: 대시보드 상단 hero 영역(채굴 요약 카드 위).
- **가맹점 POS 온보딩**
  - 트리거: `내 매장 QR` 메뉴 최초 진입 시.
  - 컴포넌트: OnboardingCard(4~5장), POS 처리에 필요한 CTA 버튼과 연결.
  - 위치: POS 패널 상단 또는 모달.
- **FAQ 접근 경로**
  - 헤더 우측 `도움말` 버튼 → Bottom Sheet(모바일) / 사이드패널(데스크탑)에서 `FAQAccordion` 렌더링.
  - 카테고리별 탭 제공(채굴, 출금/보안, 가맹점, 직원 관리).

## 2. QA 시나리오
1. **온보딩 카드 흐름**
   - 확인: 카드 순서, CTA 라벨, 접근성(포커스 이동, 스크린리더).
   - 체크리스트 연결: `docs/uiux/mobile_responsive_qa_and_training.md` 1.1, 1.2.
2. **FAQ 아코디언**
   - 확인: 카테고리 태그, 질문/답변 텍스트, 키보드 조작(`Tab`, `Enter`), VoiceOver/TalkBack 읽기.
   - 스냅샷: `Education/FAQ Accordion` 스토리로 비주얼 회귀 커버.
3. **출금 튜토리얼 Step Modal**
   - 확인: 3단계 진행 표시, 오류 메시지, `prefers-reduced-motion` 동작.
4. **POS 튜토리얼**
   - 확인: QR 생성→결제→환불 흐름 안내 및 CTA 링크 정확성.
   - QA 체크리스트 연결: `docs/uiux/mobile_responsive_qa_and_training.md` 1.3.

## 3. 운영 절차
- 스토리북 → 개발 브랜치 반영 후 Playwright 스냅샷 업데이트(`npm run storybook` + `npx playwright test --update-snapshots`).
- QA 체크리스트 구글시트/Notion에 복사하여 테스트 증적 기록(뷰포트/기기/결과).
- 릴리즈 전 교육 콘텐츠 변경 시 `docs/uiux/education_content_outline.md` 업데이트 필수.

## 4. 남은 과제
- 실디바이스(iOS/Android) 접근성 테스트 일정 확정.
- 온보딩 카드 다국어 번역 및 레이아웃 확인.
- 분석 이벤트 정의: 온보딩 카드 스킵률, FAQ 열람 비율 모니터링.

