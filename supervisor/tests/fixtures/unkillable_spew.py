#!<<PYTHON>>
import time
import signal
signal.signal(signal.SIGTERM, signal.SIG_IGN)

counter = 0

while 1:
   time.sleep(0.01)
   print(f"more spewage {counter}")
   counter += 1
   
