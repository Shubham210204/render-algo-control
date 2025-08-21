from dhanhq import dhanhq
import pandas as pd
import yfinance as yf
import datetime
import time
import os
import sys
from zoneinfo import ZoneInfo

# ---- credentials ----
client_id = os.getenv("client_id")
access_token = os.getenv("access_token")
dhan = dhanhq(client_id, access_token)

def get_instrument_token(stock_name):
    df = pd.read_csv('api-scrip-master.csv')
    data_dict = {}
    for index, row in df.iterrows():
        trading_symbol = row['SEM_TRADING_SYMBOL']
        exm_ecxh_id = row['SEM_EXM_EXCH_ID']
        if trading_symbol not in data_dict:
            data_dict[trading_symbol] = {}
        data_dict[trading_symbol][exm_ecxh_id] = row.to_dict()
    return data_dict[stock_name]['NSE']['SEM_SMST_SECURITY_ID']

def place_bracket_order(stock_name, stock_id, qty, target_price, stoploss_price):
    # Step 1: Place BUY order (market)
    buy_order = dhan.place_order(
        security_id=stock_id,
        exchange_segment=dhan.NSE,
        transaction_type=dhan.BUY,
        quantity=qty,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=0
    )
    buy_id = buy_order['data']['orderId']
    print("Bought", qty, "quantity of", stock_name, "at:", buy_price, ",Target:", target, ",Stop loss:", stop_loss)
    sys.stdout.flush()
            
    time.sleep(2)

    # Step 2: Place Target SELL order
    target_order = dhan.place_order(
        security_id=stock_id,
        exchange_segment=dhan.NSE,
        transaction_type=dhan.SELL,
        quantity=qty,
        order_type=dhan.LIMIT,
        product_type=dhan.INTRA,
        price=target_price,
        validity=dhan.DAY
    )
    target_id = target_order['data']['orderId']

    # Step 3: Place Stop Loss SELL order
    sl_order = dhan.place_order(
        security_id=stock_id,
        exchange_segment=dhan.NSE,
        transaction_type=dhan.SELL,
        quantity=qty,
        order_type=dhan.SLM,
        product_type=dhan.INTRA,
        price=stoploss_price,
        trigger_price=stoploss_price,
        validity=dhan.DAY
    )
    sl_id = sl_order['data']['orderId']

    return buy_id, target_id, sl_id

def oco_monitor(stock_id, buy_id, target_id, sl_id, check_interval=2):
    while True:
        target_status = dhan.get_order_by_id(target_id)['data'][0]['orderStatus']
        sl_status = dhan.get_order_by_id(sl_id)['data'][0]['orderStatus']
        current_time = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).time()
        if current_time > datetime.time(15,00):
            print("Time up, closing all orders...")
            sys.stdout.flush()
            dhan.cancel_order(sl_id)
            dhan.cancel_order(target_id)
            # dhan.cancel_order(buy_id)
            sell_order = dhan.place_order(
                security_id=stock_id,
                exchange_segment=dhan.NSE,
                transaction_type=dhan.SELL,
                quantity=qty,
                order_type=dhan.MARKET,
                product_type=dhan.INTRA,
                price=0
            )
            break
        if target_status == "TRADED":
            print("Target hit! Cancelling Stop Loss order...")
            sys.stdout.flush()
            dhan.cancel_order(sl_id)
            break
        if sl_status == "TRADED":
            print("Stop Loss hit! Cancelling Target order...")
            sys.stdout.flush()
            dhan.cancel_order(target_id)
            break
        time.sleep(check_interval)

def round_to_tick(price, tick_size=0.10):
    return round(round(price / tick_size) * tick_size, 2)

def get_chart(stock_name):
    stock = yf.Ticker(stock_name + ".NS")
    df = stock.history(interval="5m", period="3d")
    df.reset_index(inplace=True)
    df = df[['Datetime', 'Open', 'High', 'Low', 'Close']]
    df.rename(columns={'Datetime': 'timestamp'}, inplace=True)
    df['timestamp'] = df['timestamp'].dt.tz_localize(None)

    for col in ['Open', 'High', 'Low', 'Close']:
        df[col] = df[col].apply(round_to_tick)

    df['SMA_44'] = df['Close'].rolling(window=44).mean().round(2)
    return df

# def sma_rising(stock_id):
#     chart = get_chart(stock_id)
#     if chart.loc[50, 'SMA_44'] < chart.loc[74, 'SMA_44'] < chart.loc[98, 'SMA_44'] < chart.loc[122, 'SMA_44'] < chart.loc[146, 'SMA_44']:
#         return True
#     else:
#         return False

watchlist = ['NHPC','MOTHERSON','PNB','CANBK','IRFC','UNIONBANK','IOC','TATASTEEL','GAIL','BHEL','ONGC','BANKBARODA','WIPRO','POWERGRID','ECLERX','BPCL','NTPC','COALINDIA','TATAPOWER','BEL','PFC','ITC','VEDL','VBL','DABUR','JSWENERGY','ADANIPOWER','ATGL','AMBUJACEM','ICICIPRULI','TATAMOTORS','HINDALCO','IRCTC','HDFCLIFE','DLF','INDUSINDBK','BAJFINANCE','LICI','ADANIGREEN','ZYDUSLIFE','JINDALSTEL','TATACONSUM','JSWSTEEL','AXISBANK','DRREDDY','GODREJCP','LODHA','UBL','ADANIPORTS','NAUKRI','RELIANCE','INFY','ICICIBANK','HCLTECH','TECHM','CHOLAFIN','CIPLA','HAVELLS','SUNPHARMA','SBILIFE','ICICIGI','BAJAJFINSV','BHARTIARTL','KOTAKBANK','HDFCBANK','NESTLEIND','ADANIENT','ASIANPAINT','HINDUNILVR','GRASIM','TVSMOTOR','TCS','PIDILITIND','SIEMENS','M&M']

traded_watchlist = []

while True:
     # ---- time preferences ----
     current_time = datetime.datetime.now(ZoneInfo("Asia/Kolkata")).time()
     if current_time < datetime.time(9, 20):
          print("wait for market to start", current_time)
          sys.stdout.flush()
          time.sleep(300)
          continue
     if current_time > datetime.time(15,00):
          print("Market is over, Bye Bye see you tomorrow", current_time)
          sys.stdout.flush()
          break
     
     # ---- loop for each stock ----
     for stock_name in watchlist:
        # ---- data fetch ----
        chart = get_chart(stock_name)
        stock_id = get_instrument_token(stock_name)
        is_rising = chart.iloc[-5]['SMA_44'] > chart.iloc[-20]['SMA_44'] > chart.iloc[-35]['SMA_44'] > chart.iloc[-50]['SMA_44'] > chart.iloc[-65]['SMA_44'] > chart.iloc[-80]['SMA_44'] > chart.iloc[-95]['SMA_44'] > chart.iloc[-110]['SMA_44'] > chart.iloc[-125]['SMA_44'] > chart.iloc[-140]['SMA_44']

        # ---- bullish candles ----
        engulf = (  
            chart.iloc[-3]['Open'] > chart.iloc[-3]['Close'] and
            chart.iloc[-2]['Open'] < chart.iloc[-3]['Close'] and
            chart.iloc[-2]['Close'] > chart.iloc[-3]['Open'])
        # red_hammer = (
        #     chart.iloc[-3]['Close'] < chart.iloc[-3]['Open'] and
        #     (chart.iloc[-3]['Close'] - chart.iloc[-3]['Low']) >= 4 * abs(chart.iloc[-3]['Open'] - chart.iloc[-3]['Close']) and
        #     (chart.iloc[-3]['High'] - chart.iloc[-3]['Open']) < (chart.iloc[-3]['Open'] - chart.iloc[-3]['Close']))
        green_hammer = (
            chart.iloc[-3]['Close'] > chart.iloc[-3]['Open'] and
            (chart.iloc[-3]['Open'] - chart.iloc[-3]['Low']) >= 4 * abs(chart.iloc[-3]['Close'] - chart.iloc[-3]['Open']) and
            (chart.iloc[-3]['High'] - chart.iloc[-3]['Close']) < (chart.iloc[-3]['Close'] - chart.iloc[-3]['Open']))
        white_soldiers = (
            chart.iloc[-3]['Close'] > chart.iloc[-3]['Open'] and
            chart.iloc[-4]['Close'] > chart.iloc[-4]['Open'] and
            chart.iloc[-3]['Close'] > chart.iloc[-4]['Close'] and
            chart.iloc[-4]['Close'] > chart.iloc[-5]['Close'])
        big_green = (
            chart.iloc[-2]['Open'] == chart.iloc[-2]['Low'] and
            chart.iloc[-2]['Close'] == chart.iloc[-2]['High'] and
            chart.iloc[-2]['Close'] > chart.iloc[-2]['Open']
        )

        # ---- candle formations ----
        bullish = engulf or green_hammer or white_soldiers or big_green
        crossover = (chart.iloc[-2]['Low'] < chart.iloc[-2]['SMA_44']) and (chart.iloc[-2]['High'] > chart.iloc[-2]['SMA_44']) and (chart.iloc[-2]['Open'] < chart.iloc[-2]['Close'])
        confirmation = chart.iloc[-1]['High'] > chart.iloc[-2]['High']

        # ---- trade value calculation ----
        balance_response = dhan.get_fund_limits()
        available_balance = balance_response['data']['availabelBalance']
        leveraged_margin = available_balance * 5
        buy_price = chart.iloc[-1]['High']
        # target_get = buy_price + 2.5 * (chart.iloc[-2]['High'] - chart.iloc[-2]['Low'])
        target = round_to_tick(buy_price * 1.005)
        # target = round(max(target_get, min_target), 2)
        # stop_loss_get = chart.iloc[-4]['Low']
        stop_loss = round_to_tick(buy_price * 0.996)
        # stop_loss = round(min(stop_loss_get, max_stop_loss), 2)
        qty = 1 # int(leveraged_margin // buy_price)

        # ---- trade conditions ----
        if crossover and confirmation and bullish and stock_name not in traded_watchlist and is_rising and buy_price < 3 * available_balance:
            buy_id, target_id, sl_id = place_bracket_order(stock_name, stock_id, qty, target, stop_loss)
            oco_monitor(stock_id, buy_id, target_id, sl_id)
            traded_watchlist.append(stock_name)
            print("Traded stocks:", traded_watchlist)
            sys.stdout.flush()

print("🛑 Script ended!!")
sys.stdout.flush()