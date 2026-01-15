# KRX-Stock MCP Server

## 1. Overview
KRX(한국거래소) API를 활용해 국내 주식 시장(KOSPI, KOSDAQ, KONEX)에 상장된 종목의 주가와 종목정보를 제공하는 MCP 서버입니다.   


## 2. Primitives
### 2.1. Tool
- **get_stock_info_by_date**  : 주어진 종목의 **종목정보**를 제공합니다. 구체적인 날짜가 주어지지 않을 경우 최근 개장일 기준으로 검색하며, 시장명이 주어지지 않을 경우 KOSPI · KOSDAQ · KONEX 에서 모두 검색합니다.     

- **get_stock_price_by_date** : 주어진 종목의 **주가**를 제공합니다. 구체적인 날짜가 주어지지 않을 경우 최근 개장일 기준으로 검색하며, 시장명이 주어지지 않을 경우 KOSPI · KOSDAQ · KONEX 에서 모두 검색합니다.     

## 3. Settings

### 3.1. API Key

KRX-Stock 서버를 사용하기 위해서는 KRX(한국거래소) API 키를 발급받아야 합니다. 다음 순서에 따라 API 키를 발급 받고 이용할 수 있습니다.

(1) [한국거래소 데이터마켓](https://openapi.krx.co.kr/contents/OPP/MAIN/main/index.cmd) 접속  
(2) 회원가입/로그인      
(3) '마이페이지 > API 인증키 신청'에서 인증키 발급  
(4) '서비스이용 > 주식'에서 [유가증권 일별매매정보](), [코스닥 일별매매정보](), [코넥스 일별매매정보](), [유가증권 일별매매정보](), [코스닥 종목기본정보](), [코넥스 종목기본정보]() 링크 접속 후, API 이용신청  


### 3.2. Environments
**(1) 레포지토리 복사**
```
git clone https://github.com/millet04/krx-stock-mcp.git
cd krx-stock-mcp
```
위의 절차에 따라 발급 받은 API 키를 `.env.sample` 파일에 입력합니다. <u>서버 실행 전 파일명을 `.env`로 수정해야 서버가 정상적으로 실행됩니다.</u>

**(2) 의존성 설치**

다음과 같이 uv 환경에서 코드를 실행하는 것이 편리합니다.
```
# 의존성 설치
uv sync 

# 가상환경 실행
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 서버실행 확인
uv run main.py
``` 
> Claud Desktop 에서 MCP 서버를 사용할 경우, 사용자가 직접 서버를 실행할 필요는 없습니다. 코드가 정상적으로 실행되는지만 확인하면 됩니다. 


## 4. How to use

### 4.1. Claud Desktop
Claud Desktop에서 Krx-Stock 서버를 사용하려면 '파일 > 설정 > 개발자 > claud_desktop_config.json' 파일을 다음과 같이 수정해주어야 합니다. 

```
{
  "mcpServers": {
    "krx-stock-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\...\\...\\...\\krx-stock-mcp", # main.py 가 있는 경로
        "run",
        "main.py"
      ]
    }
  }
}
```
> Claud Desktop (호스트)이 백그라운드에서 서버 역할을 하는 프로세스를 실행하고 응답을 수신합니다. 이때 호스트와 서버(프로세스)는 HTTPS 가 아닌 **표준 입출력(STDIO)** 을 통해 통신합니다. **(Local Server)** 

