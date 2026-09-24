import json
from datetime import datetime
import urllib.parse
import feedparser
import yfinance as yf


def fetch_market_data():
    """抓取最新即時市場數據"""
    print("正在抓取市場金融數據...")

    # 抓取標的：10年期美債殖利率 (^TNX), WTI原油 (CL=F), 美元/台幣 (USDTWD=X)
    tickers = {"us10y": "^TNX", "oil": "CL=F", "usdtwd": "USDTWD=X"}

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


def fetch_macro_news():
    """抓取影響總經、通膨與利率的最新即時新聞 RSS"""
    print("正在抓取即時總經新聞...")

    queries = [
        "聯準會 利率 通膨",
        "美債殖利率 油價",
        "川普 關稅 地緣政治",
    ]

    news_list = []
    for q in queries:
        try:
            # 使用 urllib.parse.quote 將中文與空白安全轉碼，避免 InvalidURL 錯誤
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
    news = fetch_macro_news()

    output_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S (UTC)"),
        "market": market,
        "news": news,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("成功產生最新 data.json 檔案！")


if __name__ == "__main__":
    main()
    
