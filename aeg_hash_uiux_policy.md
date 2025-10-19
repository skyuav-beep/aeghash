# 🎨 AEG Hash UI/UX & Color System Policy (v1.1)

## 📘 개요
AEG Hash 시스템은 **관리자(Admin)** 와 **사용자(User)** 로 UI/UX를 구분한다.

- **Admin:** PC 중심, 데이터 관리 및 운영 효율성을 우선한 데스크탑 인터페이스.
- **User:** 웹앱(모바일 우선) 반응형으로 설계된 인터페이스.

---

## 🧩 전체 구조
| 구분 | 대상 | 주요 기기 | 주요 목적 | UI 특징 |
|------|------|-------------|------------|------------|
| **Admin** | 내부 운영자 | PC (1920px 기준) | 데이터 관리, 정산, 회원관리, 설정 | 데이터 테이블 중심, 다단 메뉴 구조, 고정 사이드바 |
| **User (WebApp)** | 일반 사용자 | 모바일/태블릿/PC 반응형 | 해시파워 구매, 로그인, 리워드 확인 | 단일 컬럼, 터치 중심, 간결한 인터페이스 |

---

## 🎨 컬러 팔레트 (Color Palette)

| 역할 | 색상 | HEX | 사용 예시 |
|------|------|------|------------|
| **Primary** | Yellow | `#FDC915` | 주요 버튼, 포인트 강조 |
| **Primary Light** | Light Yellow | `#FFE46D` | Hover 효과, 강조 배경 |
| **Text Primary** | Dark Gray | `#1A1A1A` | 주요 텍스트 |
| **Text Secondary** | Medium Gray | `#444444` | 보조 설명 텍스트 |
| **Background** | White | `#FFFFFF` | 기본 배경 |
| **Border / Line** | Light Gray | `#EAEAEA` | 버튼, 카드, 구분선 |
| **Accent (Optional)** | Deep Blue | `#002F6C` | Admin 대시보드 포인트 색 |

---

## 🧱 공통 컴포넌트 정책

### 1. **타이포그래피 (Typography)**
- **폰트:** `Inter`, `Pretendard`, `Noto Sans KR`
- **크기:**
  - Title: 24px Bold
  - Subtitle: 14px Italic
  - Button Text: 16px Medium
  - Table Text (Admin): 14px Regular

### 2. **버튼(Button)**
| 구분 | 배경색 | 테두리 | 텍스트 | 모서리 | 상태 |
|------|----------|-----------|------------|----------|----------|
| Primary | `#FDC915` | 없음 | `#1A1A1A` | 30px | 활성 |
| Secondary | 투명 | `1px solid #FDC915` | `#1A1A1A` | 30px | 기본 |
| Disabled | `#F7F7F7` | `#CCCCCC` | `#AAAAAA` | 30px | 비활성 |

### 3. **입력 폼(Input)**
- 라운드 8px, 테두리 `#EAEAEA`
- 포커스 시 `#FDC915` glow 효과
- 에러 시 테두리 `#FF5A5A`

### 4. **카드(Card)**
- 라운드 12px, 그림자 `rgba(0,0,0,0.05)`
- 내부 여백 16px
- 반응형에서는 한 줄당 1~2개 배치

---

## 🖥️ Admin (PC) 전용 정책

### 1. **레이아웃 구조**
- **좌측 사이드바:** 고정 (메뉴 아이콘 + 텍스트)
- **상단 헤더:** 알림, 사용자 정보, 설정 아이콘 포함
- **본문 영역:** 테이블, 그래프, 카드형 데이터 위주

### 2. **UI 특징**
- 테이블 기반의 데이터 중심 UI
- 다단 구조 (2~3컬럼) 활용 가능
- Hover 효과로 행 강조
- 검색 및 필터는 우측 상단 고정 배치

### 3. **컴포넌트 예시**
- DataTable / Pagination / FilterBox / Modal / Toast / Tooltip
- 색상 강조: Primary Yellow + Deep Blue

---

## 📱 User (WebApp) 전용 정책

### 1. **레이아웃 구조**
- **세로 스크롤 중심** (Single Column)
- **상단:** 로고 및 페이지 타이틀
- **중앙:** 주요 기능 (예: Login, Dashboard, Reward, My Page)
- **하단:** Floating Navigation Bar (5버튼 이하)

### 2. **UX 특징**
- 손가락 터치 기준 버튼 크기 (최소 48x48px)
- 페이지 간 애니메이션 (fade-in/out)
- 핵심 동선: 로그인 → 대시보드 → 해시/보상 조회

### 3. **모바일 전용 컴포넌트**
| 컴포넌트 | 설명 |
|-----------|------|
| Bottom Nav | 홈 / 마이페이지 / 리워드 / 설정 |
| Floating Button | + 버튼 (해시 구매, QR, 공유 등) |
| Toast | 알림 메시지 (3초 표시) |
| Step Modal | 가입 절차, 인증 단계 UI |

---

## ⚙️ 반응형 기준 (Breakpoints)
| 기기 | 기준 해상도 | 특징 |
|-------|--------------|--------|
| Mobile | 360~480px | 단일 컬럼, 하단 내비게이션 |
| Tablet | 768px | 카드형 2단, 텍스트 확장 |
| Desktop | 1280px 이상 | 고정폭 레이아웃, 좌측 메뉴 |

---

## 💡 애니메이션 가이드
- 버튼 클릭 시 `scale(0.96)`
- 페이지 진입 시 fade-in (0.8s)
- Admin 모달 등장 시 slide-up (0.4s)
- WebApp 로고 진입 시 bounce-in 효과 가능

---

## 🔐 접근성 및 UI 일관성
- 컬러 명도 대비율: 최소 4.5:1 이상 유지
- 폰트 크기 최소 12px 이상
- 버튼/폼 요소 모두 키보드 탐색 지원 (Admin)

---

## 📁 디자인 토큰 분리 계획
- `/tokens/colors.json` : 컬러 세트 정의
- `/tokens/typography.json` : 폰트 스타일 정의
- `/tokens/components.json` : 버튼, 카드, 입력폼 등 공통 컴포넌트 규칙

---

**정리 요약:**  
- Admin: 데이터 중심, 다단 구조, PC 최적화  
- User(WebApp): 행동 중심, 반응형 단일 컬럼 구조  
- 공통 컬러: Yellow + White + Dark Gray 조합  
- 컴포넌트 재사용성 극대화 (React 기반 적용 가능)

