import time
import datetime
import sys
import pytz

# Define IST timezone
ist = pytz.timezone('Asia/Kolkata')

while True:
    now = datetime.datetime.now(ist)  # get current date and time in IST
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    sys.stdout.flush()
    time.sleep(3600)  # wait 1 hour

