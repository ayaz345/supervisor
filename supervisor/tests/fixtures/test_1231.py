# -*- coding: utf-8 -*-
import logging
import random
import sys
import time

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(levelname)s [%(asctime)s] %(message)s',
                        datefmt='%m-%d|%H:%M:%S')
    for i in range(1, 500):
        delay = random.randint(400, 1200)
        time.sleep(delay / 1000.0)
        logging.info('%d - hash=57d94b…381088', i)

if __name__ == '__main__':
    main()
