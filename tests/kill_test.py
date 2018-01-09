#!/usr/bin/python
# Pretty much spews out a whole bunch of threads to make multi calls
# on the px to test how px-daemon respondes.
# This was a problem in very early beta
# When sqlite3worker finally gets added, hopefully this test will yield faster
# results.
# 1.0.1 flaw
import threading
from subprocess import call
from random import choice

def stupid_call():
  while 1:
    print call(['python', '../sys_tools/geo'] + choice([['127.0.0.1'], ['1.0.0.0']]))


for _ in range(50):
  threading._start_new_thread(stupid_call, tuple())

while 1:pass
