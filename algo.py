# import time
# import random
# import sys

# while True:
#     print(f"Running algo... Value: {random.randint(1,100)}")
#     sys.stdout.flush()  # flush immediately
#     time.sleep(2)

import time
import datetime
import sys

while True:
    now = datetime.datetime.now()  # get current date and time
    print(f"Alive from: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    sys.stdout.flush()  # flush immediately
    time.sleep(3600)  # wait 1 hour (3600 seconds)
