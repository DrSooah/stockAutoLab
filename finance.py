import yfinance as yf
import requests
from datetime import datetime, timedelta, timezone

# ===== 설정 =====
TICKERS = ["TSLY", "CONY", "TSLW", "NFLW", "COIW", 
           "PLTW", "NVDW", "XDTE", "QDTE", "VZ", 
           "PFE", "JEPQ", "CVX", "XOVR", "GOOW", 
           "METW", "AMDW", "AVGW", "AMZW", "MSFW", 
           "MSTW", "HOOW", "UNH", "AAPW", "AMDW",
           "AMZW", "AVGW", "BRKW"]
WEBHOOK_URL = "https://discord.com/api/webhooks/1399780317254127797/xi1lBDb981_I5dALDLkqAxnYKR9_W_Up6u2LntUppc214_Uwun0gStaorJZo1Z91BaQc"
RSI_PERIODS = [14]
# ===============

def calculate_rsi(data, period):
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

        rsi_values = {}
        signal_count = {"overbought": 0, "oversold": 0}

        for period in RSI_PERIODS:
            data[f'RSI_{period}'] = calculate_rsi(data, period)
            latest_rsi = data[f'RSI_{period}'].iloc[-1]
            rsi_values[period] = latest_rsi

            if latest_rsi > 70:
                signal_count["overbought"] += 1
            elif latest_rsi < 30:
                signal_count["oversold"] += 1

        rsi_report = "\n".join([f"  • RSI({p}): {rsi_values[p]:.2f}" for p in RSI_PERIODS])
        message = f"[{ticker}]\n{rsi_report}"

        if signal_count["oversold"] >= 1:
            message += "\n⛔ 과매도 신호 감지 (2개 이상)"
            send_discord_message(f"📉 {ticker}: 과매도 RSI 감지\n{rsi_report}")
        elif signal_count["overbought"] >= 1:
            message += "\n🚀 과매수 신호 감지 (2개 이상)"
            send_discord_message(f"📈 {ticker}: 과매수 RSI 감지\n{rsi_report}")

        return message
    except Exception as e:
        return f"❌ {ticker}: 에러 발생 - {str(e)}"

def main():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    print(f"\n📅 현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    send_discord_message("--------------------------------------\n")
    send_discord_message(f"📅 RSI 분석 시작 (KST 기준): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

    for ticker in TICKERS:
        result = analyze_ticker(ticker)
        print(result)

if __name__ == "__main__":
    main()

