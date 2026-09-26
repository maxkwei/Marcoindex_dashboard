import json
from datetime import datetime
import urllib.parse
import feedparser
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf


def fetch_fred_and_market_data():
    """從 FRED 與 yfinance 抓取數據並對齊統一時間軸 (2000-2026)"""
    print("正在抓取總經與市場數據...")

    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    # 建立統一的月度時間序列基準 (2000-01 到 當前年月)
    date_range = pd.date_range(start=start_date, end=end_date, freq="ME")
    master_dates = date_range.strftime("%Y-%m").tolist()

    series_map = {
        "fed_rate": "DFF",
        "us10y_yield": "DGS10",
        "us20y_yield": "DGS20",
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "pmi": "MANMM101USM657S",
        "usdtwd": "DEXTAUS",     # 美元/台幣
        "usdjpy": "DEXJPUS",     # 美元/日元
        "usdcny": "DEXCHUS",     # 美元/人民幣
        "oil": "DCOILWTICO",     # WTI 原油
        "gold": "GOLDAMGBD228NLBM", # 黃金價格
    }

    history_data = {}
    latest_macro = {}

    for name, code in series_map.items():
        try:
            df = web.DataReader(code, "fred", start_date, end_date)
            df = df.dropna()
            df_resampled = df.resample("ME").last().ffill()

            df_resampled.index = df_resampled.index.strftime("%Y-%m")
            aligned_s = df_resampled[code].reindex(master_dates).ffill().bfill()

            values = [round(float(v), 2) for v in aligned_s.values]

            # PMI 轉為 0-100 標準指數
            if name == "pmi":
                values = [
                    round(v * 100 + 50, 1) if v < 10 else round(v, 1)
                    for v in values
                ]

            history_data[name] = {"dates": master_dates, "values": values}
            latest_macro[name] = values[-1] if len(values) > 0 else "N/A"
        except Exception as e:
            print(f"抓取 FRED {code} 失敗: {e}")
            history_data[name] = {"dates": master_dates, "values": []}
            latest_macro[name] = "N/A"

    # 用 yfinance 補齊最新即時報價，確保當前數字準確
    try:
        yf_tickers = {
            "usdtwd": "USDTWD=X",
            "usdjpy": "JPY=X",
            "usdcny": "CNY=X",
            "oil": "CL=F",
            "gold": "GC=F",
        }
        for key, ticker in yf_tickers.items():
            t = yf.Ticker(ticker).history(period="5d")
            if not t.empty:
                latest_macro[key] = round(float(t["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"yfinance 即時更新失敗: {e}")

    return history_data, latest_macro


def fetch_macro_news():
    """抓取即時新聞"""
    print("正在抓取即時總經新聞...")
    queries = ["聯準會 利率 美債", "美元 台幣 日元 人民幣 匯率", "原油 黃金 價格"]

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

    print("成功更新數據，時間軸已完美對齊！")


if __name__ == "__main__":
    main()
