#-*- coding:UTF-8 -*-

"""
此自动运行组件通过monkeyrunner提供的API实现
"""
import sys,os,cv2
reload(sys)
sys.setdefaultencoding('utf-8')
import tesserocr,redis,json
from xml.dom.minidom import Document
import threading
from PIL import Image
import Queue,base64
import time,logging.config
import traceback
from redis_p import Task
from subprocess import Popen
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")

reload(sys)
sys.setdefaultencoding('utf-8')
""""
ocrQue用于图片分发现场和ocr线程通信
用于ocr线程识别完成之后作为生产者将识别后的结果放入combineQue中，Shuffle线程根据包名称进场分类和重组任务创建与下发

"""
ocrQue=Queue.Queue(10)
combineQue=Queue.Queue(10)
picSumQue=Queue.Queue(5)
apkTaskQue=Queue.Queue(5)


class ImageTaskProducer(threading.Thread):
    def __init__(self,pichomepath,picfinishpath):
        threading.Thread.__init__(self)
        self.dirPath=pichomepath
        self.finishPath=picfinishpath
        self.redisImageTask=Task("imagetaskque")
        # self.que=ocrQue
        # self.setDaemon(True)
        self.endReachCount=0
        self.tmpWrapImageList=[]
        self.setName("ImageTaskProducerThread")
        # self.picsumque=picSumQue
        self.picWrapSumTask=Task("picwrapsum")
        self.apkPicCountMap={}
        if not os.path.exists(self.finishPath):
            os.mkdir(self.finishPath)
    def setdirPath(self,path):
        self.dirPath=path
    def setFinishPath(self,path):
        self.finishPath=path
    def run(self):
        self.putOcrTaskFromDir()

    def putOcrTaskFromDir(self):
        if os.path.isdir(self.dirPath):
            log.debug("get image task from %s to Queue----"%self.dirPath)
            while True:
                dirList=os.listdir(self.dirPath)
                if len(dirList)==0:
                    log.debug("no image in %s"%self.dirPath)
                    time.sleep(10)
                else:
                    for appdir in dirList:
                        tmppackname=appdir
                        appdir=os.path.join(self.dirPath,appdir)
                        if os.path.isdir(appdir):
                            secondDirList=os.listdir(appdir)
                            if len(secondDirList)==0:
                                if self.endReachCount>0:#最后一张图片已经来过，而且当前文件夹下已经没有文件了
                                    for tmp in self.tmpWrapImageList:
                                        if tmppackname==tmp.getPackName():
                                            emptydir = os.path.join(self.dirPath,tmppackname)
                                            self.redisImageTask.pushPicTask(tmp)
                                            time.sleep(5)  # 最后的图片延迟一点，保证其他图片先被处理
                                            picwrap=PicSumWrap(self.apkPicCountMap[tmppackname],tmppackname)
                                            seriwrapsum = json.dumps(picwrap, default=lambda obj: obj.__dict__,
                                                                       ensure_ascii=False)
                                            # self.picsumque.put(PicSumWrap(self.apkPicCountMap[tmppackname],tmppackname))#告知此apk总共有多少张快照
                                            self.picWrapSumTask.pushTask(seriwrapsum)
                                            os.rmdir(emptydir)
                                            self.endReachCount=self.endReachCount-1
                                log.debug("%s is empty"%appdir)
                                time.sleep(5)
                            else:
                                if not self.apkPicCountMap.has_key(tmppackname):
                                    self.apkPicCountMap[tmppackname]=0
                                time.sleep(1)#保证已经获取的图片名称所对应的文件已经写完。
                                piccount=len(secondDirList)
                                tmpcount = self.apkPicCountMap[tmppackname]
                                tmpcount = tmpcount + piccount
                                self.apkPicCountMap[tmppackname] = tmpcount
                                for pic in secondDirList:
                                    pic_tmp=pic
                                    destdir=os.path.join(self.finishPath,tmppackname)
                                    if not os.path.exists(destdir):
                                        os.mkdir(destdir)
                                    destPic = os.path.join(destdir, pic_tmp)
                                    pic=os.path.join(appdir,pic)
                                    print pic
                                    image = cv2.imread(pic)
                                    global bim
                                    bim=image

                                    try:
                                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                                        ret, bim = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
                                    except:
                                        bim=image

                                    seq = pic_tmp.split(".")[0]
                                    bpath=os.path.join("/tmp/appimage",appdir.split("/")[-1])
                                    if not os.path.exists(bpath):
                                        os.makedirs(bpath)
                                    bfile=os.path.join(bpath,seq+".png")
                                    cv2.imwrite(bfile,bim)
                                    f=open(bfile,"rb")
                                    strbImage = base64.b64encode(f.read())

                                    if seq=='e-n-d':
                                        imageData = ImageWrap(strbImage, appdir.split("/")[-1], seq)
                                        seriiamgedata = json.dumps(imageData, default=lambda obj: obj.__dict__,ensure_ascii=False)
                                        self.tmpWrapImageList.append(seriiamgedata)
                                        os.remove(pic)
                                        self.endReachCount=self.endReachCount+1
                                        continue
                                    else:
                                        imageData=ImageWrap(strbImage,appdir.split("/")[-1],seq)
                                        seriiamgedata = json.dumps(imageData, default=lambda obj: obj.__dict__, ensure_ascii=False)
                                        self.redisImageTask.pushPicTask(seriiamgedata)
                                        os.remove(bfile)
                                        # self.que.put(imageData)
                                        log.debug("mv %s to %s"%(pic_tmp,self.finishPath))
                                        try:
                                            log.info("pic=%s!!!"%pic)
                                            log.info(("destpic=%s"%destPic))
                                            os.rename(pic,destPic)
                                        except:
                                            log.error(traceback.print_exc())
                        else:
                            log.debug("%s is not dir"%pic)
                            try:
                                os.remove(appdir)
                            except:
                                traceback.print_exc()
                            pass

class GetTitleInfo(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'titleque'
        self.combineque=combineQue
    def getTask(self):
        d = self.rcon.blpop(self.queue, 0)[1]
        wrap = json.loads(d)
        titlewrap=WrapInfo(wrap["packName"],wrap["info"],wrap["seq"])
        return titlewrap
    def run(self):
        log.debug("----------------GetTitleInfo start----------------")
        while True:
            titlewrap=self.getTask()
            self.combineque.put(titlewrap)


"""用于分布式集群中多主机之间图片的拷贝与发送"""

class PicSumWrap():
    def __init__(self,picsum,packname):
        self.picSum=picsum
        self.packName=packname
    def getPicSum(self):
        return self.picSum
    def setPicSum(self,picsum):
        self.picSum=picsum
    def setPackName(self,pckname):
        self.packName=pckname
    def getPackName(self):
        return self.packName

class WrapInfo():
    def __init__(self,packname="",text="",seq=""):
        self.packName=packname
        self.info=text
        self.seq=seq
        self.childList=[]
        self.childMap={}
    def setPackName(self,packname):
        self.packName=packname
    def getPackName(self):
        return self.packName
    def setInfo(self,info):
        self.info=info
    def getInfo(self):
        return self.info
    def addInfo(self,str):
        self.info=self.info+str
    def addChildList(self,child):
        self.childList.append(child)
    def setSeq(self,seq):
        self.seq=seq
    def getSeq(self):
        return self.seq
    def addChildMap(self,seq,child):
        self.childMap[seq]=child

"""用于传输OCR任务队列中数据的包裹"""
class ImageWrap():
    def __init__(self,image,packname,seq):
        self.image=image
        self.packName=packname
        self.imageSeq=seq
    def setImage(self,image):
        self.image=image
    def setPackName(self,packname):
        self.packName=packname
    def setImageSeq(self,seq):
        self.imageSeq=seq
    def getImageSeq(self):
        return self.imageSeq
    def getImage(self):
        return self.image
    def getPackName(self):
        return self.packName
    def getSeq(self):
        return self.imageSeq


class GetImageTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.queue = 'imagetaskque'
        self.ocrQue=ocrQue
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
        # log.debug("write %s to %s"%(picname,curdir))
        time.sleep(1)
        bim=Image.open(picname,"r")
        wrapimage=ImageWrap(wrap["packName"],bim,wrap["imageSeq"])
        return wrapimage
    def run(self):
        log.debug("--------Get image task start----------")
        while True:
            wrapimage=self.getTask()
            log.debug("put %s to ocrQue"%wrapimage.getImageSeq())
            self.ocrQue.put(wrapimage)


"""根据任务分配器分配的队列，读取对应的combineQue中的任务，在内存中建立一颗wrap节点树,每一个APP会有一个ContentRecombineThread"""
class ContentRecombineThread(threading.Thread):
    def __init__(self,que,returnque):
        threading.Thread.__init__(self)
        self.root=WrapInfo()
        self.setName("contentRecombineThread")
        self.combineque=que
        self.finishFlag=False
        self.returnQue=returnque
        self.endFlag=False
    def getRoot(self):
        return self.root
    def isTreeBuildFinish(self):
        if not self.finishFlag:
            log.info("building tree for %s is building"%self.root.getPackName())
            return False
        else:
            return True

    def run(self):
        log.debug("ContentRecombineThread running----")
        self.buildTree()
        packname = self.root.getPackName()
        log.debug("finish build %s wrap tree----"%packname)
        xml=XmlCreateUtil(self.root)
        xml.buildXmlTree()
        log.debug("finish build %s XML tree----" % packname)
        xml.saveAsFile(packname)
        log.debug("apk %s finish ALL TASK!!!!!!!!!!"%packname)
        self.returnQue.put(packname)#告知任务回收器，任务已经完成

"""@TreeBuildTaskRecyle 用于回收任务分配器中创建的队列和线程"""
class TreeBuildTaskRecyle(threading.Thread):
    def __init__(self,shufflemap,returnque):
        threading.Thread.__init__(self)
        self.taskmap=shufflemap
        self.returnQue=returnque
        self.setDaemon(True)
        self.setName("TreeBuildTaskRecyleThread")
    def recycleTaskMap(self,packname):
        del self.taskmap[packname]
        log.info("recycle the %s'building-tree threading----"%packname)
        log.info("finish %s tree build,del que and thread list!!!!!!!!" % packname)
    def run(self):
        while True:
            for value in self.taskmap.values():
                global str
                str=""
                try:
                    str=self.returnQue.get(timeout=5)
                    if str <> "":
                        self.recycleTaskMap(str)
                        time.sleep(2)
                except:
                    log.debug("no build tree thread was finished!----")
                    time.sleep(2)
            time.sleep(2)

"""从combineQue中取wrapinfo任务，作为任务分配器，把对应的任务分到所对应的树，负责洗牌算法"""
class ShuffleTreeBuildTask(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.que=combineQue
            self.shuffleMap={}
            self.returnQue=Queue.Queue(4)
            self.setName("ShuffleTreeBuildTaskThread")
            # self.picSumQue=picSumQue
            self.picWrapSumTask = Task("picwrapsum",timeout=5)
        def getTaskList(self, packname):
            if not self.shuffleMap.has_key(packname):
                que = Queue.Queue(10)
                log.debug("new a Queue for apk %s build Node tree----" % packname)
                buildthread = XmlCreateUtil(que,self.returnQue)
                log.debug("new a node-tree-build-Thread for %s ----" % packname)
                count=0
                endwrapinfo=WrapInfo()
                queAndthread = [que, buildthread,count,endwrapinfo]
                self.shuffleMap[packname] = queAndthread
                return self.shuffleMap[packname]
            else:
                return self.shuffleMap[packname]

        def run(self):
            log.debug("-----ShuffleTreeBuildTask begin-------------")
            taskrecycle=TreeBuildTaskRecyle(self.shuffleMap,self.returnQue)
            taskrecycle.start()
            while True:
                wrap = self.que.get()
                packname = wrap.getPackName()#根据包名来分配APK的任务，进行洗牌
                seq = wrap.getSeq()
                log.debug("ShuffleTreeBuildTask get wrap seq=%s from combineQue----"%seq)
                if seq=='e-n-d':
                    try:
                        picWrapCount=self.picWrapSumTask.getTask()
                        picsum=picWrapCount["picSum"]
                    except:
                        pass
                        if self.shuffleMap[packname][2]==picsum:
                            self.shuffleMap[packname][0].put(wrap)
                        else:
                            pass
                            self.taskShuffle[packname][3]=wrap#把e-n-d结点保存起来


                if not self.shuffleMap.has_key(packname):#如果包名在任务分配器当中不存在，则新建队列和建树线程
                    tasklist=self.getTaskList(packname)
                    tasklist[1].start()
                    tasklist[0].put(wrap)
                else:
                    self.shuffleMap[packname][0].put(wrap)
                    self.shuffleMap[packname][2]= self.shuffleMap[packname][2]+1
                    log.debug("put wrap to que,for %s ----" % packname)
                    log.debug("in shuffle seq==%s ****" % seq)
                    if self.shuffleMap[packname][3].getSeq()=='e-n-d':#尾结点已经保存进去了，才进行以下的判断
                        if self.shuffleMap[packname][2] == picsum:
                            self.shuffleMap[packname][0].put(wrap)
                        
"""XmlCreateUtil根据所对应的队列传来的任务，组建XMl结点树"""
class XmlCreateUtil(threading.Thread):
    def __init__(self,que,returnque):
        threading.Thread.__init__(self)
        self.wraproot=WrapInfo()
        self.doc = Document()
        self.rootNode = self.doc.createElement('appinfos')
        self.doc.appendChild(self.rootNode)
        self.firstlevelMap={}
        self.treeBuildQue=que
        self.returnQue=returnque
        self.picSumQue=picSumQue
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S")
        self.rootNode.setAttribute("analysis-time",timeStr)

    def run(self):
        piccount=0
        while True:
            wrap=self.treeBuildQue.get()
            seq=wrap.getSeq()
            packname=wrap.getPackName()
            if self.wraproot.getPackName()=="":
                self.wraproot.setPackName(packname)
                self.rootNode.setAttribute("packname",packname)
            """收到e-n-d后，检查"""
            if seq=='e-n-d':
                # picsumwrap=self.picSumQue.get(timeout=0.5)
                # picsumwrap.getPicSum()
                self.saveAsFile(packname)
                self.returnQue.put(packname)#完成时，往返回值队列返回APP包名，告知任务回收器回收任务
                log.debug("%s XML Tree Build  fininsh"%packname)
                break

            if len(seq)==5:
                if not self.firstlevelMap.has_key(seq):
                    firstLevelNode=self.doc.createElement(seq)
                    # firstLevelNode.
                    firstLevelNode.setAttribute("title",wrap.getInfo())
                    # titleNode=self.doc.createElement()
                    # firstLevelNode.setAttribute("")
                    self.firstlevelMap[seq]=firstLevelNode
                    self.rootNode.appendChild(firstLevelNode)
                else:
                    firstLevelNode=self.firstlevelMap[seq]
                    firstLevelNode.setAttribute("title",wrap.getInfo())

            elif len(seq)==7:
                seqHead=seq[0:5]
                if self.firstlevelMap.has_key(seqHead):
                    secondLevelNode=self.doc.createElement(seq)
                    secondLevelNode.setAttribute("infotext",wrap.getInfo())
                    firstLevelNode=self.firstlevelMap[seqHead]
                    firstLevelNode.appendChild(secondLevelNode)
                else:
                    firstLevelNode=self.doc.createElement(seqHead)
                    firstLevelNode.setAttribute("title","")
                    self.firstlevelMap[seqHead]=firstLevelNode
                    self.rootNode.appendChild(firstLevelNode)

    def saveAsFile(self, packname):
        timeStr = time.strftime("%Y%m%d%H%M%S")
        curpath = os.getcwd()
        xmldir = os.path.join(curpath, "xmldir")
        if not os.path.exists(xmldir):
            os.mkdir(xmldir)
        xmlname = timeStr + packname + ".xml"
        xmlname = os.path.join(xmldir, xmlname)
        f = open(xmlname, 'w')
        f.write(self.doc.toprettyxml(indent='\t'))
        f.close()
        log.debug("----sava the xml file % ----- ")
        endtime=time.clock()
        appruntime = packname + "_" + timeStr 
        # appruntime = packName + "_" + timeStr + "_" + str(begintime) + "\n"
        f1=open("/home/hw/python_code/endtime","a")
        f1.write(str(appruntime))
        f1.flush()
        f1.close()


"""从ocrque取任务，并调用OCR引擎进行识别,识别之后放入combineQue,进行下一步的Shuffle"""
class OcrThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.ocrque=ocrQue
        self.combineque=combineQue
        self.setDaemon(True)
        # self.redisTask=Task(("imagetaskque")
        self.setName("OCR Thread")
    def run(self):
        while True:
            wrapimage=self.ocrque.get()
            log.debug("Ocrthread get wrapimage from ocrque")
            wrapinfo=AppOcrUtil.getWrapInfoOfImage(wrapimage)
            if wrapinfo.getSeq()=='e-n-d':
                log.debug("%s's e-n-d wrapinfo put into combineQue"%wrapinfo.getPackName())
            else:
                log.debug("Ocrthread put wrapinfo to combineque for %s---"%wrapinfo.getPackName())
            self.combineque.put(wrapinfo)

"""AppOcrUtil负责图片的预处理以及图片的识别"""
class AppOcrUtil():
    def __init__(self):
        pass
    @staticmethod
    def getPackNameFromPath(path):
        return path.split("/")[-2]
    @staticmethod
    def getSeqFromPath(path):
        picName=path.split("/")[-1]
        return picName.split(".")[0]
    @staticmethod
    def getWrapInfoOfImage(imagewrap):
        wrap=WrapInfo()
        seq=imagewrap.getSeq()
        if seq=='e-n-d':
            wrap.setInfo("-------------the end of the process------------")
            wrap.setPackName(imagewrap.getPackName())
            wrap.setSeq(imagewrap.getSeq())
            log.debug("-------------the end of the process------------")
            return wrap
        else:
            image=imagewrap.getImage()
            result=tesserocr.image_to_text(image,lang="chi_sim").encode('utf-8')
            log.debug("finish %s image OCR"%imagewrap.getImageSeq())
            result=AppOcrUtil.removeSpace(result)
            wrap.setInfo(result)
            wrap.setPackName(imagewrap.getPackName())
            wrap.setSeq(imagewrap.getSeq())
            log.debug("image %s' OCR result is %s----"%(imagewrap.getImageSeq()+'.png',result))
            return wrap#返回包裹着的信息块

    @staticmethod
    def removeSpace(str):
        str = str.replace(" ", "").replace("\t", "").strip()
        str=str.replace("\n"," ")
        return str


"""把图片封装后放入ocrQue队列当中，供OcrThread取"""
class ImageTaskProducerSingalServer(threading.Thread):
    def __init__(self,pichomepath,picfinishpath):
        threading.Thread.__init__(self)
        self.dirPath=pichomepath
        self.finishPath=picfinishpath
        self.que=ocrQue
        self.setDaemon(True)
        self.endReachCount=0
        self.tmpWrapImageList=[]
        self.setName("ImageTaskProducerThread")
        self.picsumque=picSumQue
        self.apkPicCountMap={}
        if not os.path.exists(self.finishPath):
            os.mkdir(self.finishPath)
    def setdirPath(self,path):
        self.dirPath=path
    def setFinishPath(self,path):
        self.finishPath=path
    def run(self):
        self.putOcrTaskFromDir()

    def putOcrTaskFromDir(self):
        if os.path.isdir(self.dirPath):
            log.debug("get image task from %s to Queue----"%self.dirPath)
            while True:
                dirList=os.listdir(self.dirPath)
                if len(dirList)==0:
                    log.debug("no image in %s"%self.dirPath)
                    time.sleep(10)
                else:
                    for appdir in dirList:
                        tmppackname=appdir
                        appdir=os.path.join(self.dirPath,appdir)
                        if os.path.isdir(appdir):
                            secondDirList=os.listdir(appdir)
                            if len(secondDirList)==0:
                                if self.endReachCount>0:#最后一张图片已经来过，而且当前文件夹下已经没有文件了
                                    for tmp in self.tmpWrapImageList:
                                        if tmppackname==tmp.getPackName():
                                            emptydir = os.path.join(self.dirPath,tmppackname)
                                            self.que.put(tmp)
                                            time.sleep(5)  # 最后的图片延迟一点，保证其他图片先被处理
                                            PicSumWrap(self.apkPicCountMap[tmppackname],tmppackname)
                                            self.picsumque.put(PicSumWrap(self.apkPicCountMap[tmppackname],tmppackname))#告知此apk总共有多少张快照
                                            os.rmdir(emptydir)
                                            self.endReachCount=self.endReachCount-1
                                log.debug("%s is empty"%appdir)
                                time.sleep(5)
                            else:
                                if not self.apkPicCountMap.has_key(tmppackname):
                                    self.apkPicCountMap[tmppackname]=0
                                time.sleep(1)#保证已经获取的图片名称所对应的文件已经写完。
                                piccount=len(secondDirList)
                                tmpcount = self.apkPicCountMap[tmppackname]
                                tmpcount = tmpcount + piccount
                                self.apkPicCountMap[tmppackname] = tmpcount
                                for pic in secondDirList:
                                    pic_tmp=pic
                                    destdir=os.path.join(self.finishPath,tmppackname)
                                    if not os.path.exists(destdir):
                                        os.mkdir(destdir)
                                    destPic = os.path.join(destdir, pic_tmp)
                                    pic=os.path.join(appdir,pic)
                                    image = Image.open(pic)
                                    image = image.convert("L")#灰度化
                                    table = []
                                    threshold = 127
                                    for i in range(256):
                                        if i < threshold:
                                            table.append(0)  # black
                                        else:
                                            table.append(1)  # white
                                    bim = image.point(table, "1")
                                    seq=pic_tmp.split(".")[0]
                                    if seq=='e-n-d':
                                        self.tmpWrapImageList.append(ImageWrap(bim,appdir.split("/")[-1], seq))
                                        os.remove(pic)
                                        self.endReachCount=self.endReachCount+1
                                        continue
                                    else:
                                        imageData=ImageWrap(bim,appdir.split("/")[-1],seq)
                                        self.que.put(imageData)
                                        log.debug("mv %s to %s"%(pic_tmp,self.finishPath))
                                        try:
                                            log.info("pic=%s!!!"%pic)
                                            log.info(("destpic=%s"%destPic))
                                            os.rename(pic,destPic)
                                        except:
                                            log.error(traceback.print_exc())
                        else:
                            log.debug("%s is not dir"%pic)
                            try:
                                os.remove(appdir)
                            except:
                                traceback.print_exc()
                            pass

if __name__=="__main__":
    imagetask=ImageTaskProducer("/home/pic","/home/finish_pic")
    imagetask.setDaemon(True)
    imagetask.start()
    imagetaskreceiver=GetImageTask()
    imagetaskreceiver.start()
    gettitletask=GetTitleInfo()
    ocrpool=[]
    for i in range(2):
        ocrpool.append(OcrThread())
    for ocr in ocrpool:
        ocr.setDaemon(True)
        ocr.start()
    gettitletask.start()
    taskShuffle=ShuffleTreeBuildTask()
    taskShuffle.start()




