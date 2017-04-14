#-*- coding:UTF-8 -*-
"""
AIAS辅助工具实现类，引用
"""
import sys,signal,os,logging.config

from app_ocr import ImageTaskProducer, GetTitleInfo, OcrThread, ShuffleTreeBuildTask
from my_net import AppNetMonitor
TIMES=2
reload(sys)
sys.setdefaultencoding('utf-8')
import threading,time
from uiautomatordump import PointElement
aapt="/home/android/android-sdk-linux/build-tools/23.0.3/aapt"
from subprocess import Popen,PIPE

logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")

class InitUtil():
    def __init__(self):
        self.pckname=""
        self.apkDir="/home/apptask"
    @staticmethod
    def auto_run(pckname):
        device = Popen(['monkeyrunner', './monkeyrunner_test.py', pckname])
        device.wait()

    @staticmethod
    def createPicDir(packName):
        dir_name = os.path.join("/home/pic", packName)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        else:
            pass
        return dir_name
    @staticmethod
    def adbInit():
        adb="adb"
        p1=Popen([adb,"kill-server"])
        p1.wait()
        time.sleep(1)
        p2=Popen([adb,"start-server"])
        p2.wait()
        time.sleep(5)
        log.debug("initialing the adb server")

    """getDevicesList return the devices list"""

    @staticmethod
    def getDeviceList():
        adb="adb"
        p=Popen([adb,"devices"],stdout=PIPE)
        info=p.stdout.read()
        info_list=info.split("\n")
        info_list=info_list[1:-2]
        result=[]
        for info in info_list:
            tmp=info.split("\t")
            result.append(tmp[0])
        return result
    @staticmethod
    def launchDevice():
        genymotion = "/home/genymotion/player"
        p1 = Popen([genymotion, "--vm-name", "Custom Phone - 5.1.0 - API 22 - 768x1280"])
        # p2 = Popen([genymotion, "--vm-name", "Custom Phone - 5.0.0 - API 21 - 768x1280"])
        time.sleep(20)
        log.debug("genymotion success launch")
    @staticmethod
    def getMainActivity(path):
        pckname = ""
        lchname = ""
        p2 = Popen([aapt, "d", "badging", path], stdout=PIPE)
        info = p2.stdout.read()
        info_list = info.split("\n")
        for element in info_list:
            ret = element.find("package: name='")
            if ret > -1:
                pcklen = len("package: name='")
                e = element.find("'", pcklen + 1)
                pckname = element[pcklen:e]
            ret2 = element.find("launchable-activity: name='")
            if ret2 > -1:
                lchlen = len("launchable-activity: name='")
                e = element.find("'", lchlen + 1)
                lchname = element[lchlen:e]
        result = pckname + "/" + lchname
        return result
    @staticmethod
    def getPackageName(path):
        return  InitUtil.getMainActivity(path).split("/")[0]
    @staticmethod
    def getPointListByUiDump(packname):
        p=PointElement()
        rpmap=p.getClickPointMap()
        # rpmap={}
        l=[]
        for key,value in rpmap.items():
            tmp=[]
            tmp.append(int(key[0]))
            tmp.append(int(key[1]))
            tmp.append(value)
            # log.debug("--标题坐标:(%s,%s):标题内容:%s--"%(key[0],key[1],value))
            print "--标题坐标:(%s,%s) :标题内容:%s"%(key[0],key[1],value)
            l.append(tmp)
        l = sorted(l, key=lambda d: d[1])
        return l

        # """l:[x,y,titleinfo]"""

    @staticmethod
    def saveSeqAndText(seqandtitlestr):
        print "in util is"+seqandtitlestr
        seqandtitlestr = seqandtitlestr.decode("utf-8")
        p1=Popen(["python","saveseqandtitle.py",seqandtitlestr])
        p1.wait()
    @staticmethod
    def isNetResponse(packName,deviceId):
        print "---开始分析Android端APP:%s网络信息----"%packName
        amnt = AppNetMonitor(deviceId)
        log.debug("create AppNetMonitor Object")
        pid = amnt.getPidByPackage(packName)
        if pid <> "":
            amnt.getAppStatusFile(pid)
            uid = amnt.getAppUid()
            plist = amnt.parseTcpFile(uid)
            if plist == []:
                print "----APP %s 无网络响应,正在重新分析和判断----" % packName
                time.sleep(5)
                for i in range(TIMES):
                    plist = amnt.parseTcpFile(uid)
                    if len(plist) > 0:
                        print "APP %s有网络响应，网络信息如下:" % packName
                        for l in plist:
                            print "UID:%s,服务器地址:%s,服务器端口 :%s,本地IP:%s,本地端口:%s" % tuple(l)
                        return True
                    else:
                        if i + 1 == TIMES:
                            print"----APP %s 无网络响应,准备停止运行APP----" % packName
                            log.error("----APP %s has no net response,ready to stop APP----" % packName)
                            return False
                        else:
                            time.sleep(5)
                            print "----APP %s 无网络响应,正在重新分析和判断----" % packName
                            continue
            else:
                print "APP %s有网络响应，网络信息如下:" % packName
                for l in plist:
                    print "UID:%s,服务器地址:%s,服务器端口 :%s,本地IP:%s,本地端口:%s" % tuple(l)
                return True
        else:
            log.debug("%s is not running now" % packName)

    @staticmethod
    def runOcr():
        imagetask = ImageTaskProducer("/home/pic", "/home/finish_pic")
        imagetask.setDaemon(True)
        imagetask.start()
        gettitletask = GetTitleInfo()
        ocrpool = []
        for i in range(4):
            ocrpool.append(OcrThread())
        for ocr in ocrpool:
            ocr.setDaemon(True)
            ocr.start()
        gettitletask.start()
        taskShuffle = ShuffleTreeBuildTask()
        taskShuffle.start()
