#-*- coding:UTF-8 -*-
import sys,os,cv2
reload(sys)
sys.setdefaultencoding('utf-8')
import traceback,base64,json
from redis_p import Task
import threading,os,time,logging.config,Image
from app_ocr import WrapInfo,PicSumWrap,ImageWrap
logging.config.fileConfig("/home/hw/python_code/logging.conf")
log = logging.getLogger("debug01")

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
if __name__=="__main__":
    itp=ImageTaskProducer("/home/pic","/home/finish_pic/")
    # itp.setDaemon(True)
    itp.start()
