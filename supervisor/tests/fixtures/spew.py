#!<<PYTHON>>
import sys
import time

for counter in range(30000):
    sys.stdout.write("more spewage %d\n" % counter)
    sys.stdout.flush()
    time.sleep(0.01)
