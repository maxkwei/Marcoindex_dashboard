name: Daily Macro Data & News Updater

on:
  schedule:
    - cron: '0 0 * * *'  # 每天 UTC 00:00 (台灣時間早上 8:00) 自動執行
  workflow_dispatch:      # 支援手動點擊執行按鈕

jobs:
  update-dashboard:
    runs-on: ubuntu-latest
    steps:
      - name: 檢出儲存庫程式碼
        uses: actions/checkout@v3

      - name: 設定 Python 環境
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: 安裝所需 Python 套件
        run: |
          python -m pip install --upgrade pip
          pip install yfinance feedparser

      - name: 執行資料抓取與更新腳本
        run: python update_data.py

      - name: 自動提交並推播最新 data.json
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action Bot"
          git add data.json
          git commit -m "Auto-update: Latest finance data and news [skip ci]" || exit 0
          git push

