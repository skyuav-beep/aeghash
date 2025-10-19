# 모바일 전용 인터랙션 모션 스펙 (v0.1)

## 1. 공통 파라미터
- 기본 지속시간: 0.18s (기본), 0.12s (`prefers-reduced-motion` 활성 시).
- Easing: `cubic-bezier(0.22, 0.61, 0.36, 1)` (표준), `linear` (Skeleton/Progress).
- Shadow/Blur: 토큰 `components.motion.shadow.*` 참조, Elevation 변화 시 2단계 이내로 제한.

## 2. Bottom Navigation
- 탭 전환: Fade + Scale 0.96→1.0, 지속 0.18s, easing 표준.
- Indicator bar: Width transition 0.16s, color `colors.palette.primary`, delay 0.04s.
- Haptic: 탭 전환 시 `UIImpactFeedbackStyleLight`.

## 3. Floating Action Button
- Appear: Slide up 24px + Fade (0.2→1.0), 0.2s.
- Pressed: Scale 1.0→0.94→1.0, 0.12s, easing `cubic-bezier(0.4, 0, 0.2, 1)`.
- Hide on scroll: Scroll down 32px 이상 시 0.18s로 아래로 슬라이드.

## 4. Toast
- Enter: TranslateY 12px→0, opacity 0→1, 0.18s.
- Exit: TranslateY 0→12px, opacity 1→0, 0.14s.
- Swipe dismiss: Threshold 40px, velocity 500px/s 이상 시 dismiss.

## 5. Step Modal
- Step transition: Horizontal slide 24px, opacity 0→1, 0.2s.
- Progress bar: Width change 0.24s, easing linear.
- Back navigation: Reverse slide, 0.16s.

## 6. Animation Tokens
- `tokens/components.json`에 다음 키 추가 필요:
  - `components.motion.duration.short`, `components.motion.duration.medium`.
  - `components.motion.easing.standard`, `components.motion.easing.linear`.
  - `components.motion.haptic.light`.

## 7. Lottie 프로토타입 범위
- FAB appear/disappear
- Step Modal 단계 전환
- Toast swipe dismiss

## 8. QA 체크리스트
- 모션 지속시간 제한 준수 여부 (`prefers-reduced-motion` 대응 포함).
- 포커스 상태에서 모션이 입력 방해하지 않는지 검토.
- 하드웨어 저사양 기기(60fps 이하)에서 프레임 드랍 체크.
