from lumibot.traders import Trader
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.backtesting import YahooDataBacktesting

import requests

from finbert_utils import estimate_sentiment

from datetime import datetime
from timedelta import Timedelta

from config import API_URL,API_SECRET,API_KEY

ALPACA_CONFIG = {
    "API_KEY": API_KEY,
    "API_SECRET":API_SECRET,
    "PAPER":  True
}

HEADERS = {
    "accept": "application/json",
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

NEWS_URL = "https://data.alpaca.markets/v1beta1/news?sort=desc"

from tradingview_ta import TA_Handler, Interval, Exchange
import tradingview_ta

from macd import macd

class TestStrategy(Strategy):

    def initialize(self, symbol="SPY", risk:float=.5):#change to spy / btc/usd
        self.symbol = symbol
        self.sleeptime = "1D"
        self.current_position = None
        self.risk = risk
        #self.minutes_before_closing = 8
        self.set_market('24/7') #delete when not using crypto to test afterhours, and replace btc symbols and exchange with spy and amex

    def technicals(self):
#        output = TA_Handler(symbol='spy', #change to spy / btcusdc
#                    screener='america', #change to america / crytpo
#                    exchange='amex', #change to amex / kraken
#                    interval='1d')
#     
#        recommendation = output.get_analysis().summary["RECOMMENDATION"]
        today, seven_days_ago = self.news_start_date()
        recommendation = macd(today)
        return recommendation

    def sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.risk / last_price,0)
        return cash, last_price, quantity
    
    def news_start_date(self):
        today = self.get_datetime()
        seven_days_ago = today - Timedelta(days=7)
        return today.strftime('%Y-%m-%d'), seven_days_ago.strftime('%Y-%m-%d')
    
    def fundamentals(self):
        today,seven_days_ago = self.news_start_date()
        PARAMETERS = {
            "start":seven_days_ago,
            "end":today,
            "symbols":"SPY,QQQ,NVDA,MSFT,V,MA,XOM,MS,JPM,BLK,TLT,VIX",
            "limit":10,
            }
        news = requests.get(NEWS_URL,headers=HEADERS,params=PARAMETERS)
        news_data = news.json()
        headlines = [event["headline"]for event in news_data["news"]]
        probability,sentiment=estimate_sentiment(headlines)
        return headlines,probability,sentiment

    def on_trading_iteration(self):

        technicals = self.technicals()
        headlines,probability, sentiment = self.fundamentals()
        cash, last_price, quantity = self.sizing()
        symbol = self.symbol

        print(headlines)
        print(probability)
        print(sentiment)

        print(technicals)
        print(cash)

        print("\n", self.current_position)

        if cash > last_price:

            if technicals == "HOLD_LONG":
                if self.current_position == "short":
                    print("Closing short position")
                    self.current_position = None
                    self.sell_all()
                if sentiment == "positive" and probability > .8:
                    order = self.create_order(
                        symbol,
                        quantity,
                        "buy",
                        type="bracket",
                        take_profit_price = last_price*1.6,
                        stop_loss_price = last_price*0.95
                        )
                    self.current_position = "long"
                    self.submit_order(order)
                    print("Long order submitted for ", quantity, " shares")
                if sentiment == "neutral":#to account for long term upside bias of market
                    order = self.create_order(
                        symbol,
                        quantity/2,
                        "buy",
                        type="bracket",
                        take_profit_price = last_price*1.6,
                        stop_loss_price = last_price*0.95
                        )
                    self.current_position = "long"
                    self.submit_order(order)
                    print("Long order submitted for ", quantity/2, " shares")
            elif technicals == "HOLD_SHORT":
                if self.current_position == "long":
                    print("Closing long position")
                    self.sell_all()
                    self.current_position = None
                if sentiment == "negative" and probability > .66:
                    order = self.create_order(
                        symbol,
                        quantity,
                        "sell",
                        type="bracket",
                        take_profit_price = last_price*.8,
                        stop_loss_price = last_price *1.05
                    )
                    self.current_position = "short"
                    self.submit_order(order)
                    print("Short order submitted for ", quantity, " shares")
            elif technicals == "BUY":
                if self.current_position == "short":
                    print("Closing short position")
                    self.sell_all()
                order = self.create_order(
                    symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price = last_price*1.6,
                    stop_loss_price = last_price*0.95
                    )
                self.current_position = "long"
                self.submit_order(order)
                print("Long order submitted for ", quantity, " shares")
            elif technicals == "SELL":
                if self.current_position == "long":
                    print("Closing long position")
                    self.current_position = None
                    self.sell_all()
                order = self.create_order(
                    symbol,
                    quantity,
                    "sell",
                    type="bracket",
                    take_profit_price = last_price*.9,
                    stop_loss_price = last_price *1.03
                )
                self.current_position = "short"
                self.submit_order(order)
                print("Short order submitted for ", quantity/2, " shares")

         
    def on_abrupt_closing(self):
        self.log_message("Abrupt closing")
        self.sell_all()
        self.current_position = None
            
start_date = datetime(2022,1,1)
end_date = datetime(2022,9,15)



broker = Alpaca(ALPACA_CONFIG)

strategy = TestStrategy(name='teststrat', broker=broker, parameters={"symbol":"SPY", "cash_at_risk":.5})     
strategy.backtest(YahooDataBacktesting, start_date,end_date,parameters={"symbol":"SPY","cash_at_risk":.5})  

#uncomment following to run live

#trader = Trader()
#trader.add_strategy(strategy)
#trader.run_all()

