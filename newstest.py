import requests

from config import API_URL,API_SECRET,API_KEY
from datetime import datetime

from timedelta import Timedelta
url = "https://data.alpaca.markets/v1beta1/news?sort=desc"

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

PARAMETERS = {
    "start":"2024-08-29",
    "symbols":"SPY,SCHD,ES,QQQ,AAPL,MSFT,NVDA,AMZN,META,GOOGL,BRK.B,LLY,AVGO,JPM,TSLA,UNH,XOM,V,PG,JNJ,MA,COST,HD,WMT,TGT,KO,ADBE,CVX,ORCL,MCD,WFC,VZ,UNP,MS,BLK,TLT,VIX",
    "limit":50,
}

news = requests.get(url,headers=HEADERS,params=PARAMETERS)
print(news.text)

