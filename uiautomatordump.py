#-*- coding:UTF-8 -*-
"""
APP界面控件解析实现文件
"""
import sys,signal,os
reload(sys)
sys.setdefaultencoding('utf-8')

import tempfile
from subprocess import  Popen,PIPE
import os
import re
import time
import xml.etree.cElementTree as ET


def uiDump(filepath):
    """
    获取当前Activity控件树
    """
    p1=Popen(["adb","shell","uiautomator dump","/data/local/tmp/uidump.xml"],stdout=PIPE)
    p1.stdout.readlines()
    p1.wait()
    p2=Popen(["adb","pull","/data/local/tmp/uidump.xml",filepath],stdout=PIPE)
    p2.stdout.readlines()
    p2.wait()

class PointElement(object):
    """
    通过元素定位,需要Android 4.0以上

    """
    def __init__(self):
        """
        初始化，获取系统临时文件存储目录，定义匹配数字模式
        """
        # self.tempFile = tempfile.gettempdir()
        self.tempFile = "/tmp"
        uiDump(self.tempFile)
        self.tree=ET.ElementTree(file=self.tempFile + "/uidump.xml")
        self.pattern = re.compile(r"\d+")
        self.pointlist=self.getPointMap()
        self.clickPointMap=self.pointlist[0]
        self.menupointMap=self.pointlist[1]
    def getClickPointMap(self):
        pointmap={}
        for key,value in self.clickPointMap.items():
            if len(value)>6:
                pointmap[key]=value
            else:
                pass
        return pointmap

    def getMenuPointMap(self):
        return self.menupointMap

    def __element(self, attrib, name):
        """
        同属性单个元素，返回单个坐标元组
        """
        treeIter = self.tree.iter(tag="node")
        for elem in treeIter:
            if elem.attrib[attrib] == name:
                bounds = elem.attrib["bounds"]
                coord = self.pattern.findall(bounds)
                Xpoint = (int(coord[2]) - int(coord[0])) / 2.0 + int(coord[0])
                Ypoint = (int(coord[3]) - int(coord[1])) / 2.0 + int(coord[1])
                return Xpoint, Ypoint


    def getElements(self, attrib, name):
        """
        同属性多个元素，返回坐标元组列表
        """
        list = []
        treeIter = self.tree.iter(tag="node")
        for elem in treeIter:
            if elem.attrib[attrib] == name:
                bounds = elem.attrib["bounds"]
                coord = self.pattern.findall(bounds)
                Xpoint = (int(coord[2]) - int(coord[0])) / 2.0 + int(coord[0])
                Ypoint = (int(coord[3]) - int(coord[1])) / 2.0 + int(coord[1])
                list.append((Xpoint, Ypoint))
        return list

    def getElementDesc(self):
        pointmap = {}
        treeIter = self.tree.iter(tag="node")
        for elem in treeIter:
            if elem.attrib["content-desc"] <> "":
                textinfo = elem.attrib["content-desc"]
                bounds = elem.attrib["bounds"]
                coord = self.pattern.findall(bounds)
                Xpoint = (int(coord[2]) - int(coord[0])) / 2+ int(coord[0])
                Ypoint = (int(coord[3]) - int(coord[1])) / 2 + int(coord[1])
                pointmap[(Xpoint, Ypoint)] = textinfo
        return pointmap


    def getElementText1(self):
        """map={(x,y):text}
        """
        pointmap={}
        treeIter = self.tree.iter(tag="node")
        for elem in treeIter:
            value=elem.attrib["text"]
            if value<>"" and value <>'搜索' and value<> '广告' :

                if elem.attrib["class"].find("TextView")<>-1:
                    # print value
                    textinfo=elem.attrib["text"]
                    bounds = elem.attrib["bounds"]
                    coord = self.pattern.findall(bounds)
                    Xpoint = (int(coord[2]) - int(coord[0])) / 2 + int(coord[0])
                    Ypoint = (int(coord[3]) - int(coord[1])) / 2 + int(coord[1])
                    pointmap[(Xpoint,Ypoint)]=textinfo
        return pointmap

    def getElementText(self):
        """map={(x,y):text}
        """
        pointmap = {}
        treeIter = self.tree.iter(tag="node")
        for elem in treeIter:
            value = elem.attrib["text"]
            if value <> "" and value <> '搜索' and value <> '广告':

                    # print value
                textinfo = elem.attrib["text"]
                bounds = elem.attrib["bounds"]
                coord = self.pattern.findall(bounds)
                Xpoint = (int(coord[2]) - int(coord[0])) / 2 + int(coord[0])
                Ypoint = (int(coord[3]) - int(coord[1])) / 2 + int(coord[1])
                pointmap[(Xpoint, Ypoint)] = textinfo
        return pointmap

    def getPointMap(self):
        textmap = self.getElementText()
        menumap = {}
        rmenumap={}
        pointmap = {}
        for key, value in textmap.items():
            if key[1] > 99:
                pointmap[key] = value
            else:
                menumap[key] = value
            i=0
            vtmp=""
            tmp=()
            for key,value in menumap.items():
                if i==0:
                    tmp=key[1]
                    vtmp=value
                    i=i+1
                else:
                    if tmp==key[1]:
                        rmenumap[key]=value
                    else:
                        pass
            rmenumap[tmp]=vtmp
        return pointmap,rmenumap

    def getElementByClass(self, className):
        """
        通过元素类名定位
        usage: findElementByClass("android.widget.TextView")
        """
        return self.__element("class", className)

    def getElementsByClass(self, className):
        return self.__elements("class", className)

    def findElementById(self, id):
        """
        通过元素的resource-id定位
        usage: findElementsById("com.android.deskclock:id/imageview")
        """
        return self.__element("resource-id",id)

    def findElementsById(self, id):
        return self.__elements("resource-id",id)

if __name__=="__main__":
    p=PointElement()
    ans=p.getClickPointMap()
    # packname=sys.argv[1]
    ansstr=""
    for key,value in ans.items():
        if value <>'搜索' and value <> '广告'<>len(value)>=15:
            ansstr=ansstr+str(key[0])+":"+str(key[1])+"title:"+value+"_*"
    print ansstr[0:-2]
    del p
    del ans
    # uiDump(".")