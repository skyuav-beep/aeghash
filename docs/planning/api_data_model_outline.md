# API & 데이터 모델 초안 (Codex Task1)

## 참조 문서
- `spec.md`
- `HashDam API v1.md`
- `MBlock Docs v1.4.md`
- `docs/planning/platform_system_plan.md`
- `docs/planning/uiux_task_breakdown.md`

## 1. 서비스 경계
- **Auth Service**: 소셜 로그인(Google/Kakao/Apple), Turnstile, 2FA, 세션·토큰 관리.
- **User Service**: 프로필, 알림 설정, 출금 화이트리스트, 보안 이벤트 로그.
- **Wallet Service**: 내부 포인트 지갑 + 외부(BNB) 지갑, 출금 승인 플로우, 위험 탐지.
- **Mining Service**: HashDam 채굴 데이터 수집, 해시/보너스 계산, 채굴 ETL 파이프.
- **Commerce Service**: 쇼핑몰 주문, PV 계산, 가맹점 정산, QR 결제.
- **Bonus Engine**: 유니레벨/바이너리 조직 구조, 보너스 배치, 정산 큐.
- **Admin Console**: 조직도, 정산/출금 승인, KPI 모니터링, 감사 로그.

## 2. 핵심 데이터 모델 초안

### 2.1 Users
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | UUID | 회원 고유 식별자 |
| `email` | string | 이메일(Unique) |
| `nickname` | string | 표기명 |
| `phone_number` | string | 국제번호 포함 |
| `referral_code` | string | 추천 코드(자동 생성) |
| `sponsor_id` | UUID | 추천 사용자 ID |
| `security_settings` | json | 2FA, 화이트리스트 등 |
| `roles` | array[string] | user/admin/finance 등 |
| `created_at` | datetime | 가입 일시 |

### 2.2 Wallets
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | UUID | 지갑 ID |
| `user_id` | UUID | 소유자 |
| `type` | enum | `POINT`, `CRYPTO` |
| `chain` | string | BNB, 기타 네트워크 |
| `address` | string | 외부 지갑 주소 (MBlock 생성) |
| `balance` | decimal | 현재 잔액 |
| `status` | enum | `ACTIVE`, `SUSPENDED` |
| `meta` | json | 지갑키 참조값, MBlock token 등 |
| `created_at` | datetime | 생성 일시 |

### 2.3 Transactions
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | UUID | 트랜잭션 ID |
| `wallet_id` | UUID | 지갑 참조 |
| `type` | enum | `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `BONUS` |
| `amount` | decimal | 금액 |
| `status` | enum | `PENDING`, `APPROVED`, `REJECTED`, `FAILED` |
| `external_txid` | string | MBlock/HashDam 연계 식별자 |
| `initiated_by` | UUID | 사용자/관리자 ID |
| `metadata` | json | API 응답, 실패 이유 등 |
| `created_at` | datetime | 생성 |
| `updated_at` | datetime | 상태 변경 |

### 2.4 Mining Hash
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | UUID | 레코드 ID |
| `user_id` | UUID | 사용자 |
| `hash_power` | decimal | 현재 해시파워 |
| `hash_credit` | decimal | 잔여 크레딧 |
| `hash_rate` | decimal | 실시간 해시율 |
| `coin` | string | 코인 심볼 (LTC, DOGE 등) |
| `last_sync_at` | datetime | HashDam 데이터 동기화 시점 |
| `source_payload` | json | HashDam API 원본 |

### 2.5 Orders & PV
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `order_id` | UUID | 주문 ID |
| `user_id` | UUID | 구매자 |
| `merchant_id` | UUID | 가맹점 |
| `total_amount` | decimal | 결제 금액 |
| `pv_amount` | decimal | PV |
| `status` | enum | `PENDING`, `PAID`, `CANCELLED`, `REFUNDED` |
| `channel` | enum | `ONLINE`, `OFFLINE_QR`, `POS` |
| `created_at` | datetime | 주문 시각 |

### 2.6 Organization Nodes
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `node_id` | UUID | 트리 노드 |
| `user_id` | UUID | 회원 참조 |
| `tree_type` | enum | `UNILEVEL`, `BINARY` |
| `position` | string | 유니레벨 Depth 또는 바이너리 좌/우 |
| `parent_node_id` | UUID | 상위 노드 |
| `rank` | enum | 직급 |
| `volume_left` | decimal | (바이너리) 좌측 매출 |
| `volume_right` | decimal | (바이너리) 우측 매출 |
| `center_id` | UUID | 센터 배정 ID |
| `created_at` | datetime | 배치 일시 |

## 3. 외부 API 계약 정리

### 3.1 HashDam (채굴)
- 인증: `X-HASHDAM-Key` 헤더 (문서 기준), IP 화이트리스트. 현재 문서 기준으로는 테스트 시 별도 키 없이 호출 가능하므로 키 값이 제공되기 전까지는 헤더 없이 동작하도록 구현해 둔다.
- 주요 메서드: `hashBalance`, `hashRateDaily`, `profitDaily`, `assetWithdrawRequest`.
- TODO: 실사용 Key/Value 미제공 → 계약 시 비밀 키 확보 및 보안 정책 수립 (`.env.example`에 주석으로 안내).
- 데이터 매핑: 해시 내역, 해시율, 채굴 수익, 자산 잔고를 `Mining Service`와 `Transactions`에 매핑.

### 3.2 MBlock (지갑/결제)
- 인증: `X-MBLOCK-Key`, Wallet Key 기반. (현재 제공: Base URL `https://agent.mblockapi.com/bsc`, Key Value `l3NR5Rz658AoV87N556xHGs8czL13ohjve01JRlncqnSCdTBZUvj0TcngNXAD2o5`)
- 주요 메서드: `requestWallet`, `transferByWalletKey`, `transitByWalletKey`, `balanceOf`.
- Required Value: Key/Value 문서 제공 → 비밀 관리 `.env` + 시크릿 매니저 필요.
- 데이터 매핑: 지갑 생성 시 Wallet meta 저장, 전송 결과를 `Transactions.external_txid`와 연결.

## 4. API 초안 (REST 예시)
- `/api/v1/auth/oauth/callback`
- `/api/v1/users/me`
- `/api/v1/wallets`
- `/api/v1/wallets/{wallet_id}/withdraw`
- `/api/v1/mining/hash`
- `/api/v1/mining/withdraw`
- `/api/v1/orders`
- `/admin/organizations/{tree_type}/{node_id}/kpi`
- `/api/v1/merchants/{merchant_id}/settlements`

## 5. 향후 워크숍 To-Do
- [x] HashDam 응답 스키마 샘플 확보 (`tests/resources/hashdam/*.json`) 및 기본 변환 규칙 초안: 금액/해시 값은 `Decimal`, 날짜는 UTC 기준 `datetime`.
- [x] MBlock Transit Config 항목(수수료, callback) 샘플 (`tests/resources/mblock/*.json`)과 출금 승인 정책 연계 초안 작성: `fee` → 출금 수수료 모델, `callback` → 웹훅 큐 관리.
- [ ] Bonus Engine 입력/출력 스키마 상세화
- [ ] API 버저닝 전략 및 에러 코드 표준 초안 작성
- [ ] 데이터 거버넌스(감사 로그, PII 마스킹) 규칙 문서화

## 6. 참고 리소스
- HashDam 샘플 응답: `tests/resources/hashdam/hash_balance_sample.json`, `tests/resources/hashdam/asset_withdraw_request_sample.json`
- MBlock 샘플 응답: `tests/resources/mblock/balance_of_success.json`, `tests/resources/mblock/transit_config_sample.json`, `tests/resources/mblock/transit_by_wallet_key_success.json`
