#-*- coding:UTF-8 -*-

"""
通过adb实现，调用了device_adb,apptaskSend,util
    1、APP自动运行组件的实现
    2、快照截图的实现

"""
import sys,logging.config
reload(sys)
sys.setdefaultencoding('utf-8')
import sys,time,os,Queue
from device_adb import AutoRunDevice
from  apptaskSend import AppTaskSender
from util import InitUtil
f1=open("/home/hw/python_code/starttime","a")
curdir=os.getcwd()
logcfg=os.path.join(curdir,"logging.conf")
logging.config.fileConfig(logcfg)
log = logging.getLogger("debug01")
deviceId='192.168.56.101:5555'
"""创建自动运行设备"""
device=AutoRunDevice(deviceId)
apptaskque=Queue.Queue(2)

def logRunTime(s,packname):
    timeStr = time.strftime("%Y%m%d%H%M%S")
    endtime = time.time()
    f1.write(packname+timeStr+"_"+str(endtime - s)+"\n")
    f1.flush()

def appAutoRun(path):
    log.debug("获取APP分析任务----")
    """获取包名称"""
    log.debug("开始对%s进行预处理"%path)
    packnameandactivity=InitUtil.getMainActivity(path)
    device.home()
    log.debug("预处理成功，获取到%s的包名和主Acitivity:%s"%(path,packnameandactivity))
    device.sleep(1)
    home_image=device.takeSnapshot()#保存主界面,用于后期的界面判定
    sub_home_image=home_image.getSubAppImage((400, 500, 700, 900))
    time.sleep(1)
    device.installPackage(path)
    packName=InitUtil.getPackageName(path)
    """启动主组件"""
    device.startActivity(packnameandactivity)
    """休眠5秒等广告界面过去"""
    device.sleep(5)
    log.debug("获取到%s 分析任务"%packName)
    netFlag=True
    # netFlag=InitUtil.isNetResponse(packName,deviceId)
    if netFlag==False:
        log.debug("uninstall %s"%packName)
        device.unInstallAppByPackName(packName)
        return

    """截取APP运行的第一张照片，用于后期比较"""
    first_image=device.takeSnapshot()
    sec_end_sub_image=first_image.getSubAppImage((400, 500, 700, 900))
    """每个APP创建一个文件夹用于存放截图"""
    dir_name=InitUtil.createPicDir(packName)
    begintime=time.time()
    """开始遍历逻辑"""
    global level
    level=0
    i=0
    num=8
    for i in range(num):
        """第一及快照的序列号"""
        firstlevelandseq= str(1)+"-" + str(i)
        """进行坐标点的采集"""
        pointlist=InitUtil.getPointListByUiDump(packName)
        titleimage=device.takeSnapshot()
        titleimage_name="/home/titledir/"+firstlevelandseq+".png"
        titleimage.writeAppImage(titleimage_name)
        """第一级页面，在点击之前截屏保存页面快照用于下次判断"""
        first_level_image1 = device.takeSnapshot()
        first_level_sub_image1 = first_level_image1.getSubAppImage((400, 500, 700, 900))
        """用于表示第一级页面中链接区域的序号置0,重新标号"""
        seq = 0
        """用于存储标题和序号信息"""
        seqandtitlestr=""
        for t in pointlist:
            """点击坐标点"""
            device.click(t[0],t[1])
            log.debug("点击（%s,%s）"%(t[0],t[1]))
            time.sleep(3)
            """发生点击操作后，截图"""
            click_image = device.takeSnapshot()
            click_sub_image = click_image.getSubAppImage((400, 500, 700, 900))
            if first_level_sub_image1.sameAs(sub_home_image, 0.90):
                logRunTime(begintime,packName)
                log.error("从一级页面返回到了主界面退出----,exit")
                pic_name='e-n-d.png'
                pic_name = os.path.join(dir_name, pic_name)
                end_image=click_image.getSubAppImage((20, 90, 750, 1170))
                end_image.writeAppImage(pic_name)
                log.debug("---写快照%s---",pic_name)
                device.stopAppByActivity(packnameandactivity)
                device.unInstallAppByPackName(packName)
                log.debug("uninstall %s" % packName)
                return

            """点击前和点击后对比，如果两图片相同，则说明的区域为非点击区域"""
            log.debug("----进行坐标点击区域判断----")
            if first_level_sub_image1.sameAs(click_sub_image, 0.90):
                log.info("----此点为非链接点击区域点，准备点击下一坐标点----")
                continue
            else:
                log.debug("-----此坐标的为链接点击区域，发生了界面响应------")
                secondlevel_first_sub_image = first_image.getSubAppImage((400, 500, 700, 900))
            """"上一次进入第二级页面的图片相同或者和上一次从第二级返回的页面相同，则重复点击了相同区域"""
            log.debug("---进行界面冗余判断---")
            if click_sub_image.sameAs(secondlevel_first_sub_image,0.01) or click_sub_image.sameAs(sec_end_sub_image,0.90):
                device.back()  # if touch the same (x,y) ,then press the back key
                time.sleep(0.5)
                log.debug("----界面发生了冗余，将返回上一级----")
                continue
            else:
                """"非重复的进入第二级页面开始滑动屏幕"""
                log.debug("----发生了界面响应----")
                seq = seq+1  # 第一级点击区域序号加1
                seqandtitlestr=seqandtitlestr+firstlevelandseq +'-'+str(seq)+"title:"+t[2]+"packname:"+packName+"_*"
                first_image = click_image  # 保存进入第二级页面的第一张图片，用于判定后期进入重复的点击区域
                """第二级页面最多滑动max_value屏"""
                max_value = 8
                for j in range(max_value):
                    """滑屏前截图，用于是否回到主界面、是否到底端和下一步的识别"""
                    if j==0:
                        d_image1 = click_image
                    else:
                        d_image1=d_image2
                    sec_level_pic_name = firstlevelandseq +'-'+str(seq)+'-'+str(j)+'.png'  # i:the seq of first level picture
                    sec_level_pic_name = os.path.join(dir_name, sec_level_pic_name)
                    """判断和主界面是否一样"""
                    d_sub_image1 = d_image1.getSubAppImage((400, 500, 700, 900))
                    if d_sub_image1.sameAs(sub_home_image, 0.90):
                        log.error("从二级页面的返回到了主界面退出----,exit")
                        logRunTime(begintime,packName)
                        pic_name = 'e-n-d.png'
                        pic_name = os.path.join(dir_name, pic_name)
                        d_image1=d_image1.getSubAppImage((20, 90, 750, 1170))
                        d_image1.writeAppImage(pic_name)
                        log.debug("---写快照%s---", pic_name)
                        device.stopAppByActivity(packnameandactivity)
                        device.unInstallAppByPackName(packName)
                        return

                    """滑动前截取子图用于判断是否到达了页面的底部"""
                    d_sub_image1=d_image1.getSubAppImage((80, 900, 300, 1100))
                    """待识别的区域为（0,50,768,1184）"""
                    d_image1 = d_image1.getSubAppImage((20, 90, 750, 1170))
                    d_image1.writeAppImage(sec_level_pic_name)  # save second level picture
                    """滑动屏幕"""
                    log.debug("---写快照%s---", sec_level_pic_name)
                    device.drag(760,850,760, 160)  # drag in the second level
                    time.sleep(0.5)
                    log.debug("----第二级页面滑屏----")

                    """滑屏后再一次截取快照,用于判断是否到底端"""
                    d_image2 = device.takeSnapshot()
                    d_sub_image2 = d_image2.getSubAppImage((80, 900, 300, 1100))
                    if d_sub_image1.sameAs(d_sub_image2, 0.90) :
                        device.back()  # if after drag the image don't change,then press back
                        time.sleep(1)
                        log.info("已经到达第二级页面的底部，准备返回")
                        break
                    else:
                        if j == max_value - 1:
                            device.back()
                            sec_end_sub_image=device.takeSnapshot()
                            sec_end_sub_image=sec_end_sub_image.getSubAppImage((400, 500, 700, 900))
                            time.sleep(1)
                            log.info("完成了第二级页面的遍历，准备返回")
                            break
                        else:
                            continue

        InitUtil.saveSeqAndText(seqandtitlestr)
        device.drag(760,850,760, 160)
        time.sleep(2)
        log.debug("-------第一级页面滑屏幕-------")
        if num==i+1:
            endImage=device.takeSnapshot()
            logRunTime(begintime,packName)
            endImage=endImage.getSubAppImage((20, 90, 750, 1170))
            pic_name='e-n-d.png'
            pic_name = os.path.join(dir_name,pic_name)
            endImage.writeAppImage(pic_name)
            log.debug("---写快照%s---", pic_name)
            log.debug("APP %s 自动运行完毕"%packName)
            device.unInstallAppByPackName(packName)
            return

if __name__=="__main__":
    ats=AppTaskSender("/home/apptest",apptaskque)
    ats.setName("app task sender")
    ats.setDaemon(True)
    ats.start()
    while True:
        if apptaskque.empty():
            log.debug("app task queue is empty")
            time.sleep(10)
        else:
            apptask=apptaskque.get()
            log.debug("the the path %s"%apptask)
            appAutoRun(apptask)
            time.sleep(50)

