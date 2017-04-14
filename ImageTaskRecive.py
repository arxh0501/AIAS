#-*- coding:UTF-8 -*-
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
import traceback,base64,json
from redis_p import Task,redis
import threading,os,time,logging.config,Image
from app_ocr import WrapInfo,PicSumWrap,ImageWrap
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")


class GetImageTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'imagetaskque'
        # self.ocrQue=
        # self.imagetaskdir=
        # self.combineque="imagetaskque"
    def getTask(self):
        d = self.rcon.blpop(self.queue, 0)[1]
        wrap = json.loads(d)
        pic = base64.decodestring(wrap["image"])
        curdir=os.getcwd()
        packName = wrap["packName"]
        imagetaskdir=os.path.join(curdir,"imagetask/"+packName)
        if not os.path.exists(imagetaskdir):
            os.makedirs(imagetaskdir)

        packName=wrap["packName"]
        seq=wrap["imageSeq"]
        picname=seq+".png"
        picname=os.path.join(imagetaskdir,picname)
        f=open(picname,"wb")
        f.write(pic)
        f.close()
        log.debug("write %s to %s"%(picname,curdir))
        time.sleep(1)
        bim=Image.open(picname,"r")
        wrapimage=ImageWrap(wrap["packName"],bim,wrap["imageSeq"])
        return wrapimage
    def run(self):
        log.debug("----------------GetTitleInfo start----------------")
        while True:
            wrapimage=self.getTask()
            # self.put(wrapimage)
