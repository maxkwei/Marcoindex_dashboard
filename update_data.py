import json
from datetime import datetime
import urllib.parse
import feedparser
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf


def fetch_fred_and_market_data():
    """從 FRED 與 yfinance 抓取 2000-2026 的歷史走勢與最新報價"""
    print("正在抓取總經與市場數據...")

    # FRED 數據源：
    # DFF: 聯準會利率, DGS10: 10年美債, DGS20: 20年美債
    # CPIAUCSL: CPI, CPILFESL: 核心CPI, MANMM101USM657S: PMI趨勢
    # DEXTAUS: USD/TWD 歷史, DCOILWTICO: WTI 原油歷史
    series_map = {
        "fed_rate": "DFF",
        "us10y_yield": "DGS10",
        "us20y_yield": "DGS20",
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "pmi": "MANMM101USM657S",
        "usdtwd": "DEXTAUS",
        "oil": "DCOILWTICO",
    }

    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    history_data = {}
    latest_macro = {}

    for name, code in series_map.items():
        try:
            df = web.DataReader(code, "fred", start_date, end_date)
            df = df.dropna()

            # 月度重採樣以平滑圖表並降低資料量
            df_resampled = df.resample("ME").last().dropna()

            dates = df_resampled.index.strftime("%Y-%m").tolist()
            values = [round(float(v), 2) for v in df_resampled[code].values]

            # 若為 PMI 數據，轉換放大為標準 0-100 指數區間
            if name == "pmi":
                values = [
                    round(v * 100 + 50, 1) if v < 10 else v for v in values
                ]

            history_data[name] = {"dates": dates, "values": values}
            latest_macro[name] = values[-1] if len(values) > 0 else "N/A"
        except Exception as e:
            print(f"抓取 {code} 失敗: {e}")
            history_data[name] = {"dates": [], "values": []}
            latest_macro[name] = "N/A"

    # 即時補齊最新市場價格 (yfinance)
    try:
        twd_ticker = yf.Ticker("USDTWD=X").history(period="2d")
        if not twd_ticker.empty:
            latest_macro["usdtwd"] = round(
                float(twd_ticker["Close"].iloc[-1]), 2
            )

        oil_ticker = yf.Ticker("CL=F").history(period="2d")
        if not oil_ticker.empty:
            latest_macro["oil"] = round(float(oil_ticker["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"yfinance 即時更新失敗: {e}")

    return history_data, latest_macro


def fetch_macro_news():
    """抓取即時新聞"""
    print("正在抓取即時總經新聞...")
    queries = ["聯準會 利率 美債", "通膨 CPI 油價", "美元 台幣 匯率"]

    news_list = []
    for q in queries:
        try:
            encoded_query = urllib.parse.quote(q)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            feed = feedparser.parse(url)

            for entry in feed.entries[:2]:
                news_list.append(
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "published": getattr(entry, "published", "最新新聞"),
                        "source": (
                            entry.source.title
                            if hasattr(entry, "source")
                            else "Google News"
                        ),
                    }
                )
        except Exception as e:
            print(f"新聞抓取失敗: {e}")

    return news_list


def main():
    history, latest_macro = fetch_fred_and_market_data()
    news = fetch_macro_news()

    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "latest_macro": latest_macro,
        "history": history,
        "news": news,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("成功更新 data.json！")


if __name__ == "__main__":
    main()
