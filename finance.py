import yfinance as yf
import requests
from datetime import datetime, timedelta, timezone
import os

# ===== 설정 =====
TICKERS = ["TSLY", "CONY", "TSLW", "NFLW", "COIW", "PLTW", "NVDW", "XDTE", "QDTE"]  # 분석할 종목 리스트
WEBHOOK_URL = "https://discord.com/api/webhooks/1399780317254127797/xi1lBDb981_I5dALDLkqAxnYKR9_W_Up6u2LntUppc214_Uwun0gStaorJZo1Z91BaQc"
RSI_PERIOD = 14
# ===============

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_discord_message(message):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

def analyze_ticker(ticker):
    try:
        data = yf.download(ticker, period="2mo", interval="1d", progress=False, auto_adjust=False)

        if data.empty:
            return f"⚠️ {ticker}: 데이터 없음"

        data['RSI'] = calculate_rsi(data)
        latest_rsi = data['RSI'].iloc[-1]

        message = f"[{ticker}] RSI: {latest_rsi:.2f}"

        if latest_rsi < 30:
            message += " ⛔ 과매도 구간!"
            send_discord_message(f"📉 {ticker}:\tRSI {latest_rsi:.2f} (과매도)")
        elif latest_rsi > 70:
            message += " 🚀 과매수 구간!"
            send_discord_message(f"📈 {ticker}:\tRSI {latest_rsi:.2f} (과매수)")

        return message
    except Exception as e:
        return f"❌ {ticker}: 에러 발생 - {str(e)}"

def main():
    kst = timezone(timedelta(hours=9))  # UTC+9
    now = datetime.now(kst)
    print(f"\n📅 현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    send_discord_message("--------------------------------------\n")
    send_discord_message(f"\n\n\n📅 현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("🔍 종목별 RSI 분석 시작")
    for ticker in TICKERS:
        result = analyze_ticker(ticker)
        print(result)

if __name__ == "__main__":
    main()
