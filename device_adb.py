#-*- coding:UTF-8 -*-
import sys,signal,threading
from util import InitUtil
reload(sys)
sys.setdefaultencoding('utf-8')
import os,time,Image,logging.config
from datetime import datetime
from subprocess import PIPE,Popen,call

repeatTimesOnError=2
idCheckTimes=20
DEBUG=True
waitForConnectionTime=10
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")

class AppImage():
    def __init__(self,path):
        if not isinstance(path,Image.Image):
            self.appImage=Image.open(path)
        elif isinstance(path,Image.Image):
            self.appImage=path
        else:
            pass
    def setAppImage(self,img):
        self.appImage=img
    def getImage(self):
        return self.appImage
    def getSubAppImage(self,box):
        region = self.appImage.crop(box)
        tmp=AppImage(region)
        # tmp.setAppImage(region)
        return tmp
    def writeAppImage(self,path):
        self.appImage.save(path)

    def sameAs(self, appimag2, percent):
        if self.appImage.size <> appimag2.getImage().size:
            return False
        else:
            diff = 0
            """resize，格式转换，把图片压缩成16*16大小，ANTIALIAS是抗锯齿效果开启，“L”是将其转化为 """
            imag2 = appimag2.getImage().resize((32, 32), Image.ANTIALIAS).convert('L')
            self.appImage = self.appImage.resize((32, 32), Image.ANTIALIAS).convert('L')
            for w in range(0, imag2.size[0]):
                for h in range(0, imag2.size[1]):
                    if self.appImage.getpixel((w, h)) <> imag2.getpixel(((w, h))):
                        diff = diff + 1

            if percent > 1 - diff / imag2.size[0] * imag2.size[1]:
                return False
            else:
                return True

class AutoRunDevice(threading.Thread):
    def __init__(self,deviceId):
        log.debug("开始创建自动化运行设备 %s" % deviceId)
        self.deviceId = deviceId

    def stopAppByActivity(self,activity):
        p1=Popen(["adb","shell","-s","am force-stop",activity])
        log.debug("---stop activity %s---"%activity)
        p1.wait()
    def adbshell(self,cmd):
        p1=Popen(["adb","shell",cmd])
        p1.wait()

    def installPackage(self, apkname):
        log.debug("正在自动安装%s----"%apkname)
        p1=Popen(["adb","install",apkname],stdout=PIPE)
        log1=p1.stdout.read()
        if log1.find("INSTALL_FAILED_ALREADY_EXISTS")==-1:
            log.debug("%s 成功安装----"%apkname)
        else:
            log.debug("pack exist already")

    def takeSnapshot(self):
        call(["adb", "shell", "/system/bin/screencap -p /tmp/screenshot.png"])
        call(["adb", "pull", "/tmp/screenshot.png", "/tmp"])
        return AppImage("/tmp/screenshot.png")

    def unInstallAppByPackName(self,packname):
        call(["adb","uninstall",packname])
        log.debug("success remove the Packagename %s",packname)

    def exitGracefully(self, activity):
        signal.signal(signal.SIGINT, signal.getsignal(signal.SIGINT))
        self.stopAppByActivity(activity)
        sys.exit(1)

    def exitApp(self,activity):
        self.stopAppByActivity(activity)
        sys.exit(1)

    def home(self):
        call(["adb","shell","input","keyevent","KEYCODE_HOME"])
        time.sleep(1)
    def back(self):
        call(["adb", "shell", "input", "keyevent", "KEYCODE_BACK"])
        time.sleep(2.5)
    def sleep(self, seconds):
        time.sleep(seconds)
    def click(self, x, y):
        call(["adb","shell","input","tap",str(x),str(y)])
        time.sleep(1)
    def drag(self, x1, y1, x2, y2):
        call(["adb","shell","input","swipe",str(x1),str(y1),str(x2),str(y2)])
        time.sleep(0.5)
    def startActivity(self, activity):
        p1=Popen(["adb","shell","am","start","-an",activity],stdout=PIPE)
        p1.stdout.read()
        time.sleep(1)
        log.debug("success launch the activity %s"%activity)

    def debug(self,info):
        log.debug(info)
    def info(self,info):
        log.info(info)
    def error(self,info):
        log.error(info)

    def type(self, content):
        self.debug('device input the %s' % content)
        self.device.type(content)






