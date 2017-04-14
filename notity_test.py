#-*- coding:UTF-8 -*-
import sys,signal
reload(sys)
import os
import datetime,time
import threading
from my_log import AppLog
import pyinotify
import logging
import Queue
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_DELETE, IN_CREATE, IN_MODIFY


class AppTaskEvent(ProcessEvent):
    #自定义写入那个文件，可以自己修改
    def process_IN_CREATE(self, event):
        print "CREATE event:", event.pathname
        AppLog.debug("write apk into taskdir")
        getApkTaskFromDir()

    def process_IN_DELETE(self, event):
        print "DELETE event:", event.pathname
        logging.info("DELETE event : %s  %s" % (os.path.join(event.path,event.name),datetime.datetime.now()))

class AppTask(threading.Thread):
    def __init__(self,path):
        self.queue=Queue.Queue(5)
        self.apkDir=path
        self.eventHand=AppTaskEvent()
    def watchAppDir(self):
        # watch manager
        wm = WatchManager()
        wm.add_watch(self.apkDir, IN_CREATE | IN_DELETE, rec=True)
        # event handler
        eh = self.eventHand
        # notifier
        notifier = Notifier(wm, eh)
        notifier.loop()
    def getApkTaskFromDir(self):
        try:
            if os.path.isdir(self.apkDir):
                dirList = os.listdir(self.dirPath)
                for dir in dirList:
                    apk = os.path.join(self.apkDir, dir)
                    finishDir=os.path.join(os.getcwd(),"app_finish")
                    destFile=os.path.join(finishDir,dir)
                    os.rename(apk,destFile)
                    self.queue.put(apk)
        except:
            AppLog.error("exception happend in getapktaskfromdir")


def watchAppDir():
    # watch manager
    wm = WatchManager()
    wm.add_watch("/home/apkdir", IN_CREATE | IN_DELETE, rec=True)
    # event handler
    eh = AppTaskEvent()
    # notifier
    notifier = Notifier(wm, eh)
    notifier.loop()

def getApkTaskFromDir():
    try:
        dirPath="/home/apkdir"
        if os.path.isdir(dirPath):
            dirList = os.listdir(dirPath)
            print dirList
            time.sleep(2)
            for dir in dirList:
                apk = os.path.join(dirPath, dir)
                finishDir = os.path.join(os.getcwd(), "app_finish")
                destFile = os.path.join(finishDir, dir)
                AppLog.debug("mv apk to the dest__________________________________________")
                os.rename(apk, destFile)
                # self.queue.put(apk)
    except:
        pass

if __name__ == '__main__':
    test={}
    test[1]=2
    test["fd"]=4
    print test[1]
    print test["fd"]