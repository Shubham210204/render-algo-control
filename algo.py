import time
import random
import sys

while True:
    print(f"Running algo... Value: {random.randint(1,100)}")
    sys.stdout.flush()  # flush immediately
    time.sleep(2)
