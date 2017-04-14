#-*- coding:UTF-8 -*-
import sys,signal
reload(sys)
sys.setdefaultencoding('utf-8')
import sys,time,os
from app_ocr import WrapInfo
import logging
import json
import redis

class Task(object):
    def __init__(self):
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'infocombineque'

    def push_task(self,value):
        self.rcon.lpush(self.queue,value)
            # time.sleep(1)
            # task = self.rcon.blpop(self.queue, 0)[1]
            # print "push task"
    def push_pic(self,pic):
        self.rcon.lpush(self.queue,pic)

if __name__ == '__main__':
    seqandtitlestr=sys.argv[1]
    seqandtitlestr = seqandtitlestr.decode('utf-8').encode('utf-8')
    # print "*****"+seqandtitlestr
    seqandtitlestr=seqandtitlestr[0:-2]
    seqandtitlelist=seqandtitlestr.split("_*")
    for seqandtitle in seqandtitlelist:
        wi=WrapInfo()
        tmplist=seqandtitle.split("packname:")
        if len(tmplist)>1:
            tmplist2=tmplist[0].split("title:")
            wi.setPackName(tmplist[1])
            wi.setSeq(tmplist2[0])
            wi.setInfo(tmplist2[1])
            print '-----'+tmplist2[1]
            redistask=Task()
            seqstr=json.dumps(wi,default=lambda obj:obj.__dict__,ensure_ascii=False)
            redistask.push_task(seqstr)
