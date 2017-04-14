#-*-coding:utf-8 -*-
import redis
import base64
class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'pictaskque'

    def push_task(self):
        while True:
            result=self.rcon.blpop(self.queue,0)
            # task = self.rcon.blpop(self.queue, 0)[1]
            base64.encodestring()
            pic=base64.decodestring(result[1])
            f=open("3.png","wb")
            f.write(pic)
            f.close()

if __name__ == '__main__':
    print 'listen task queue'
    Task().push_task()