#-*-coding:utf-8 -*-
import redis
import time
import datetime
import logging.config
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")

import cPickle
import base64

class Task(object):
    def __init__(self,quename,timeout=0):
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = quename
        self.timeout=timeout

    def pushTask(self,taskObject):
        self.rcon.lpush(self.queue,taskObject)
        time.sleep(1)
        log.debug("put task to %s"%self.queue)


    def pushPicTask(self,pic):
        self.rcon.lpush(self.queue,pic)
    def getTask(self):
        task = self.rcon.blpop(self.queue, timeout=self.timeout)[1]
        return task
        # f=cPickle.loads(task)
        # f.write()

if __name__ == '__main__':
    print 'listen task queue'
    f = open("/home/2.png", 'rb')  # 二进制方式打开图文件
    ls_f = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
    print ls_f
    imgdata = base64.b64decode(ls_f)
    file = open('1.jpg', 'wb')
    file.write(imgdata)
    file.close()

    # f.close()
    begin = datetime.datetime.now()
    Task().push_pic(ls_f)
    end = datetime.datetime.now()
    print end-begin