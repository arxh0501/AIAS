#-*- coding:UTF-8 -*-
import sys,signal
reload(sys)
sys.setdefaultencoding('utf-8')
import sys,time,os
from app_ocr import WrapInfo
import logging
import json
import redis

def dict2WrapInfo(d):
    return WrapInfo(d["info"], d["packName"], d["seq"])

class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'titleque'
    def getTask(self):
        d= self.rcon.blpop(self.queue, 0)[1]
        wrap=json.loads(d)
        print type(d)
        print type(wrap)
        print wrap
        print wrap["info"]
        print wrap["packName"]
        print wrap["seq"]
        print d
        print "------------------------------------"


if __name__ == '__main__':
    redistask=Task()
    redistask.getTask()



