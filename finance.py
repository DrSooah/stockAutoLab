import subprocess
import sys

# 필요한 패키지 설치 시도
required_modules = ["yfinance", "requests", "pandas"]
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f"📦 '{module}' 모듈이 설치되어 있지 않습니다. 설치를 시도합니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

# 이후 안전하게 import
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

# ===== 설정 =====
TICKERS = [
    "TSLY", "CONY", "TSLW", "NFLW", "COIW", "PLTW", "NVDW", "XDTE", "QDTE",
    "VZ", "PFE", "JEPQ", "CVX", "XOVR", "GOOW", "METW", "AMDW", "AVGW",
    "AMZW", "MSFW", "MSTW", "HOOW", "UNH", "AAPW", "BRKW", "SCHD", "O",
    "TSLA", "U", "PLUG", "UBS", "NEE", "MRK", "MSTY"
]
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RSI_PERIODS = [14]
# ===============

def calculate_rsi_series(close, period):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def send_discord_message(message):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        return
    payload = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"❌ Discord 전송 실패: {e}")

def analyze_ticker(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=False)

        if data.empty or "Close" not in data:
            return f"⚠️ {ticker}: 종가 데이터 없음"

        close = data["Close"]
        rsi_values = {}
        signal_count = {"overbought": 0, "oversold": 0}
        report_date = None

        for period in RSI_PERIODS:
            rsi_series = calculate_rsi_series(close, period).dropna()
            send_discord_message(f"{rsi_series}")
            if len(rsi_series) < 2:
                rsi_values[period] = None
                send_discord_message(f"⚠️ {ticker} - RSI({period}) 시계열 길이 부족")
                continue
            send_message("step 01")
            try:
                latest_rsi = rsi_series.iloc[-2]  # 전일 기준
                rsi_values[period] = latest_rsi
                send_discord_message("step 02")
                if report_date is None:
                    report_date = pd.to_datetime(rsi_series.index[-2]).strftime("%Y-%m-%d")
                send_discord_message("step 03")
                if pd.notna(latest_rsi):
                    if latest_rsi > 70:
                        signal_count["overbought"] += 1
                    elif latest_rsi < 30:
                        signal_count["oversold"] += 1
                else:
                    send_discord_message(f"⚠️ {ticker} - RSI({period}) 값이 NaN입니다.")

            except Exception as e:
                rsi_values[period] = None
                send_discord_message(f"❌ {ticker} - RSI({period}) 처리 실패: {str(e)}")
        send_discord_message("step 04")
        rsi_report = "\n".join([
            f"  • RSI({p}) @ {report_date if report_date else 'N/A'}: {rsi_values[p]:.2f}"
            if rsi_values[p] is not None else f"  • RSI({p}): 계산 불가"
            for p in RSI_PERIODS
        ])
        send_discord_message("step 05")
        message = f"[{ticker}]\n{rsi_report}"

        if signal_count["oversold"] >= 1:
            message += "\n⛔ 과매도 신호 감지"
            send_discord_message(f"📉 {ticker}: 과매도 RSI 감지\n{rsi_report}")
        elif signal_count["overbought"] >= 1:
            message += "\n🚀 과매수 신호 감지"
            send_discord_message(f"📈 {ticker}: 과매수 RSI 감지\n{rsi_report}")
        else:
            message += "\n📊 중립 구간 (과매수/과매도 아님)"
            send_discord_message(f"📊 {ticker}: 중립 RSI 상태\n{rsi_report}")

        return message

    except Exception as e:
        error_msg = f"❌ {ticker}: 에러 발생 - {str(e)}"
        send_discord_message(error_msg)
        return error_msg

def main():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    print(f"\n📅 현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    send_discord_message("--------------------------------------\n")
    send_discord_message(f"📅 RSI 분석 시작 (KST 기준): {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

    for ticker in TICKERS:
        print(f"🔍 {ticker} 분석 중...", end=' ')
        send_discord_message(f"🔍 {ticker} 분석 중...")
        result = analyze_ticker(ticker)
        print(result)

if __name__ == "__main__":
    main()


