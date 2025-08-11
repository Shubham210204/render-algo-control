import sys
# sys.stdout.flush()

from dhanhq import dhanhq
import pandas as pd
import yfinance as yf
import datetime
import time
import os

# ---- credentials ----
client_id = os.getenv("client_id")
access_token = os.getenv("access_token")
dhan = dhanhq(client_id, access_token)

print(client_id)
sys.stdout.flush()

print(access_token)
sys.stdout.flush()