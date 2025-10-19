# MBlock Docs - v1.4

API Document for Binance Network

### `API Ver 1.4.0`

- 문서변경내역
    
    
    | API Ver | 변경내용 | 일자 |  |
    | --- | --- | --- | --- |
    | 1.4.0 | 최초작성 | 2025-02-15 |  |
    |  |  |  |  |

### API 목록

- Network API
    
    
    | No. | 작업명 | 요청구분 | Method Type | 지원 Version |
    | --- | --- | --- | --- | --- |
    | 1 | 지갑 잔액 확인 | balanceOf | POST | Ver 1.0.0 |
    | 2 | 전송 내역 확인 | receiptByHash | POST | Ver 1.0.0 |
    | 3 | 지갑 키로 전송 | transferByWalletKey | POST | Ver 1.3.0 |
    | - | 전송 가스비 설정 | gasConfig | POST | 지원예정 |
- Wallet API
    
    
    | No. | 작업명 | 요청구분 | Method Type | 지원 Version |
    | --- | --- | --- | --- | --- |
    | 1 | 지갑 생성 요청 | requestWallet | POST | Ver 1.3.0 |
    | 2 | 지갑 초기화 요청 | refreshWallet | POST | Ver 1.3.0 |
- Transit API
    
    
    | No. | 작업명 | 요청구분 | Method Type | 지원 Version |
    | --- | --- | --- | --- | --- |
    | 1 | Transit 설정 저장 및 조회 | transitConfig | POST | Ver 1.4.0 |
    | 2 | Transit 전송 요청 | transitByWalletKey | POST | Ver 1.4.0 |

### API Docs

- Introduction
    - 기본 정보
        - API URL
            - `https://*.mblockapi.com/bsc`
            - API 사용자에게 제공된 문서의 서비스 URL 정보를 참조
        - HTTP Header (Authorization Key)
            - Method : POST
            - Key Name : `X-MBLOCK-Key`
            - Value : `l3NR5Rz658AoV87N556xHGs8czL13ohjve01JRlncqnSCdTBZUvj0TcngNXAD2o5`
        - Request Message Body
            - Type:  Raw
            - Content Type : application/json
        - Callback Message Body
            - Type:  Raw
            - Content Type : application/json
        - HTTP Request 예시
            
            ```json
            POST /bsc HTTP/1.1
            Host: *.mblockapi.com
            Content-Type: application/json
            X-MBLOCK-Key: ••••••
            Content-Length: *
            
            {
                "method": "{METHOD_NAME}",
                "{KEY_1}": "{VALUE_1}",
                "{KEY_2}": "{VALUE_2}",
                ...
            }
            ```
            
    - Error 목록
        
        
        | No. | Message | Description |
        | --- | --- | --- |
        | 1 | Not Found API Key | HTTP Header에서 API Key가 없음 |
        | 2 | Invalid API Key | API Key가 올바르지 않음 |
        | 3 | Invalid access from an unauthorized IP Address | 호출한 Remote IP에 대한 사용권한이 없음. API Key 단위로 권한이 관리됨 |
        | 4 | No API Permission | 호출한 Method에 사용권한이 없음. API Key 단위로 권한이 관리됨 |
        | 5 | Invalid Wallet Key | Wallet Key 값을 찾을수 없거나 올바르지 않음 |
        | 6 | Unsupported token symbol | Token 이름이 올바르지 않음 |
        | 7 | Transfer volume is required | 전송요청 금액이 올바르지 않음 |
        | 8 | Contract address is incorrect | 요청한 Token Contract가 일치하지 않음 |
        | 9 | Transaction Logs not found | 요청한 Hash의 데이터 중에서 Log가 존재하지 않음 |
        | 10 | Wallet address is incorrect | 지갑 주소가 올바르지 않음 |
        | 11 | Transaction receipt not found | 요청한 Hash의 데이터가 존재하지 않음 |
        | 12 | Request Time out, Transaction receipt not found. | Token 전송 후 전송 결과를 10초가 기다렸지만, 확인 할 수 없음 |
        | 13 | RPCError: {ERROR_MESSAGE}   | Main Network상에서 오류가 발생했음 (상세 메세지가 같이 출력됨) |
        | 14 | Wallet address is incorrect | Wallet Key가 올바르지 않음 |
        | 15 | Wallet address has expired | Wallet Key가 만료되었음 |
        | 16 | Request volume is zero or not enough balance | 요청한 수량이 0 이거나 지갑의 잔고가 부족함 |
        | 17 | Not enough balance | 지갑의 잔고가 부족함 |
        | 18 | Invalid Configuration | 설정값 정보가 올바르지 않음 |
        
    
- Network API
    - 지갑 잔액 확인 (balance Of Contract)
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | balanceOf |
            | contract | string | Token 계약 주소 |  | - Token 계약 주소 지정시 Token의 잔고를 조회
            - Null 값 이면 BNB 잔액을 조회 |
            | address | string | 지갑주소 | Not Null |  |
            - Message Body
                
                ```json
                {
                    "method": "balanceOf",
                    "contract": "0x337610d27c682...........3b107C9d34dDd",
                    "address" : "0x5f2ad8b…...14c648213"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | amount | string | 지갑 잔고 |  |  |
            | message | string | 결과 메세지 |  | 오류 발생시 상세 메세지 |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "amount": "1.0"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
        
    - 전송 내역 확인 (Transaction Receipt)
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | receiptByHash |
            | contract | string | Token 계약 주소 | Not Null | - Token 계약 주소 지정시 Token의 잔고를 조회
            - Null 값 이면 BNB 잔액을 조회 |
            | txid | string | Transaction Hash ID 값 | Not Null |  |
            - Message Body
                
                ```json
                {
                    "method": "receiptByHash",
                    "contract": "0x337610d27c682...........3b107C9d34dDd",
                    "txid" : "0x1eeec26e62c4244667d…......d268e975dfbef21ab318"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | from | string | 전송 지갑 주소 | Not Null |  |
            | to | string | 수신 지갑 주소 | Not Null |  |
            | amount | string | 전송 Token 수량 | Not Null |  |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "from": "0x5f2ad8b…...14c648213",
                        "to": "0x5f2ad8b…...14c648213",
                        "amount": "1.0",
                        "message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
        
    - 지갑키로 전송 (Transfer by Wallet Key)
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | transferByWalletKey |
            | walletKey | string | 전송할 지갑의 walletKey | Not Null |  |
            | contract | string | Token 계약 주소 | Not Null | - 전송할 Token의 계약 주소
            - Null 값 이면 BNB를 전송 |
            | to | string | 수신 지갑 주소 | Not Null |  |
            | amount | string | 전송 수량 | Not Null |  |
            - Message Body
                
                ```json
                {
                    "method": "transferByWalletKey",
                    "walletKey": "097nUePpxA4K0….........38i7x3I8933jcIUD",
                    "contract": "0x337610d27c682...........3b107C9d34dDd",
                    "to": "0x5f2ad8b…...14c648213",
                    "amount": "0.05"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | txid | string | 전송 결과 Hash ID | Not Null |  |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "txid": "0x1eeec26e62c4244667…..........bd268e975dfbef21ab318",
                        "message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
        
    - [지원예정] 전송 가스비 설정 (Gas Config)
    
- Wallet API
    - 지갑키 생성 (Request Wallet Key)
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | requestWallet |
            - Message Body
                
                ```json
                {
                    "method": "requestWallet"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | address | string | 생성된 지갑 주소 | Not Null |  |
            | walletKey | string | 생성된 지갑의 Wallet Key | Not Null |  |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "address": "0x63458854ea289….....75ee9bdb2",
                        "walletKey": "r682g7p3RvP4hg2….........nx69bTG4LBo",
                        "message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
        
    - 지갑키 초기화 (Refresh Wallet Key)
        
        ```
        - 기존 Wallet Key 값을 새로운 값으로 변경하는 기능을 제공한다.
        - 변경 즉시 이전 Wallet Key 값은 사용 할 수 없으며, 응답 데이터에 포함된 Wallet Key 값을 사용해야 한다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | refreshWallet |
            | walletKey | string | 기존에 발급받은 walletKey |  |  |
            - Message Body
                
                ```json
                {
                    "method": "refreshWallet",
                    "walletKey": "r682g7p3RvP4hg2….........nx69bTG4LBo"
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | walletKey | string | 새로운 Wallet Key | Not Null | 기존 Wallet Key를 갱신한 새로운 Wallet Key 값 |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "walletKey": "097nUePpxA4K0….........38i7x3I8933jcIUD",
                        "message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
    
- Transit API
    - Transit 설정 저장 및 조회 (Transit Config)
        
        ```
        - transitByWalletKey 기능에서 사용하는 변수를 서버에 저장 및 조회하는 기능을 제공한다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null | transitConfig |
            | [config](https://www.notion.so/MBlock-Docs-v1-4-19b46c8428cc8088a697fcfef9713e5b?pvs=21) | json | Transit Config 값 |  | - config값이 Null이면 현재 저장된 값을 조회함
            - config값이 Not Null이면 해당 값으로 갱신하고 저장된 값을 조회함 |
            - Message Body
                - 새로운 Config 값 저장
                
                ```json
                {
                    "method": "transitConfig",
                    "config": {
                			"fee": 0.0002,
                			"feeWalletKey": "097nUePpxA4K0….........38i7x3I8933jcIUD",
                			"delay": 5,
                			"count": 2,
                			"callback": "https://domain.com/callback_path"
                		}
                }
                ```
                
                - 현재 Config 값 조회
                
                ```json
                {
                    "method": "transitConfig"
                }
                ```
                
                - 현재 Config 값 초기화
                
                ```json
                {
                    "method": "transitConfig",
                    "config": {}
                }
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | bool | 처리 상태 | Not Null |  |
            | config | json | Transit Config 값 | Not Null |  |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                        "result": true,
                        "config": {
                    			"fee": 0.0002,
                    			"feeWalletKey": "097nUePpxA4K0….........38i7x3I8933jcIUD",
                    			"delay": 5,
                    			"count": 2,
                    			"callback": "https://domain.com/path"
                    		},
                    		"message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                    - 설정된 Config 값이 없는 경우
                    
                    ```json
                    {
                        "result": true,
                        "config": {},
                    		"message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
        
    - Transit 전송 요청 (Transit By Wallet Key)
        
        ```
        - 사용자 지갑에서 수신 지갑으로 토큰을 전송하는 기능을 제공한다.
        - Transit 요청이 시작되면 해당 요청을 식별할수 있는 고유 값을 생성하여 회신하고, 서버는 Transit 작업을 비동기로 수행한다.
        - 사용자 지갑의 잔고를 확인하여 조건에 부합하면 전송을 위한 수수료를 사용자 지갑으로 보내고, 요청시 지정한 수신 지갑으로 해당 토큰의 잔고를 전송한다.
        - 작업 결과는 Config정보의 callback값을 참조하여 처리 결과를 전송(HTTP/REST API)한다.
        - transitByWalletKey → config 데이터를 전송하면, 서버에 저장된 Config정보를 무시하고 해당 값으로 Override하여 사용 할 수 있다.
        ```
        
        - 요청 (Request)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | method | string | 요청구분 | Not Null |  |
            | walletKey | string | 사용자 지갑의 walletKey | Not Null |  |
            | contract | string | 토큰 계약 주소 | Not Null | 전송할 Token의 계약 주소 |
            | to | string | 수신 지갑 주소 | Not Null |  |
            | amount | string | 이체 수량 |  | Null 이면 사용자 지갑의 전체 토큰 수량을 적용 |
            | [config](https://www.notion.so/MBlock-Docs-v1-4-19b46c8428cc8088a697fcfef9713e5b?pvs=21) | json | 수동 Transit Config 값 |  | - Null 이면 서버에 저장된 config 값을 적용
            - Not Null 이면 해당 요청에 전송된 config 값을 적용
            - 일부 항목만 설정시 해당 항목에 대해서만 적용되며, 그외 항목은 서버에 저장된 config 값을 적용 |
            - Message Body
                - 서버 Config 값을 사용하여 전송
                
                ```json
                {
                		"method": "transitByWalletKey",
                		"walletKey" : "097nUePpxA4K0….........38i7x3I8933jcIUD",
                		"contract": "0x0be962843f4Bc6dA….......276D8473BeC0A0630",
                		"to": "0x5f2ad8b…...14c648213",
                		"amount": "0.05"
                }
                ```
                
                - 수동으로 Config 값을 설정하여 전송
                
                ```json
                {
                		"method": "transitByWalletKey",
                		"walletKey" : "097nUePpxA4K0….........38i7x3I8933jcIUD",
                		"contract": "0x0be962843f4Bc6dA….......276D8473BeC0A0630",
                		"to": "0x5f2ad8b…...14c648213",
                		"amount": "0.05",
                		"config": {
                			"fee": 0.0002,
                			"callback": "https://domain.com/callback_path"
                		}
                }
                
                위와 같이 전송되면 "fee", "callback" 값만 override 되며, 나머지는 서버 config 값을 사용한다.
                단, 전송되지 않은 나머지 항목이 서버 Config에 Null 값이면 오류가 발생한다.
                ```
                
            
        - 응답 (Response)
            
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | boolean | 처리결과 | Not Null |  |
            | token | string | 해당 요청을 식별하는 값 | Not Null | Order No. 또는 Invoice No. 역할을 하는 값 |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                    		"result": true,
                    		"token": "sdfsdfsdfsdf67…..........bd2sdfsdfsdffsf",
                    		"message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
            
        - 결과전송 (Callback)
            
            ```bash
            작업 결과는 Config정보의 callback값을 참조하여 아래처럼 URL을 호출하는 방식으로 전송(HTTP/REST API)한다.
            
            curl --location 'https://domain.com/callback_path?p=v' \
            --header 'Content-Type: application/json' \
            --data '{
                "result": {RESULT},
                "token": "{TOKEN}",
                ...
                "message": "{RESULT_MESSAGE}"
            }'
            ```
            
            | 이름 | 타입 | 설명 | 필수 | 비고 |
            | --- | --- | --- | --- | --- |
            | result | boolean | 처리결과 | Not Null |  |
            | token | string | 해당 요청을 식별하는 값 | Not Null | Order No. 또는 Invoice No. 역할을 하는 값 |
            | txidFee | string | 전송수수료 전송 결과 Hash ID |  | - 전송수수료 지갑 → 사용자 지갑
            - 사용자 지갑에 전송수수료 이상의 잔고가 있는 경우, 수수료 전송을 하지 않음(Null) |
            | txidToken | string | 토큰(코인) 전송 결과 Hash ID |  | 사용자 지갑 → 받는주소 지갑 |
            | message | string | 결과 메세지 |  |  |
            - Message Body
                - 성공 (Success)
                    
                    ```json
                    {
                    		"result": true,
                    		"token": "sdfsdfsdfsdf67…..........bd2sdfsdfsdffsf",
                    		"txidFee": "0xsdfsdfsdfsdf44667…..........bd268esdfsdfsdfsdfbsfsf",
                    		"txidToken": "0x1eeec26e62c4244667…..........bd268e975dfbef21ab318",
                    		"message": "{RESULT_MESSAGE}"
                    }
                    ```
                    
                - 실패 (Failed)
                    
                    ```json
                    {
                        "result": false,
                        "token": "sdfsdfsdfsdf67…..........bd2sdfsdfsdffsf",
                        "message": "{ERROR_MESSAGE}"
                    }
                    ```
                    
    
- Data Set List (Json Schema)
    - Transit Config
        
        
        | 이름 | 타입 | 설명 | 필수 | 비고 |
        | --- | --- | --- | --- | --- |
        | fee | double | 전송 비용(bnb) |  |  |
        | feeWalletKey | string | 전송수수료 지갑의 walletKey |  |  |
        | delay | int | 확인 지연시간(second)  |  |  |
        | count | int | 확인 횟수 |  |  |
        | callback | string | 결과 회신받는 URL 경로 |  |  |
    - ~~Gas Config~~