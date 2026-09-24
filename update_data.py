import json
from datetime import datetime
import urllib.parse
import feedparser
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf


def fetch_market_data():
    """抓取即時市場數據 (10年美債, 20年美債, 原油, 美元/台幣)"""
    print("正在抓取市場金融數據...")
    tickers = {
        "us10y": "^TNX",
        "us20y": "TLT",  # 20年期美債ETF/殖利率參考
        "oil": "CL=F",
        "usdtwd": "USDTWD=X",
    }

    market_data = {}
    for key, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest_price = round(float(hist["Close"].iloc[-1]), 2)
                prev_price = round(float(hist["Close"].iloc[-2]), 2)
                change = round(latest_price - prev_price, 2)
                market_data[key] = {
                    "current": latest_price,
                    "prev": prev_price,
                    "change": change,
                }
            else:
                market_data[key] = {
                    "current": "N/A",
                    "prev": "N/A",
                    "change": 0,
                }
        except Exception as e:
            print(f"抓取 {symbol} 失敗: {e}")
            market_data[key] = {"current": "N/A", "prev": "N/A", "change": 0}

    return market_data


def fetch_fred_macro_history():
    """從 FRED 官方數據庫抓取 2000 年至今的歷史走勢數據"""
    print("正在從 FRED 抓取 2000 年至今的歷史走勢與最新指標...")

    # FRED 代碼：
    # DFF: 聯準會有效聯邦基金利率
    # CPIAUCSL: CPI (消費者物價指數)
    # CPILFESL: 核心 CPI (扣除能源與食品)
    # ISM/MANPMI 或 NAPM: 製造業 PMI 指數
    # DGS10: 10年期美債殖利率
    # DGS20: 20年期美債殖利率
    series_map = {
        "fed_rate": "DFF",
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "pmi": "MANMM101USM657S",  # 美國製造業指標趨勢
        "us10y_yield": "DGS10",
        "us20y_yield": "DGS20",
    }

    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    history_data = {}
    latest_macro = {}

    for name, code in series_map.items():
        try:
            df = web.DataReader(code, "fred", start_date, end_date)
            df = df.dropna()

            # 採樣降低檔案大小 (按月採樣，利於前端快速繪圖)
            df_resampled = df.resample("ME").last().dropna()

            dates = df_resampled.index.strftime("%Y-%m").tolist()
            values = [round(float(v), 2) for v in df_resampled[code].values]

            history_data[name] = {"dates": dates, "values": values}

            # 紀錄最新值
            if len(values) > 0:
                latest_macro[name] = values[-1]
            else:
                latest_macro[name] = "N/A"
        except Exception as e:
            print(f"抓取 FRED 代碼 {code} 失敗: {e}")
            history_data[name] = {"dates": [], "values": []}
            latest_macro[name] = "N/A"

    return history_data, latest_macro


def fetch_macro_news():
    """抓取關鍵總經新聞 RSS"""
    print("正在抓取即時總經新聞...")
    queries = [
        "聯準會 利率 CPI 通膨",
        "美債殖利率 PMI 經濟",
        "川普 關稅 油價",
    ]

    news_list = []
    for q in queries:
        try:
            encoded_query = urllib.parse.quote(q)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            feed = feedparser.parse(url)

            for entry in feed.entries[:3]:
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
            print(f"抓取關鍵字 '{q}' 新聞失敗: {e}")

    return news_list


def main():
    market = fetch_market_data()
    history, latest_macro = fetch_fred_macro_history()
    news = fetch_macro_news()

    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "market": market,
        "latest_macro": latest_macro,
        "history": history,
        "news": news,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("成功產生最新 2000-2026 總經歷史數據 data.json 檔案！")


if __name__ == "__main__":
    main()
