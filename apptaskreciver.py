#-*- coding:UTF-8 -*-
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
import struct,time
import tesserocr,redis,json
import logging.config
from subprocess import PIPE,Popen
import cPickle
import pickle
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")
from redis_p import Task
import socket

class AppFile():
    def __init__(self):
        pass
    @staticmethod
    def copyFile(spath,dpath):
        # sfile=host+":"+spath
        p1=Popen(["scp",spath,dpath])
        p1.wait()
        log.debug("copy file from %s to dir %s" % (spath, dpath))

    @staticmethod
    def sendFile(host,user,spath,dpath):
        dfile=user+"@"+host+":"+dpath
        p1=Popen["scp",spath,dfile]
        p1.wait()
        log.debug("send file from %s to  dir %s"%(spath,dfile))
class AppTaskReceiver():
    def __init__(self):
        self.taskDir="/tmp/apptask/"
        self.appFile=AppFile()
        self.appTaskQue="apptaskque"
        self.task = Task(self.appTaskQue)
        if not os.path.exists(self.taskDir):
            os.mkdir(self.taskDir)
    def getAppTaskFrom(self):
        # t=Task(self.appTaskQue)
        return self.task.getTask()

if __name__=="__main__":
    atr = AppTaskReceiver()
    appFile=AppFile()
    while True:
        spath=atr.getAppTaskFrom()
        appFile.copyFile(spath,atr.taskDir)
        time.sleep(5)
