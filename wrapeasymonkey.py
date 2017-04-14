'''
Created on 2017
@auther: huangwei
This file is the main apis sourcecode of the easy monkey wrapper
'''

import sys
import os,time
from datetime import datetime
import traceback

'''
Global variables
'''
DEBUG=True
INFO=True
ERROR=True
repeatTimesOnError=2
idCheckTimes=20
waitForConnectionTime=10
ANDROID_HOME=os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/root/android-sdk-linux/'

'''
import android libs and internal libs
'''
import signal
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice
from com.android.monkeyrunner.easy import By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer
from com.android.hierarchyviewerlib.models import ViewNode
from com.android.chimpchat.core import TouchPressType
# from com.whoistester.android.testCaseManager import testCaseManager
class wrapEasyMonkey():
	'''
	#############################
	Wrap easy monkey class
	#############################
	'''
	def __init__(self,deviceId):
		self.debug("__int__: creating the wrap easy monkey object with deviceid %s" % deviceId)
		self.deviceId = deviceId
		device = self.waitForConnection()
		self.device = device
		self.easyDevice = EasyMonkeyDevice(device)
		#self.DOWN = TouchPressType.DOWN.getIdentifier()
		#self.UP = TouchPressType.UP.getIdentifier()
		#self.DOWN_AND_UP = TouchPressType.DOWN_AND_UP.getIdentifier()
		self.DOWN = MonkeyDevice.DOWN
		self.UP = MonkeyDevice.UP
		self.DOWN_AND_UP = MonkeyDevice.DOWN_AND_UP
		# self.caseManager = testCaseManager(self)
		self.debug('created the wrapEasyDevice')

	def waitForConnection(self,seconds=1):
		try:
			device = MonkeyRunner.waitForConnection(30, self.deviceId)
			return device
		except :
			self.error("Couldn't connect to %s" %self.deviceId)
			os._exists(1)


	def exitGracefully(self,signum, frame):
		signal.signal(signal.SIGINT, signal.getsignal(signal.SIGINT))
		self.device.shell('killall com.android.commands.monkey')
		self.error('!!!!recive the int signal then exit')
		sys.exit(1)

	def installPackage(self,apkname):
			self.device.installPackage(apkname)
			self.debug("% success installed"%apkname)

	def click(self,x,y):
		# self.device=MonkeyRunner.waitForConnection()
		self.debug("click on (%s,%s)"%(str(x),str(y)))
		if self.device<>None:
			try:
				self.device.wake()
				self.device.touch(x,y,'DOWN_AND_UP')
				self.sleep(0.5)
			except:
				self.error("exception happed in click!!!!")
				self.device=MonkeyRunner.waitForConnection(self.deviceId)
				self.device.touch(x, y, 'DOWN_AND_UP')
				self.sleep(0.5)

	def drag(self,xs,ys,xe,ye,time=0.1,step=1):
		self.device.drag(xs,ys,xe,ye,time,step)
		self.sleep(0.4)

	def startActivity(self,activity):
		try:
			self.debug("starting the activity... %s" % activity)
			self.device.startActivity(component=activity)
		except:
			self.error("starting the activity %s error" % activity)
			sys.exc_info()
			traceback.print_exc()
			return False

	'''
	type charactors, special charactors please the press function to input the keycode
	'''

	def type(self,content):
		self.debug('device input the %s' % content)
		self.device.type(content)

	'''
	press keycode, special charactor and direction button ...
	'''

	def press(self,keycode,type):
		# self.device = MonkeyRunner.waitForConnection(self.deviceId)
		if self.device<>None:
			try:
				self.device.wake()
				self.device.press(keycode,type)
				self.debug('device press the key "%s" ' % keycode)
				self.sleep(0.2)
			except:
				self.error('press exception happen!!!!!!')
				self.device=MonkeyRunner.waitForConnection(self.deviceId)
				self.device.press(keycode, type)
				self.sleep(0.2)
				self.debug('device press the key "%s" ' % keycode)

		# self.sleep(0.2)

	def pressDownAndUp(self,keycode):
		self.press(keycode,self.DOWN)
		self.press(keycode,self.UP)
		self.debug('device press_donwu_and_up')
		self.sleep(0.2)

	'''
	sleep function
	'''

	def sleep(self,seconds):
		time.sleep(seconds)

	'''
	wrap easyMonkeyDevice by function
	will return the view object if found.if do not found will return None.
	'''
	def getView(self,id):
		self.debug('calling getview function by the id (%s)' % id)
		for tmp in range(repeatTimesOnError):
			try:
				return By.id(id)
			except:
				self.debug('getView: the %dst time error by id (%s) ,  will retry ' % (tmp,id))
				self.sleep(0.5)
				continue
		self.error('getView: sorry , still can\'t get the view by this id (%s). please check the view ' % id)
		sys.exc_info()
		traceback.print_exc()
		return None


	'''
	if the id object is a textview, then will clear all the text
	'''
	def clearTextById(self,id):
		self.debug('calling clearTextById function by the id (%s)' % id)
		if(self.checkIdExist(id)):
			if not self.isFocused(id):
				self.touchViewById(id,self.DOWN_AND_UP)
			TextView = self.getView(id)
			rangenumber = len(self.getText(TextView))
			for x in range(rangenumber):
				self.device.press('KEYCODE_DEL',self.DOWN_AND_UP)
			for x in range(rangenumber):
				self.device.press('KEYCODE_FORWARD_DEL',self.DOWN_AND_UP)
			self.debug('clearTextById: cleared the text in id (%s)' % id)
			return True
		self.error('clearTextById: sorry ,the id (%s) is not exist ' % id)
		sys.exc_info()
		traceback.print_exc()
		return False

	'''
	wrap get text function.
	return text string content of the view object. If can not found the view object , will return None.
	'''
	def getText(self,view):

		self.debug('calling getText function')
		for tmp in range(repeatTimesOnError):
			try:
				return self.easyDevice.getText(view).encode(sys.getdefaultencoding())
			except:
				self.debug('getText: the %dst time getText error , will retry ' % tmp)
				time.sleep(1)
				continue
		self.error('getText: sorry , still can\'t get the text. please check the view is exist or not , or does the view have text property?')
		# sys.exc_info()
		# traceback.print_exc()
		return None

	'''
	'''

	def getDescById(self,id):
		self.debug('calling ')


	def getTextById(self,id):

		self.debug('calling getTextById function')
		for tmp in range(repeatTimesOnError):
			try:
				return self.getText(self.getView(id))
			except:
				self.debug('getTextById: the %dst time getTextById error id (%s) , will retry ' % (tmp,id))
				time.sleep(0.5)
				continue
		self.error('getTextById: sorry , still can\'t get the text by id "%s". please check the view is exist or not , or does the view have text property?' % id)
		# sys.exc_info()
		# traceback.print_exc()
		return None

	'''
	wrap easyMonkeyDevice touch view function
	return true or false (if cannot locate the view ,will return false)
	'''
	def touchView(self,view,type):

		self.debug('calling touchView function')
		for tmp in range(repeatTimesOnError):
			try:
				self.easyDevice.touch(view,type)
				return True
			except:

				self.debug('touchView: the %dst time touch error , not found the view , will retry ' % tmp)
				if (tmp >1 & DEBUG):
					self.debug('Please wait to touch the view')
				time.sleep(1)
				continue
		self.error('touchView: sorry , still can\'t touch view. please check the view is exist or not , or increase the repeat times variable?')
		sys.exc_info()
		traceback.print_exc()
		return False


	def touchViewById(self,id,type):

		self.debug( 'calling touchViewById function')
		for tmp in range(repeatTimesOnError):
			try:
				self.easyDevice.touch(By.id(id),type)
				return True
			except:

				self.debug('touchViewById: the %dst time touch error by this id (%s) , not found the view , will retry ' % (tmp,id))
				if (tmp >1 & DEBUG):
					self.debug('Please wait to touch the view')
				self.sleep(1)
				continue
		self.error('touchViewById: sorry , still can\'t touch view. please check the view is exist or not , or increase the repeat times variable?')
		sys.exc_info()
		traceback.print_exc()
		return False

	def touchPoint(self,x,y,type):

		self.debug('calling touch the point ')
		for tmp in range(repeatTimesOnError):
			try:
				self.device.touch(x,y,type)
				return True
			except:

				self.debug('touchPoint: %d time touch point error , will retry ' % tmp)
				self.sleep(1)
				continue

		self.error('touchPoint: sorry , still can\'t touch point. please check the view is exist or not , or increase the repeat times variable?')
		sys.exc_info()
		traceback.print_exc()
		return False

	'''
	has the view is focused or not
	'''

	def isFocused(self,id):

		self.debug('checking the view is focused or not')
		#hierarchyViewer = self.device.getHierarchyViewer()
		#print hierarchyViewer.findViewById(id).hasFocus

		for tmp in range(repeatTimesOnError):
			try:
				hierarchyViewer = self.device.getHierarchyViewer()
				return hierarchyViewer.findViewById(id).hasFocus
			except:

				self.debug('isFocused: the %dst time check focus error  , will retry ' % tmp)
				self.sleep(1)
				continue
		self.error('isFocused: error occured')
		sys.exc_info()
		traceback.print_exc()
		return False


	def isExist(self,id):
		#self.debug('check the id is exist or not')

		for tmp in range(repeatTimesOnError):
			try:
				if (self.easyDevice.exists(self.getView(id))):
					return True
				else:

					self.debug('isExist: %s this id does not exists,will try check again' % id)
					self.sleep(1)
					continue
			except:

				self.debug('isExist: the %dst time check id (%s) existing error ,  , will retry ' % (tmp,id))
				self.sleep(1)
				continue
		self.error('isExist: error occured')
		sys.exc_info()
		traceback.print_exc()
		return False

	def checkIdExist(self,id):
		self.debug('checking the id (%s) exist or not' % id)

		for tmp in range(repeatTimesOnError):
			try:
				if (self.easyDevice.exists(self.getView(id))):
					return True
				else:

					self.debug('checkIdExist: %s this id does not exists,will try check again' % id)
					self.sleep(1)
					continue
			except:

				self.debug('checkIdExist: the %dst time check id (%s) existing error ,  , will retry ' % (tmp,id))
				self.sleep(1)
				continue
		self.error('checkIdExist: error occured')
		sys.exc_info()
		traceback.print_exc()
		return False


	def getPosition(self,id):

		self.debug('check the view is focused or not')
		for tmp in range(repeatTimesOnError):
			try:
				hierarchyViewer = self.device.getHierarchyViewer()
				print hierarchyViewer.findViewById(id).left
				print hierarchyViewer.findViewById(id).top
				print hierarchyViewer.findViewById(id).width
				print hierarchyViewer.findViewById(id).height
				return hierarchyViewer.findViewById(id).left
			except:
				self.sleep(1)
				continue
		self.error('getPosition: error occured')
		sys.exc_info()
		traceback.print_exc()
		return None

	def touchDialogById(self,id,type):

		#self.debug('touch the dialog button , here need the parent id')
		hierarchyViewer = self.device.getHierarchyViewer()
		width=self.device.getProperty("display.width")
		height=self.device.getProperty("display.height")
		x = hierarchyViewer.findViewById(id).left
		y = hierarchyViewer.findViewById(id).top
		'''
		print hierarchyViewer.findViewById(id).scrollX
		print hierarchyViewer.findViewById(id).scrollY
		print hierarchyViewer.findViewById(id).marginTop
		print hierarchyViewer.findViewById(id).marginLeft
		print hierarchyViewer.findViewById(id).marginRight
		print hierarchyViewer.findViewById(id).marginBottom
		print hierarchyViewer.findViewById(id).left
		print hierarchyViewer.findViewById(id).top
		print hierarchyViewer.findViewById(id).width
		print hierarchyViewer.findViewById(id).height

		print 'margin'
		print width
		print height
		print hierarchyViewer.findViewById(id).properties
		print '------------------'
		'''
		p = hierarchyViewer.findViewById(id).parent.parent
		#print p.properties
		myself = hierarchyViewer.findViewById(id)
		content = hierarchyViewer.findViewById('id/content')
		x +=  p.left  + (int(width) - content.width)/2 + myself.width/2
		y += p.top  + (int(height) - content.height)/2 + myself.height/2
		#( int(width) - hierarchyViewer.findViewById(id).width)/2 + hierarchyViewer.findViewById(id).left + hierarchyViewer.findViewById(id).width/2
		#y +=  ( int(height) - hierarchyViewer.findViewById(id).height)/2 + hierarchyViewer.findViewById(id).top + hierarchyViewer.findViewById(id).height/2
		#print x
		#print y
		self.touchPoint(x,y,type)

	def touchDialog(self,parentIdPosition,id,type):

		self.debug('touch the dialog button , here need the parent id')
		hierarchyViewer = self.device.getHierarchyViewer()
		#print hierarchyViewer.findViewById(parentId).left
		#print hierarchyViewer.findViewById(parentId).top
		x = hierarchyViewer.findViewById(parentId).left + (hierarchyViewer.findViewById(parentId).width - hierarchyViewer.findViewById(id).width)/2
		y = hierarchyViewer.findViewById(parentId).top + (hierarchyViewer.findViewById(parentId).height - hierarchyViewer.findViewById(id).height)/2
		print x
		print y
		self.touchPoint(x,y,type)


	def touchDialogButton(self,type):
		if DEBUG:
			self.debug('touch the dialog button , thru controling the direction key')
		#self.device.press('KEYCODE_DPAD_DOWN',MonkeyDevice.DOWN_AND_UP)
		if type==1:
			self.press('KEYCODE_DPAD_DOWN',MonkeyDevice.DOWN_AND_UP)
			#self.press('KEYCODE_DPAD_DOWN',MonkeyDevice.DOWN_AND_UP)
			self.press('KEYCODE_ENTER',MonkeyDevice.DOWN_AND_UP)
		if type==2:
			#self.press('KEYCODE_DPAD_DOWN',MonkeyDevice.DOWN_AND_UP)
			self.press('KEYCODE_DPAD_DOWN',MonkeyDevice.DOWN_AND_UP)
			self.press('KEYCODE_DPAD_RIGHT',self.DOWN_AND_UP)
			self.press('KEYCODE_ENTER',self.DOWN_AND_UP)
		if type==0:
			self.press('KEYCODE_ENTER',self.DOWN_AND_UP)


	def touchContextMenu(self,position):
		if DEBUG:
			self.debug('touch the context menu')
		self.press('KEYCODE_MENU',self.DOWN_AND_UP)
		for tmp in range(position+1):
			self.sleep(0.5)
			self.press('KEYCODE_DPAD_RIGHT',self.DOWN_AND_UP)
		self.press('KEYCODE_ENTER',self.DOWN_AND_UP)

	'''
	def touchDialogButtonRight(self,type):
		self.device.press('KEYCODE_DPAD_DOWN',type)
		self.device.press('KEYCODE_DPAD_DOWN',type)
		self.device.press('KEYCODE_DPAD_RIGHT',type)
		self.device.press('KEYCODE_ENTER',type)
	'''
	def debug(self,debuginfo):
		if DEBUG:
			print '[%s] DEBUG:  %s ' % (datetime.today(),debuginfo)

	def info(self,info):
		if INFO:
			print '[%s] Info: %s ' % (datetime.today(),info)

	def error(self,error):
		if ERROR:
			print '[%s] ERROR: %s ' % (datetime.today(),error)

	def takeSnapshot(self):
		for tmp in range(5):
			try:
				snapshot = self.device.takeSnapshot()
				self.debug('----take snapshot-%s-----' % datetime.today())
				return snapshot
			except:
				continue
		self.error('takeSnapshot: error occured')
		sys.exc_info()
		traceback.print_exc()
		return False

