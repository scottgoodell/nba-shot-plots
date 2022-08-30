from numpy import random
import time


def delay_between_1_and_2_secs():
  return time.sleep(random.uniform(1,2))