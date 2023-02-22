import time
from concurrent.futures import ThreadPoolExecutor


class MultiThread(object):
  def __init__(self, num):
    self.pool = ThreadPoolExecutor(num)
    self.jobs = []
    self.res = []

  def run(self, func, **kwargs):
    self.jobs.append(self.pool.submit(func, **kwargs))

  def join(self):
    while self.jobs:
      for idx, job in enumerate(self.jobs):
        if job.done():
          self.res.append(job.result())
          del self.jobs[idx]
      if self.jobs:
        time.sleep(1)
