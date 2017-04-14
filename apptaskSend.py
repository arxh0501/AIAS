#-*- coding:UTF-8 -*-
import sys,os
reload(sys)
sys.setdefaultencoding('utf-8')
import struct,time,threading
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
    def copyFile(host,user,spath,dpath):
        sfile=user+"@"+host+":"+spath
        p1=Popen(["scp",sfile,dpath])
        p1.wait()
        log.debug("copy file from %s to dir %s" % (sfile, dpath))

    @staticmethod
    def sendFile(host,user,spath,dpath):
        dfile=user+"@"+host+":"+dpath
        p1=Popen["scp",spath,dfile]
        p1.wait()
        log.debug("send file from %s to  dir %s"%(spath,dfile))
class AppTaskSender(threading.Thread):
    def __init__(self,apkdir,apptaskque):
        threading.Thread.__init__(self)
        self.apkDir=apkdir
        self.appTaskQue=apptaskque
    def run(self):
        self.putApkTasktoQue()
    def putApkTasktoQue(self):
        try:
            while True:
                if os.path.isdir(self.apkDir):
                    dirList = os.listdir(self.apkDir)
                    if len(dirList)>0:
                        for apkdir in dirList:
                            apk = os.path.join(self.apkDir, apkdir)
                            finishDir = os.path.join(os.getcwd(), "app_finish")
                            destFile = os.path.join(finishDir, apkdir)
                            os.rename(apk, destFile)
                            log.debug("remove %s to finish_dir" % apk.split("/")[-1])
                            self.appTaskQue.put(destFile)
                            log.debug("put APP analysis task to AppQueue ")
                        time.sleep(5)
                    else:
                        log.debug("no app analysis task")
                        time.sleep(5)
        except:
            log.error("exception happend in getapktaskfromdir")

class AppTaskSenderDistribute(threading.Thread):
    def __init__(self,apkdir):
        self.apkDir=apkdir
        self.redisTask=Task("apptaskque")
        self.appTaskQue="apptaskque"
    def run(self):
        self.putApkTasktoQue()
    def putApkTasktoQue(self):
        try:
            while True:
                if os.path.isdir(self.apkDir):
                    dirList = os.listdir(self.apkDir)
                    if len(dirList)>0:
                        for apkdir in dirList:
                            apk = os.path.join(self.apkDir, apkdir)
                            finishDir = os.path.join(os.getcwd(), "app_finish")
                            destFile = os.path.join(finishDir, apkdir)
                            os.rename(apk, destFile)
                            log.debug("remove %s to finish_dir" % apk.split("/")[-1])
                            destFiletask=socket.gethostname()+":"+destFile
                            self.redisTask.pushTask(destFiletask)
                            log.debug("put APP analysis task to %s "%self.appTaskQue)
                        time.sleep(3)
                    else:
                        log.debug("no app analysis task")
                        time.sleep(3)
        except:
            log.error("exception happend in getapktaskfromdir")

    # def getApkTaskFromDir(self):


if __name__=="__main__":
    # path="/home/kuaibao.apk"
    # f=open("/home/redis.txt","rb")
    # # cPickle.dump(path,f)
    # # f.close()
    # # f=open(path,"rb")
    # cPickle.load(f)

    # pickle.du
    # f=open(path,"rb")
    # print f.read()
    # apkstr=pickle.load(f)
    # f1=pickle.dumps(apkstr)
    # f1.write("/home/redis.apk")
    # f.close()
    # f1.close()

    # import getpass
    # print getpass.getuser()
    # import socket
    #
    # sname=socket.gethostname()
    # print socket.gethostbyname()
    # print socket.gethostbyname(sname)
    # print socket.gethostbyaddr()
    # # file=AppFile()
    # # file.copyFile("localhost","root","/home/kuaibao.apk","/home/hw/python_code/")
    # import socket
    # print socket.gethostname()
    # myname = socket.getfqdn(socket.gethostname())
    # ipList = socket.gethostbyname_ex(socket.gethostname())
    # myaddr = socket.gethostbyname(myname)
    # print myaddr,ipList
    ate=AppTaskSender("/home/hw/python_code/apptaskdir")
    ate.putApkTasktoQue()
    # watchAppDir()