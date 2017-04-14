# coding:utf8
import sys,signal
reload(sys)
sys.setdefaultencoding('utf-8')
import sys
import cv2,cPickle
import numpy as np
class TextRegion():
    def __init__(self):
        pass
    def textpreprocess(self,gray):
        # 1. Sobel算子，x方向求梯度
        sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)

        # 2. 二值化
        ret, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 9))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (29, 6))
        # 4. 膨胀一次，让轮廓突出
        dilation = cv2.dilate(binary, element2, iterations=1)
        # 5. 腐蚀一次，去掉细节，如表格线等。注意这里去掉的是竖直的线
        erosion = cv2.erode(dilation, element1, iterations=1)
        # 6. 再次膨胀，让轮廓明显一些
        dilation2 = cv2.dilate(erosion, element2, iterations=2)
        return  dilation2

    def titlepreprocess(self,gray):
        # 1. Sobel算子，x方向求梯度
        sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize = 3)
        # 2. 二值化
        ret, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)
        # cv2.imwrite("erzhihuatupian1.png",binary)
        # 3. 膨胀和腐蚀操作的核函数
        # element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 6))
        element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 6))
        # element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 9))
        element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 9))
        # 4. 膨胀一次，让轮廓突出getStructuringElement
        dilation = cv2.dilate(binary, element2,iterations=1)
        # 5. 腐蚀一次，去掉细节，如表格线等。注意这里去掉的是竖直的线
        erosion = cv2.erode(dilation, element1,iterations=1)
        # 6. 再次膨胀，让轮廓明显一些
        dilation2 = cv2.dilate(erosion, element2,iterations=3)
        # 7. 存储中间图片
        cv2.imwrite("binary.png", binary)
        cv2.imwrite("dilation.png", dilation)
        cv2.imwrite("erosion.png", erosion)
        cv2.imwrite("dilation2.png", dilation2)

        return dilation2

    def getTitlePoint(self,img):
        boxl=self.findTextRegion(img)
        pointlist=[]
        for box in boxl:
            height = abs(box[0][1] - box[2][1])
            width = abs(box[0][0] - box[2][0])
            if (height > width * 1.1):
                continue
            Xpoint = width / 2.0 + min(box[0][0], box[2][0])
            Ypoint = height / 2.0 + min(box[0][1], box[2][1])
            point=[Xpoint,Ypoint]
            pointlist.append(point)
        return  pointlist

    def findTextRegion(self,img):
        region = []
        # 1. 查找轮廓
        contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # 2. 筛选那些面积小的
        for i in range(len(contours)):
            cnt = contours[i]
            # 计算该轮廓的面积
            area = cv2.contourArea(cnt)
            # 面积小的都筛选掉
            if(area < 4500):
                continue
            # 轮廓近似，作用很小
            epsilon = 0.001 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            # 找到最小的矩形，该矩形可能有方向
            rect = cv2.minAreaRect(cnt)
            # print "rect is: "
            # print rect
            # box是四个点的坐标
            box = cv2.cv.BoxPoints(rect)
            # print "box"+box
            box = np.int0(box)
            # print box
            # 计算高和宽
            height = abs(box[0][1] - box[2][1])
            width = abs(box[0][0] - box[2][0])
            sx=min(box[2][0],box[0][0])
            sy=min(box[2][1],box[0][1])
            ex=max(box[2][0],box[0][0])
            ey=max(box[2][1],box[0][1])
            box1=(sx,sy,ex,ey)
            # 筛选那些太细的矩形，留下扁的
            if(width>height*1.5 ):
                # print box1
                region.append(box)
                continue
            # if box[0][1]>1180 or box[0][0]>760:
            #     continue
        return region

    def detect(self,img):
        # 1.  转化成灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 2. 形态学变换的预处理，得到可以查找矩形的图片
        cv2.imwrite("huidutuxiang.png", gray)
        ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
        cv2.imwrite("二值图像.png", binary)
        dilation = self.titlepreprocess(gray)
        # 3. 查找和筛选文字区域
        region = self.findTextRegion(dilation)
        # 4. 用绿线画出这些找到的轮廓
        for box in region:
            cv2.drawContours(img, [box], 0, (0, 0, 255), 2)
        cv2.namedWindow("img", cv2.WINDOW_NORMAL)
        cv2.imshow("img", img)
        # 带轮廓的图片
        # cv2.imwrite("/home/文字区域定位.png", img)
        cv2.imwrite("/home/文字区域定位2.png", img)

        print "---------------"
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    # 读取文件
    # imagePath = sys.argv[1]
    tr=TextRegion()
    img = cv2.imread("/home/hw/1-0.png")
    tr.detect(img)