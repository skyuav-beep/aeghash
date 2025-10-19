# HashDam API v1

API Document for HashDam Pool

### Ver 1.0 (2025-08-15)

- 문서변경내역
    
    
    | 일자 | Version | 변경내용 |
    | --- | --- | --- |
    | 2025-08-15 | 1.0 | 최초작성 |
    |  |  |  |
    |  |  |  |

### API 목록

- Project API
    
    
    | No. | 작업명 | 요청구분 | Method Type | Comment |
    | --- | --- | --- | --- | --- |
    | 1 |  프로젝트 정보 | projectInfo | POST |  |
- Hash API
    
    
    | No. | 작업명 | 요청구분 | Method Type | Comment |
    | --- | --- | --- | --- | --- |
    | 1 | 해시 내역 | hashBalance | POST |  |
    | 2 | 해시크레딧 충전 | hashCreditCharge | POST |  |
    | 3 | 해시크레딧 충전 내역 | hashCreditChargeHistory | POST |  |
    | 4 | 해시파워 전환 | hashPowerSwap | POST |  |
    | 5 | 해시파원 전환 내역 | hashPowerSwapHistory | POST |  |
- Hash Rate API
    
    
    | No. | 작업명 | 요청구분 | Method Type | Comment |
    | --- | --- | --- | --- | --- |
    | 1 | 일자별 해시율 | hashRateDaily | POST |  |
    | 2 | 최근 해시율 | hashRateRecently | POST |  |
    | 3 | 최근  1Mh/s 단위 해시율 | hashRateRecentlyMega | POST | MH/s |
- Profit API
    
    
    | No. | 작업명 | 요청구분 | Method Type | Comment |
    | --- | --- | --- | --- | --- |
    | 1 | 일자별 채굴 내역  | profitDaily | POST |  |
    | 2 | 일자별 1Mh/s 채굴 내역 | profitDailyMega | POST | MH/s |
- Asset API
    
    
    | No. | 작업명 | 요청구분 | Method Type | Comment |
    | --- | --- | --- | --- | --- |
    | 1 | 자산 내역 | assetBalance | POST |  |
    | 2 | 자산 인출 내역  | assetWithdrawHistory | POST |  |
    | 3 | 자산 인출 요청 | assetWithdrawRequest | POST |  |

### Introduction

- 기본 정보
    - API URL
        - `https://api.pool.hashdam.com/v1`
        - API 사용자에게 제공된 문서의 서비스 URL 정보를 참조
    - HTTP Header (Authorization Key)
        - Method : POST
        - Key Name : `X-HASHDAM-Key`
        - Value : `••••••`
    - Request Message body
        - Type:  Raw
        - Content Type : application/json
    - Response/Callback Message body
        - Type:  Raw
        - Content Type : application/json
    - Request 예시
        
        ```json
        POST /v1 HTTP/1.1
        Host: api.pool.hashdam.com
        Content-Type: application/json
        X-HASHDAM-Key: ••••••
        Content-Length: *
        
        {
            "method": "{METHOD_NAME}",
            "{KEY_1}": "{VALUE_1}",
            "{KEY_2}": "{VALUE_2}",
            ...
        }
        ```
        
    - Response 예시
        
        ```json
        // Success
        {
            "code": 0,
            "data": {..},
            "message": "{RESULT_MESSAGE}"
        }
        
        // Failed
        {
            "code": 1,
            "message": "{ERROR_MESSAGE}",
        }
        ```
        
- Error 목록
    
    
    | No. | Message | Description |
    | --- | --- | --- |
    | 1 | Not Found API Key | HTTP Header에서 API Key가 없음 |
    | 2 | Invalid API Key | API Key가 올바르지 않음 |
    | 3 | Invalid access from an unauthorized IP Address | 호출한 Remote IP에 대한 사용권한이 없음. API Key 단위로 권한이 관리됨 |
    | 4 | No API Permission | 호출한 Method에 사용권한이 없음. API Key 단위로 권한이 관리됨 |
    |  |  |  |
    |  |  |  |
    

### S**pecifications**

- Project API
    - 프로젝트 정보 (Project Information)
        
        ```
        - 프로젝트 정보 조회.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | projectInfo |
            - Message body
                
                ```json
                {
                    "method": "projectInfo"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | projectName | string | 프로젝트 이름 |  |  |
                | coinExAccount | string | CoinEx 계정 (E-mail) |  |  |
                | createAt | int | 데이터  생성일시 | Not Null | UTC+0, Unix epoch time |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "projectName": "HashDam",
                        "coinExAccount": "email@gmail.com",
                        "createAt": 1755388800000
                    }
                }
                ```
                
        
    
- Hash API
    - 해시 내역 (Hash Balance)
        
        ```
        - 해시 내역 조회
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashBalance |
            - Message body
                
                ```json
                {
                    "method": "hashBalance"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | date | string | 해시 내역 일자 | Not Null | UTC+0 |
                | credit | string | 해시 크레딧 잔고 | Not Null |  |
                | power | string | 해시 파워 잔고 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                		    "date": "2025-08-15",
                        "credit": "651.4",
                        "power": "8348.6" 
                    }
                }
                ```
                
        
    - 해시크레딧 충전 (Hash Credit Charge)
        
        ```
        - 해시크레딧 충전
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashCreditCharge |
            | amount | string | 충전 수량 | Not Null |  |
            | from | string | 사용자 지갑 주소 |  |  |
            - Message body
                
                ```json
                {
                    "method": "hashCreditCharge",
                    "amount": "100.0"
                }
                
                // or
                
                {
                    "method": "hashCreditCharge",
                    "amount": "100.0",
                    "from": "0x1234...12345"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object |  |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | chargeId | string | 충전ID | Not Null |  |
                | address | string | 충전 입금 지갑주소 | Not Null |  |
                | amount | string | 충전 수량 | Not Null |  |
                | price | string | 지불 수량 | Not Null |  |
                | coin | string | 지불 코인명 | Not Null | 기본값: USDT
                Binance Network |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                		    "chargeId": "0xfbcbe74206bb48dba03b7f7f78ecab26",
                        "address": "0x5f2a...48213",
                        "amount": "100.0",
                        "price": "177.8",
                        "coin": "USDT"
                    }
                }
                ```
                
        
    - 해시크레딧 충전 내역 (Hash Credit Charge History)
        
        ```
        - 해시크레딧 충전 내역
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashCreditChargeHistory |
            | page | int | 요청 페이지 번호 |  | 기본값: 1 |
            | limit | int | 페이지당 데이터 수량 |  | 기본값: 10, 범위: 1~1000 |
            | startDate | string | 데이터 시작일자  |  | ”YYYY-MM-DD” |
            | endDate | string | 데이터 종료일자  |  | “YYYY-MM-DD” |
            | sort | boolean | 데이터 일자별 정렬  |  | 기본값: true (내림차순) |
            | chargeId | string | 해시크레딧 충전 ID |  |  |
            - Message body
                
                ```json
                {
                    "method": "hashCreditChargeHistory"
                }
                
                // or
                
                {
                    "method": "hashCreditChargeHistory",
                    "page": 2,
                    "limit": 20,
                    "startDate": "2025-07-01",  // ”YYYY-MM-DD”
                    "endDate": "2025-07-31",    // ”YYYY-MM-DD”
                    "sort": false              // true(내림차순), false(오름차순)
                }
                
                // or
                
                {
                    "method": "hashCreditChargeHistory",
                    "chargeId": "0xfbcbe74206bb48dba03b7f7f78ecab23"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 페이지 데이터 배열 |  |  |
            | pagination | object | 페이징 처리 정보 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | chargeId | string | 해시크레딧 충전 ID | Not Null |  |
                | from | string | 충전 출금 지갑주소 |  |  |
                | to | string | 충전 입금 지갑주소 | Not Null |  |
                | amount | string | 충전 수량 | Not Null |  |
                | price | string | 지불 수량 | Not Null |  |
                | coin | string | 지불 코인명 | Not Null |  |
                | credit | string | 충전후 해시 크레딧 잔액 |  |  |
                | status | string | 충전 상태 | Not Null |  |
                | createAt | int | 충전 요청 일시 | Not Null | UTC+0, Unix epoch time |
                | updateAt | int | 충전 확인 일시 |  | UTC+0, Unix epoch time |
            - Pagination object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | totalPage | int | 전체 페이지 크기 | Not Null |  |
                | total | int | 전체 데이터 크기 | Not Null |  |
                | currentPage | int | 페이지 번호 | Not Null |  |
                | count | int | 페이지 데이터 크기  | Not Null |  |
                | hasNext | boolean | 다음 페이지 여부 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,		    
                    "data": [
                        {
                            "chargeId": "0xfbcbe74206bb48dba03b7f7f78ecab23",
                            "to": "0x5f2a...48215",
                            "amount": "500.0",
                            "price": "889",
                            "coin": "USDT",
                            "credit": "500.0",
                            "status": "pending",
                            "createAt": 1751976817212
                        },
                        {
                            "chargeId": "0xfbcbe74206bb48dba03b7f7f78ecab22",
                            "from": "0x4821....35f2a",
                            "to": "0x5f2a...48214",
                            "amount": "300.0",
                            "price": "533.4",
                            "coin": "USDT",
                            "credit": "500.0",
                						"status": "completed",
                            "createAt": 1751976813212,
                            "updateAt": 1751976823212
                        },
                        {
                            "chargeId": "0xfbcbe74206bb48dba03b7f7f78ecab21",
                            "from": "0x4821....35f2a",
                            "to": "0x5f2a...48213",
                            "amount": "200.0",
                            "price": "355.6",
                            "coin": "USDT",
                            "credit": "0.0",
                            "status": "completed",
                            "createAt": 1751976810212,
                            "updateAt": 1751976820212
                        }
                    ],
                    "pagination": {
                        "totalPage": 1,
                		    "total": 3,
                		    "currentPage": 1,
                		    "count": 3,
                		    "hasNext": false
                    }
                }
                ```
                
        
    - 해시파워 전환 (Hash Power Swap)
        
        ```
        - 해시파워 전환
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashPowerSwap |
            | amount | string | 전환 수량 | Not Null |  |
            - Message body
                
                ```json
                {
                    "method": "hashPowerSwap",
                    "amount": "100.0"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object |  |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | swapId | string | 전환ID | Not Null |  |
                | amount | string | 전환 수량 | Not Null |  |
                | credit | string | 전환후 해시 크레딧 잔액 | Not Null |  |
                | power | string | 전환후 해시 파워 잔액 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                		    "swapId": "0xfbcbe74206bb48dba03b7f7f78ecab26",
                        "amount": "500.0",
                        "credit": "245.0",
                        "power": "892.5"
                    }
                }
                ```
                
        
    - 해시파워 전환 내역 (Hash Power Swap History)
        
        ```
        - 해시파워 전환 내역
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashPowerSwapHistory |
            | page | int | 요청 페이지 번호 |  | 기본값: 1 |
            | limit | int | 페이지당 데이터 수량 |  | 기본값: 10, 범위: 1~1000 |
            | startDate | string | 데이터 시작일자  |  | ”YYYY-MM-DD” |
            | endDate | string | 데이터 종료일자  |  | “YYYY-MM-DD” |
            | sort | boolean | 데이터 일자별 정렬  |  | 기본값: true (내림차순) |
            | swapId | string | 해시파워 전환 ID |  |  |
            - Message body
                
                ```json
                {
                    "method": "hashPowerSwapHistory"
                }
                
                // or
                
                {
                    "method": "hashPowerSwapHistory",
                    "page": 2,
                    "limit": 20,
                    "startDate": "2025-07-01",  // ”YYYY-MM-DD”
                    "endDate": "2025-07-31",    // ”YYYY-MM-DD”
                    "sort": false               // true(Ascending), false(Decending)
                }
                
                // or
                
                {
                    "method": "hashPowerSwapHistory",
                    "swapId": "0xfbcbe74206bb48dba03b7f7f78ecab23"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 페이지 데이터 배열 |  |  |
            | pagination | object | 페이징 처리 정보 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | swapId | string | 해시파워 전환 ID | Not Null |  |
                | amount | string | 전환 수량 | Not Null |  |
                | credit | string | 전환후 해시 크레딧 잔액 |  |  |
                | power | string | 전환후 해시 파워 잔액 |  |  |
                | setDate | string | 해시 파워 시작일 |  |  |
                | endDate | string | 해시 파워 종료일 |  |  |
                | period | string | 해시 파워 기간 (year) |  |  |
                | status | string | 전환 상태 | Not Null |  |
                | createAt | int | 전환 요청 일시 | Not Null | UTC+0, Unix epoch time |
                | updateAt | int | 전환 확인 일시 |  | UTC+0, Unix epoch time |
            - Pagination object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | totalPage | int | 전체 페이지 크기 | Not Null |  |
                | total | int | 전체 데이터 크기 | Not Null |  |
                | currentPage | int | 페이지 번호 | Not Null |  |
                | count | int | 페이지 데이터 크기  | Not Null |  |
                | hasNext | boolean | 다음 페이지 여부 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,    
                    "data": [
                        {
                            "swapId": "0xfbcbe74206bb48dba03b7f7f78ecab23",
                            "amount": "500.0",
                            "period": "3",
                            "status": "pending",
                            "createAt": 1751976817212
                        },
                        {
                            "swapId": "0xfbcbe74206bb48dba03b7f7f78ecab22",
                            "amount": "200.0",
                            "credit": "0.0",
                            "power": "500.0",
                            "setDate": "2025-08-15",
                            "endDate": "2028-08-14",
                            "period": "3",
                						"status": "completed",
                            "createAt": 1751976813212,
                            "updateAt": 1751976823212
                        },
                        {
                            "swapId": "0xfbcbe74206bb48dba03b7f7f78ecab21",
                            "amount": "200",
                            "credit": "300.0",
                            "power": "200.0",
                            "setDate": "2025-08-15",
                            "endDate": "2028-08-14",
                            "period": "3",
                            "status": "completed",
                            "createAt": 1751976810212,
                            "updateAt": 1751976820212
                        }
                    ],
                    "pagination": {
                	      "totalPage": 1,
                		    "total": 3,
                		    "currentPage": 1,
                		    "count": 3,
                		    "hasNext": false
                    }
                }
                ```
                
        
    
- Hash Rate API
    - 일자별 해시율 (Daily Hash Rate)
        
        ```
        - 사용자의 일자별 Hashrate 조회.
        - 데이터는 1일 단위로 UTC+0 시간대를 기준하여 0시에 생성된다.
        - 오늘 데이터는 0시 부터 24시간이 지난 내일(D+1) 0시 이후부터 조회 할 수 있다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashRateDaily |
            | date | string | 요청 데이터 일자 |  | UTC+0, Default : 최근 데이터 |
            - Message body
                
                ```json
                {
                    "method": "hashRateDaily"
                }
                
                // or
                
                {
                    "method": "hashRateDaily",
                    "date": "2025-08-15"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object |  |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | date | string | 데이터 일자 | Not Null | UTC+0 |
                | hashRate | string | 채굴 해시레이트 (Per Project) | Not Null |  |
                | hashRateMega | string | 메가 당 채굴 해시레이트 (Per Mega) | Not Null |  |
                | efficiency | string | 채굴 효율(%) | Not Null |  |
                | reject | string | 채굴 Reject 비율(%) | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "date": "2025-07-15",
                        "hashRate": "4385.87906934",
                        "hashRateMega": "0.95467644",
                        "efficiency": "95.47",
                        "reject": "0.43"
                    }
                }
                ```
                
        
    - 최근 해시율 (Recently Hash Rate)
        
        ```
        - 사용자의 최근 Hashrate 조회
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashRateRecently |
            - Message body
                
                ```json
                {
                    "method": "hashRateRecently"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | timestamp | int | 데이터  생성일시 | Not Null | UTC+0, Unix epoch time |
                | hashRate24h | string | 최근 24시간 채굴 해시레이트 (Mh/s) | Not Null |  |
                | hashRate1h | string | 최근 1시간 채굴 해시레이트 (Mh/s) | Not Null |  |
                | hashRate10m | string | 최근 10분 채굴 해시레이트 (Mh/s) | Not Null |  |
                | efficiency | string | 채굴 효율(%, 24h) | Not Null |  |
                | reject | string | 채굴 Reject 비율(%) | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "timestamp": 1757061666000,
                        "hashRate24h": "8060.70106795",
                        "hashRate1h": "8061.60789429",
                        "hashRate10m": "7905.60681733",
                        "efficiency": "96.55",
                        "reject": "0.37"
                    }
                }
                ```
                
        
    - 1Mh/s 단위 최근 해시율 (Recently Hash Rate per 1 Mh/s)
        
        ```
        - 1mh/s 당 최근 Hash Rate 조회
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | hashRateRecentlyMega |
            - Message body
                
                ```json
                {
                    "method": "hashRateRecentlyMega"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object |  |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | timestamp | int | 데이터  갱신일시 | Not Null | UTC+0, Unix epoch time |
                | hashRate24h | string | 최근 24시간 채굴 해시레이트 (Mh/s) | Not Null |  |
                | hashRate1h | string | 최근 1시간 채굴 해시레이트 (Mh/s) | Not Null |  |
                | hashRate10m | string | 최근 10분 채굴 해시레이트 (Mh/s) | Not Null |  |
                | efficiency | string | 채굴 효율(%, 24h) | Not Null |  |
                | reject | string | 채굴 Reject 비율(%) | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "timestamp": 1757061959000,
                        "hashRate24h": "0.96359258",
                        "hashRate1h": "0.96725855",
                        "hashRate10m": "0.98756358",
                        "efficiency": "96.35",
                        "reject": "0.19"
                    }
                }
                ```
                
    
- Profit API
    - 일자별 채굴 내역 (Daily Profit)
        
        ```
        - 사용자의 일자별 채굴 내역 조회.
        - 데이터는 1일 단위로 UTC+0 시간대를 기준하여 0시에 생성된다.
        - 오늘 데이터는 0시 부터 24시간이 지난 내일(D+1) 0시 이후부터 조회 할 수 있다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | profitDaily |
            | date | string | 요청 데이터 일자 |  | UTC+0, Default : 최근 데이터 |
            - Message body
                
                ```json
                {
                    "method": "profitDaily"
                }
                
                // or
                
                {
                    "method": "profitDaily",
                    "date": "2025-08-16"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | date | string | 데이터 일자 | Not Null | UTC+0 |
                | profit | object | 자산 이름 및 채굴 내역 | Not Null |  |
            - Profit object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | total | string | 채굴 수량 | Not Null |  |
                | price | string | 데이터 일자기준 최종시세 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "date": "2025-08-17",
                        "profit": {
                            "LTC": {
                                "total": "0.010387994652",
                                "price": "120.73"
                            },
                            "DOGE": {
                                "total": "39.377317869494",
                                "price": "0.234496"
                            },
                            "BELLS": {
                                "total": "0.008770512222",
                                "price": "0.174374"
                            },
                            "LKY": {
                                "total": "0.012861258186",
                                "price": "0.259606"
                            },
                            "PEP": {
                                "total": "44.412072337047",
                                "price": "0.00057683"
                            },
                            "JKC": {
                                "total": "0.038606908856",
                                "price": "0.032118"
                            },
                            "DINGO": {
                                "total": "38.239120092973",
                                "price": "0.0000624589"
                            },
                            "SHIC": {
                                "total": "290.930496398786",
                                "price": "0.0000318463"
                            }
                        }
                    }
                }
                ```
                
        
    - 일자별 1Mh/s 채굴 내역 (Daily Profit per Mh/s)
        
        ```
        - 사용자의 일자별 1Mh/s 단위 채굴 내역 조회.
        - 데이터는 1일 단위로 UTC+0 시간대를 기준하여 0시에 생성된다.
        - 오늘 데이터는 0시 부터 24시간이 지난 내일(D+1) 0시 이후부터 조회 할 수 있다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | profitDailyMega |
            | date | string | 요청 데이터 일자 |  | UTC+0, Default : 최근 데이터 |
            - Message body
                
                ```json
                {
                    "method": "profitDailyMega"
                }
                
                // or
                
                {
                    "method": "profitDailyMega",
                    "date": "2025-08-16"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | date | string | 데이터 일자 (UTC+0) | Not Null |  |
                | profit | object | 자산 이름 및 채굴 내역 | Not Null |  |
            - Profit object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | total | string | 채굴 수량 | Not Null |  |
                | price | string | 데이터 일자기준 최종시세 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "date": "2025-08-17",
                        "profit": {
                            "LTC": {
                                "total": "0.010387994652",
                                "price": "120.73"
                            },
                            "DOGE": {
                                "total": "39.377317869494",
                                "price": "0.234496"
                            },
                            "BELLS": {
                                "total": "0.008770512222",
                                "price": "0.174374"
                            },
                            "LKY": {
                                "total": "0.012861258186",
                                "price": "0.259606"
                            },
                            "PEP": {
                                "total": "44.412072337047",
                                "price": "0.00057683"
                            },
                            "JKC": {
                                "total": "0.038606908856",
                                "price": "0.032118"
                            },
                            "DINGO": {
                                "total": "38.239120092973",
                                "price": "0.0000624589"
                            },
                            "SHIC": {
                                "total": "290.930496398786",
                                "price": "0.0000318463"
                            }
                        }
                    }
                }
                ```
                
    
- Asset API
    - 자산 내역 (Asset Balance)
        
        ```
        - 자산 내역 조회.
        - 데이터는 1일 단위로 UTC+0 시간대를 기준하여 0시에 생성된다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | assetBalance |
            - Message body
                
                ```json
                {
                    "method": "assetBalance"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 처리 데이터 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | date | string | 자산 내역 일자 |  | UTC+0 |
                | asset | object | 자산 이름 및 잔고 |  |  |
            - Asset object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | balance | string | 자산 잔고 |  |  |
                | available | string | 사용가능 자산 잔고  |  |  |
                | locked | string | 동결 자산 잔고 |  |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                        "date": "2025-08-15",
                        "asset": {
                            "LTC": {
                                "balance": "0.56180567",
                                "available": "0.56180567"
                            },
                            "DOGE": {
                                "balance": "2069.43760368",
                                "available": "2069.43760368"
                            },
                            "BELLS": {
                                "balance": "0.50355155",
                                "available": "0.50355155"
                            },
                            "LKY": {
                                "balance": "0.89606043",
                                "available": "0.89606043"
                            },
                            "PEP": {
                                "balance": "2599.87337945",
                                "available": "2599.87337945"
                            },
                            "JKC": {
                                "balance": "2.02289527",
                                "available": "2.02289527"
                            },
                            "DINGO": {
                                "balance": "1906.15060841",
                                "available": "1906.15060841"
                            },
                            "SHIC": {
                                "balance": "14805.89117916",
                                "available": "14805.89117916"
                            }
                        }
                    }
                }
                ```
                
        
    - 자산 인출 내역 (Asset Withdrawal History)
        
        ```
        - 자산 인출 내역 조회.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | assetWithdrawHistory |
            | page | int | 요청 페이지 번호 |  | 기본값: 1 |
            | limit | int | 페이지당 데이터 수량 |  | 기본값: 10, 범위: 1~1000 |
            | coin | string | 자산명  |  | LTC, DOGE, BELLS, LKY, PEP, JKC, DINGO, SHIC |
            | startDate | string | 데이터 시작일자  |  | ”YYYY-MM-DD” |
            | endDate | string | 데이터 종료일자  |  | “YYYY-MM-DD” |
            | sort | boolean | 데이터 일자별 정렬  |  | 기본값: true (내림차순) |
            | withdrawId | string | 인출 요청 ID |  |  |
            - Message body
                
                ```json
                {
                    "method": "assetWithdrawHistory"
                }
                
                // or
                
                {
                    "method": "assetWithdrawHistory",
                    "page": 2,
                    "limit": 20,
                    "coin": "DOGE",             // LTC, DOGE, BELLS, LKY, PEP, JKC, DINGO, SHIC
                    "startDate": "2025-07-01",  // ”YYYY-MM-DD”
                    "endDate": "2025-07-31",    // ”YYYY-MM-DD”
                    "sort": false              // true(내림차순), false(오름차순)
                }
                
                // or
                
                {
                    "method": "assetWithdrawHistory",
                    "withdrawId": "0xfc3da061db134d759d889055980916d0"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | object | 페이지 데이터 배열 |  |  |
            | pagination | object | 페이징 처리 정보 |  |  |
            - Data object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | withdrawId | string | 인출 요청 ID | Not Null |  |
                | coin | string | 자산명  | Not Null |  |
                | amount | string | 인출 수량 | Not Null |  |
                | fee | string | 인출 수수료 | Not Null |  |
                | address | string | 인출 수신 주소 | Not Null |  |
                | type | string | 인출 유형 | Not Null |  |
                | message | string | 인출 처리 메세지 |  |  |
                | status | string | 인출 상태 | Not Null |  |
                | createAt | int | 데이터  생성일시 | Not Null | UTC+0, Unix epoch time |
                | updateAt | int | 데이터  수정일시 |  | UTC+0, Unix epoch time |
            - Pagination object
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | totalPage | int | 전체 페이지 크기 | Not Null |  |
                | total | int | 전체 데이터 크기 | Not Null |  |
                | currentPage | int | 페이지 번호 | Not Null |  |
                | count | int | 페이지 데이터 크기  | Not Null |  |
                | hasNext | boolean | 다음 페이지 여부 | Not Null |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": [
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "BELLS",
                            "amount": "5.46969956",
                            "fee": "0.01",
                            "address": "aaa@gmail.com",
                            "type": "interUser",
                            "message": "Not found or Unsupported coin symbol",
                            "status": "failed",
                            "createAt": 1751976817212,
                            "updateAt": 1751976827393
                        },
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "PEP",
                            "amount": "2246.88369794",
                            "fee": "10",
                            "address": "aaa@gmail.com",
                            "type": "interUser",
                            "status": "canceled",
                            "createAt": 1751972893804,
                            "updateAt": 1751973232938
                        },
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "DINGO",
                            "amount": "635.57095676",
                            "fee": "0",
                            "address": null,
                            "type": "interUser",
                            "status": "completed",
                            "createAt": 1748995200000
                        },
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "JKC",
                            "amount": "1.52044549",
                            "fee": "0",
                            "address": null,
                            "type": "interUser",
                            "status": "completed",
                            "createAt": 1748995200000
                        },
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "PEP",
                            "amount": "1839.71779991",
                            "fee": "0",
                            "address": null,
                            "type": "interUser",
                            "status": "completed",
                            "createAt": 1748995200000
                        },        
                        {
                            "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",
                            "coin": "DINGO",
                            "amount": "1019.44589627",
                            "fee": "0",
                            "address": null,
                            "type": "interUser",
                            "status": "completed",
                            "createAt": 1746057600000
                        }
                    ],
                    "pagination": {
                        "totalPage": 2,
                			  "total": 16,
                			  "currentPage": 2,
                			  "count": 6,
                			  "hasNext": false
                    }
                }
                ```
                
        
    - 자산 인출 요청 (Asset Withdrawal Request)
        
        ```
        - 자산 출금 요청
        - 자산 출금은 HashDam으로부터 고객사 어카운트로 출금되는 것이기에 반드시 사전에 주소를 등록해야 한다. 혹은 
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | assetWithdrawRequest |
            | coin | string | 자산명 | Not Null | LTC, DOGE, BELLS, LKY, PEP, JKC, DINGO, SHIC |
            | amount | string | 인출 요청 수량 | Not Null |  |
            - Message body
                
                ```json
                {
                    "method": "assetWithdrawRequest",
                    "coin": "PEP",
                    "amount": "100.0"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | code | int | 처리 결과 | Not Null | 0: 성공, 1: 오류 |
            | message | string | 처리 결과 메세지 |  | 오류 발생시 상세 메세지 |
            | data | json | 처리 데이터 |  |  |
            - Data Json
                
                
                | 이름 | 타입 | 설명 | 필수 | 비고 |
                | --- | --- | --- | --- | --- |
                | withdrawId | string | 인출 요청 ID |  |  |
                | coin | string | 자산명 |  |  |
                | amount | string | 인출 요청 수량 |  |  |
            - Message body
                
                ```json
                {
                    "code": 0,
                    "data": {
                		    "withdrawId": "0xd1b1c413513c40e49ec51da9b7dc7d1b",       
                        "coin": "PEP",
                        "amount": "100.0"
                    }
                }
                ```
                
        
    

### CoinEx API

- API Introduction **[[LINK](https://docs.coinex.com/api/v2/)]**
    - Authentication **[[LINK](https://docs.coinex.com/api/v2/authorization)]**
    - Rate Limit [[**LINK**](https://docs.coinex.com/api/v2/rate-limit)]
    
- 자산 인출 요청 (**Submit Withdrawal Request**) **[[LINK](https://docs.coinex.com/api/v2/assets/deposit-withdrawal/http/withdrawal)]**
    
    ```
    - This endpoint requires signature. For specific signature rules, please refer to **Authentication**
    - This endpoint will trigger rate limit. For specific rules, please refer to **Rate Limit**.
    ```
    
    ✏️ 자산인출전 반드시 CoinEX 계정에 출금 주소가 등록되어 있어야 합니다.
    
    - 요청 (Request)
        
        POST `https://api.coinex.com/v2/assets/withdraw`
        
        | 이름 | 타입 | 필수 | 설명 |
        | --- | --- | --- | --- |
        | ccy | string | Not Null | Currency name |
        | chain | string |  | Chain name. Required for On-chain, not required for inter-user transfer |
        | to_address | string | Not Null | Withdrawal address.
        The withdrawal address needs to be added to the IP whitelist via [Developer Console](https://www.coinex.com/en/apikey). Please add the address to your whitelist, before making on-chain withdrawals or inter-user transfers. |
        | withdraw_method | string |  | Withdrawal methods (On-chain or inter-user transfer). 
        Default as on-chain withdrawal**On-chain withdrawal (on_chain)**.Applicable to withdrawals from CoinEx website**Inter-user transfer (inter_user)**. Applicable to transfers between CoinEx users, no withdrawal fee or on-chain confirmation required, instant arrival. |
        | memo | string |  | A memo is required for certain currency deposits. If not, this field will not be returned. |
        | amount | string | Not Null | Withdrawal amount.
        Withdrawals lower than [minimum withdrawal amount](https://www.coinex.com/en/fees?type=deposit%5C&market=normal) cannot be completed[Withdrawal fee](https://www.coinex.com/en/fees?type=deposit%5C&market=normal) will be charged for each request, please reserve sufficient trading fee |
        | fee_ccy | string |  | Trading fee currency |
        | extra | object |  | If it is a withdrawal from the `KDA` chain, you need to append the `chain_id` field to the extra field. Please refer to the request example below. |
        | remark | string |  | Withdrawal note |
        - Message body
            
            ```json
            {
                "ccy": "USDT",
                "chain": "CSC",
                "to_address": "0x3886be3128DEF4dEC006116acaf21750c0138Ad6",
                "extra": {
                    "chain_id": "0"
                }
                "amount": "1"
            }
            ```
            
        
    - 응답 (Response)
        
        
        | 이름 | 타입 | 설명 |
        | --- | --- | --- |
        | withdraw_id | int | Withdrawal unique ID |
        | created_at | int | Withdrawal application time |
        | ccy | string | Currency name |
        | chain | string | Chain name |
        | withdraw_method | string | Withdrawal methods (On-chain or inter-user transfer) |
        | memo | string | A memo is required for certain currency deposits. If not, return an empty value. |
        | amount | string | Withdrawal amount |
        | fee_ccy | string | Trading fee currency |
        | actual_amount | string | Actual withdrawal amount |
        | tx_fee | string | Withdrawal fee |
        | tx_id | string | Tx hash |
        | to_address | string | Withdrawal address |
        | confirmation | int | Number of confirmation |
        | explorer_address_url | string | Address link in blockchain explorer |
        | explorer_tx_url | string | Transaction link in blockchain explorer |
        | status | string | Withdrawal status |
        | remark | string | Remark |
        - Message body
            
            ```json
            {
                "code": 0,
                "data": {
                    "withdraw_id": 206,
                    "created_at": 1524228297321,
                    "ccy": "BCH",
                    "chain": "",
                    "amount": "1.00000000",
                    "fee_ccy": "BCH",        
                    "actual_amount": "1.00000000",
                    "withdraw_method": "inter_user",
                    "memo": "",
                    "tx_fee": "0",
                    "tx_id": "",
                    "to_address": "1KAv3pazbTk2JnQ5xTo6fpKK7p1it2RzD4",
                    "confirmations": 0,
                    "explorer_address_url": "https://www.coinex.net/address/0xefabcc016aee2cd205139899d1cac0b672659fe8",
                    "explorer_tx_url": "https://www.coinex.net/tx/",
                    "status": "audit",
                    "remark": ""
                },
                "message": "OK"
            }
            ```