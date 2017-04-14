#-*- coding:UTF-8 -*-
import sys,signal,dpkt
reload(sys)
sys.setdefaultencoding('utf-8')
import re,os,time
from subprocess import Popen,PIPE,call
import logging.config
TIMES=5
curdir=os.getcwd()
logcfg=os.path.join(curdir,"logging.conf")
logging.config.fileConfig(logcfg)
log = logging.getLogger("debug01")
class AppNetMonitor():
    def __init__(self,devicename):
        self.deviceName=devicename
        self.srcPortList=[]
        self.tcppath="./net/tcp"
        self.tcp6path="./net/tcp6"
    def getIpAddress(self,hexa):
        v = int(hexa, 16)
        adr = (v >> 24) | (v << 24) | ((v << 8) & 0x00FF0000) | ((v >> 8) & 0x0000FF00)
        return str((adr >> 24) & 0xff) + "." + str((adr >> 16) & 0xff) + "." + str((adr >> 8) & 0xff) + "." + str(
            adr & 0xff)
    def getNetPort(self,hexa):
        return int(hexa, 16)
    def getPidByPackage(self,packname):
        p1=Popen(["adb","shell","ps"],stdout=PIPE)
        strlist=p1.stdout.readlines()
        for line in strlist:
            line=re.split("\s+",line)
            if line[8]==packname:
                return line[1]
        return ""
    def getAndroidTcpFile(self):
        path="/proc/"+"/net/tcp"
        if os.path.exists('./net/tcp'):
            os.remove('./net/tcp')
        p1=Popen(["adb","-s",self.deviceName,"pull",path,"./net/"],stdout=PIPE)
        p1.stdout.read()
        p1.wait()

    def getAndroidTcp6File(self):
        path = "/proc/" + "/net/tcp6"
        if os.path.exists('./net/tcp6'):
            os.remove('./net/tcp6')
        p1 = Popen(["adb", "-s", self.deviceName, "pull", path, "./net/"], stdout=PIPE)
        p1.stdout.read()
        p1.wait()

        log.debug("---pull tcpfile to .")
    def getAppStatusFile(self,pid):
        path = "/proc/" + str(pid) + "/status"
        if os.path.exists('./net/status'):
            os.remove('./net/status')
        p1 = Popen(["adb","-s",self.deviceName, "pull", path, "./net/"],stdout=PIPE)
        p1.stdout.read()
        p1.wait()
        log.debug("--pull status to ./net/")
    def getAppUid(self):
        count=0
        curdir=os.getcwd()
        statuspath=os.path.join(curdir,"net/status")
        file=open(statuspath)
        line=""
        while count<7:
            count=count+1
            line=file.readline()
        field=re.split("\s+",line)
        return field[1]
    def parseTcpFile(self,uid):
        log.debug("parse tcp file")
        self.getAndroidTcpFile()
        tcpfile = open(self.tcppath)
        linelist=tcpfile.readlines()
        for line in linelist:
            line=line.lstrip()
            line=line.rstrip()
            field = re.split('\s+', line)
            if field[0]=="sl":
                continue
            srclist = field[1].split(":", 2)
            dstlist= field[2].split(":", 2)
            dstIp = self.getIpAddress(dstlist[0])
            dstPort=self.getNetPort(dstlist[1])
            srcIp = self.getIpAddress(srclist[0])
            srcPort=self.getNetPort(srclist[1])
            if field[7]==uid:
                # anslist
                if srcIp<>"0.0.0.0" and srcIp<>"127.0.0.1":
                    tmplist=[uid,dstIp,dstPort,srcIp,srcPort]
                    self.srcPortList.append(tmplist)
        return self.srcPortList#[uid,dstIp,dstport,srcIp,srcPort]
        tcpfile.close()

    def parseTcp6File(self, uid):
        log.debug("parse tcp6 file")
        self.getAndroidTcp6File()
        tcpfile = open(self.tcp6path)
        linelist = tcpfile.readlines()
        for line in linelist:
            line = line.lstrip()
            line = line.rstrip()
            field = re.split('\s+', line)
            if field[0] == "sl":
                continue
            srclist = field[1].split(":", 2)
            dstlist = field[2].split(":", 2)
            dstIp = self.getIpAddress(dstlist[0])
            dstPort = self.getNetPort(dstlist[1])
            srcIp = self.getIpAddress(srclist[0])
            srcPort = self.getNetPort(srclist[1])
            if field[7] == uid:
                # anslist
                if srcIp <> "0.0.0.0" and srcIp <> "127.0.0.1":
                    tmplist = [uid, dstIp, dstPort, srcIp, srcPort]
                    self.srcPortList.append(tmplist)
        return self.srcPortList  # [uid,dstIp,dstport,srcIp,srcPort]
        tcpfile.close()

def getAppCapByPort(device):
    print "---开始在Android端抓取TCP数据包----"
    p1=Popen(["adb","-s",device,"shell","tcpdump -i eth1  -s 0 -vv -w /tmp/appnet.pcap -c 80 tcp "],stdout=PIPE)
    p1.stdout.read()
    p1.wait()
    # p1.wait()
    print "------pcap process finished----"
    p2=Popen(["adb","-s",device,"pull","/tmp/appnet.pcap","./net/"],stdout=PIPE)
    p2.stdout.read()
    p2.wait()

if __name__ == '__main__':
    amnt=AppNetMonitor("192.168.56.101:5555")
    log.debug("创建网络监控对象")
    packName='com.tencent.reading'
    pid=amnt.getPidByPackage(packName)
    print "pid:"+pid
    if pid<>"":
        amnt.getAppStatusFile(pid)
        uid=amnt.getAppUid()
        # print "uid:"+uid
        plist=amnt.parseTcpFile(uid)
        if plist==[]:
            # log.debug("----APP %s 无网络响应,正在重新分析和判断----"%packName)
            print "----APP %s 无网络响应,正在重新分析和判断----" % packName
            count=0
            time.sleep(2)
            for i in range(TIMES):
                plist = amnt.parseTcpFile(uid)
                if len(plist)>0:
                    print "APP %s 有网络数据交互，准备进行数据包分析----"%packName
                    for l in plist:
                        print "UID:%s,服务器地址:%s,服务器端口 :%s,本地IP:%s,本地端口:%s" % tuple(l)
                        # printPcap(plist)
                else:
                    if i+1==TIMES:
                        print"----APP %s 无网络响应,准备停止运行APP----" % packName
                        log.error("----APP %s has no net response,ready to stop APP----" % packName)
                        # return False
                    else:
                        time.sleep(2)
                        continue
        else:
            print "APP %s有网络响应，网络信息如下:"%packName
            for l in plist:
                print "UID:%s,服务器地址:%s,服务器端口 :%s,本地IP:%s,本地端口:%s"%tuple(l)
        # print plist
        #     printPcap(plist)
    else:
        log.debug("%s is not running now"%packName)


