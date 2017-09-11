import cv2
import numpy as np
import threading
import json
import random
import math
import time
#import Tkinter
from Tkinter import *
import ttk
import tkMessageBox
import tkFont
from PIL import Image
from PIL import ImageTk
from os import listdir, path, makedirs, remove

from class_ArduinoSerMntr import*
from class_CameraMntr import*
import class_MyThread
import class_ImageProcessing
from class_ConfigSetting import ConfigSetting
from dialog_MotorSetting import MotorSetting
from dialog_CameraConnection import CameraConnection

class App:
    # Ininitalization
    def __init__(self,root):

        self.ArdMntr= MonitorThread()
        self.ArdMntr.start()
        
        self.CamMntr= CameraLink()
        #self.CamMntr.connect_camera()
        strFont= 'Arial'
        myfont14 = tkFont.Font(family=strFont, size=14, weight= tkFont.BOLD)
        myfont12 = tkFont.Font(family=strFont, size=12)#, weight= tkFont.BOLD)
        myfont12_Bold = tkFont.Font(family=strFont, size=12, weight= tkFont.BOLD)
        myfont10 = tkFont.Font(family=strFont, size=10)
        self.bgGreen= '#007700'
        self.bgGreen_active= '#00aa00'
        bgGray= '#333333333'
        bgGray_active= 'gray'
        bgGray_select= '#999'
        self.bgRed= '#aa0000'
        self.bgRed_active= '#ee0000'
        '''
        self.root = Tkinter.Tk()
        self.root.title("[Arduino] Stepper Control")
        self.root.attributes('-zoomed', True) # FullScreen
        '''
        self.root= root
        # ====== Parameters ================================
        self.savePath= 'Data/'
        self.saveParaPath= 'Data/Para/'
        self.configName= 'config.json'

        self.img = Tkinter.PhotoImage(file = self.saveParaPath+'Icon_2.png')
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.img)
	self.ItemList=[]
        defaultValueList=[]
	self.ItemList.append("thrshd_gray")
	defaultValueList.append(128)
	self.ItemList.append("thrshd_size")
	defaultValueList.append(20)
	self.ItemList.append("Scan_X (Beg,Interval,Amount)")
	defaultValueList.append([0,500,4])
	self.ItemList.append("Scan_Y (Beg,Interval,Amount)")
	defaultValueList.append([0,500,4])
	self.ItemList.append("limit Maximum (X,Y)")
	defaultValueList.append([8000,95000])
        self.ItemList.append("Max Speed (X, Y)")
	defaultValueList.append([400,400,400])
        self.ItemList.append("Ac/Deceleration (X, Y)")
	defaultValueList.append([100,100,100])

        self.config= ConfigSetting(self.saveParaPath, self.configName, defaultValueList)
        params= self.config.read_json(self.ItemList)
        #print 'para: ',params
        self.threshold_graylevel= params[self.ItemList[0]]
        self.threshold_size= params[self.ItemList[1]] 
        self.scan_X= params[self.ItemList[2]]
        self.scan_Y= params[self.ItemList[3]]
        self.limit= params[self.ItemList[4]]
        self.MaxSpeed= params[self.ItemList[5]]
        self.Acceleration= params[self.ItemList[6]]

        self.imageProcessor= class_ImageProcessing.contour_detect(self.savePath,self.saveParaPath)
        self.checkmouse_panel_mergeframe= False
        self.x1, self.y1, self.x2, self.y2= -1,-1,-1,-1        
        self.StartScan_judge= False
        self.saveScanning= 'XXX'
        self.strStatus= 'Idling...'

        self.root.update()
        self.screen_width, self.screen_height= self.root.winfo_width(), self.root.winfo_height()
        print 'screen: ',[self.root.winfo_screenwidth(), self.root.winfo_screenheight()]
        print 'w, h: ',[self.root.winfo_width(), self.root.winfo_height()]
        btn_width, btn_height= 8, 1
        self.interval_x, self.interval_y= 6, 6
        self.mergeframe_spaceY= 50
        #print width,',', height,' ; ',btn_width,',', btn_height
        
        # ====== [Config] Menu Bar============
        self.menubar= Tkinter.Menu(self.root)
        self.FileMenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File",underline=0, menu=self.FileMenu)
        self.FileMenu.add_command(label="Save Image", command=self.btn_saveImg_click)
        self.SettingMenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.SettingMenu.add_command(label= "Motor Setting", command= self.set_Motor)
        self.menubar.add_cascade(label="Setting", underline=0, menu=self.SettingMenu)
        self.ConnectMenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.ConnectMenu.add_command(label="Connect to Arduino", command=self.set_ArdConnect)
        self.ConnectMenu.add_command(label="Connect to Camera", command=self.set_CamConnect)
        self.menubar.add_cascade(label="Communication", underline= 0, menu=self.ConnectMenu)
        self.ImgProcess= Tkinter.Menu(self.menubar, tearoff=0)
        self.ImgProcess.add_command(label="Set Background", command= self.plastic_set_background)
        self.ImgProcess.add_command(label='Otsu Binary', command= self.methond_OtsuBinary)
        self.menubar.add_cascade(label="Image Processing", underline=0, menu= self.ImgProcess)
        self.root.config(menu= self.menubar)
        self.root.update()

        # ====== [Config] Status Bar ==============
        self.statuslabel = Tkinter.Label(self.root, bd = 1, relief = Tkinter.SUNKEN, anchor = "w")
        self.statuslabel.config(text="IDLING ..................")
        self.statuslabel.pack(side = Tkinter.BOTTOM,fill=Tkinter.X)
        self.root.update()
        #self.screen_height= self.screen_height- self.statuslabel.winfo_reqheight()

        #======= [Config] Tab =================
        #Left_width= self.lbl_MoveCoord.winfo_reqwidth()+ self.interval_x*11
        Left_width= int((self.screen_width-self.interval_x*2)*0.25)
        Left_height= int((self.screen_height-self.FileMenu.winfo_reqheight()*1- self.statuslabel.winfo_reqheight()*1-self.interval_y*5))
        self.tabbox = ttk.Notebook(self.root, width=Left_width, height=Left_height)
        self.tab_control = Tkinter.Frame(self.root)
	self.tab_pinsetting = Tkinter.Frame(self.root)
	self.tab_imageprocess = Tkinter.Frame(self.root)

	self.tabbox.add(self.tab_control, text="CONTROL")
	self.tabbox.add(self.tab_pinsetting, text="PIN")
	self.tabbox.add(self.tab_imageprocess, text="IMAGE")

	#self.tabbox.place(x= self.interval_x, y= self.interval_y)
	self.tabbox.place(x= 0, y= 0)
        self.root.update()
        print '*** Input Tab', Left_width, Left_height
        print '*** TAB',self.tabbox.winfo_reqwidth(), self.tabbox.winfo_reqheight()

        # ====== [Config] Current position of motor ===========
        #self.lbl_CurrCoord= Tkinter.Label(self.root, text="[ Current Position ]", font= myfont14)
        self.lbl_CurrCoord= Tkinter.Label(self.tab_control, text="[ Current Position ]", font= myfont14)
        self.lbl_CurrCoord.place(x= self.interval_x, y= self.interval_y)
        self.root.update()
        self.lbl_CurrPos= Tkinter.Label(self.tab_control, text="(X, Y, Z)= (-1, -1, -1)",font= myfont12)
        self.lbl_CurrPos.place(x= self.interval_x, y= self.lbl_CurrCoord.winfo_y()+ self.lbl_CurrCoord.winfo_height())
        self.root.update()
        #======[Step Motor Control] ========
        self.lbl_MoveCoord= Tkinter.Label(self.tab_control, text="[ MOVE ]", font= myfont14)
        #self.lbl_MoveCoord.place(x= self.interval_x, y= self.lbl_CurrPos.winfo_y()+ self.lbl_CurrPos.winfo_height()+self.interval_y)
        self.lbl_MoveCoord.place(x= self.interval_x, y= self.lbl_CurrPos.winfo_y()+ self.lbl_CurrPos.winfo_height()+self.interval_y)
        self.root.update()

        #========== Move Amount Radio Button ===============
        self.MvAmount= Tkinter.IntVar()
        self.rdbtn_MvAmount_1= Tkinter.Radiobutton(self.tab_control, text= "1k", variable= self.MvAmount,font= myfont12_Bold, value=1, command= self.rdbtn_click, indicatoron=0, width=5, fg= 'white', activeforeground='white', bg= bgGray, activebackground= bgGray_active,selectcolor= bgGray_select)
        self.rdbtn_MvAmount_1.place(x= self.interval_x, y=self.lbl_MoveCoord.winfo_y()+ self.lbl_MoveCoord.winfo_reqheight()+ self.interval_y)
        self.root.update()
        self.rdbtn_MvAmount_5= Tkinter.Radiobutton(self.tab_control, text= "5k", value=5, variable= self.MvAmount,font= myfont12_Bold, command= self.rdbtn_click, indicatoron=0, width=5, fg= 'white', activeforeground='white', bg= bgGray, activebackground= bgGray_active,selectcolor= bgGray_select)
        self.rdbtn_MvAmount_5.place(x= self.interval_x+ self.rdbtn_MvAmount_1.winfo_x()+ self.rdbtn_MvAmount_1.winfo_reqwidth(),y= self.rdbtn_MvAmount_1.winfo_y())
        self.root.update()
        self.rdbtn_MvAmount_10= Tkinter.Radiobutton(self.tab_control, text= "10k", value=10, variable= self.MvAmount,font= myfont12_Bold, command= self.rdbtn_click, indicatoron=0, width=5, fg= 'white', activeforeground='white', bg= bgGray, activebackground= bgGray_active,selectcolor= bgGray_select)
        self.rdbtn_MvAmount_10.place(x= self.interval_x+ self.rdbtn_MvAmount_5.winfo_x()+ self.rdbtn_MvAmount_5.winfo_reqwidth(),y= self.rdbtn_MvAmount_1.winfo_y())
        self.root.update()
        self.rdbtn_MvAmount_50= Tkinter.Radiobutton(self.tab_control, text= "50k", value=50, variable= self.MvAmount,font= myfont12_Bold, command= self.rdbtn_click, indicatoron=0, width=5, fg= 'white', activeforeground='white', bg= bgGray, activebackground= bgGray_active,selectcolor= bgGray_select)
        self.rdbtn_MvAmount_50.place(x= self.interval_x+ self.rdbtn_MvAmount_10.winfo_x()+ self.rdbtn_MvAmount_10.winfo_reqwidth(),y= self.rdbtn_MvAmount_1.winfo_y())
        self.root.update()
        self.rdbtn_MvAmount_100= Tkinter.Radiobutton(self.tab_control, text= "100k", value=100, variable= self.MvAmount,font= myfont12_Bold, command= self.rdbtn_click, indicatoron=0, width=5, fg= 'white', activeforeground='white', bg= bgGray, activebackground= bgGray_active,selectcolor= bgGray_select)
        self.rdbtn_MvAmount_100.place(x= self.interval_x+ self.rdbtn_MvAmount_50.winfo_x()+ self.rdbtn_MvAmount_50.winfo_reqwidth(),y= self.rdbtn_MvAmount_1.winfo_y())
        self.root.update()
        self.rdbtn_MvAmount_10.select()
        self.lbl_posUnit_1= Tkinter.Label(self.tab_control, text='(step)')
        self.lbl_posUnit_1.place(x= self.rdbtn_MvAmount_100.winfo_x()+ self.rdbtn_MvAmount_100.winfo_width(), y= self.rdbtn_MvAmount_1.winfo_y()+self.interval_y)
        self.root.update()
        
        # ======= Move Direction ===============
        #photo_up=PhotoImage(file=self.saveParaPath+'img_Up.png')
        #photo_up= photo_up.zoom(1)
        #photo_up= photo_up.subsample(4)
        photo_up= self.IconResize(self.saveParaPath+'img_Up.png')
        self.btn_MoveUp= Tkinter.Button(self.tab_control,image= photo_up, cursor= 'hand2')
        self.btn_MoveUp.image= photo_up
        self.btn_MoveUp.place(x= self.rdbtn_MvAmount_10.winfo_x()+int(self.rdbtn_MvAmount_10.winfo_reqwidth()*0), y=self.rdbtn_MvAmount_1.winfo_y()+ self.rdbtn_MvAmount_1.winfo_reqheight()+ self.interval_y)
        self.root.update()
        photo_down= self.IconResize(self.saveParaPath+'img_Down.png')
        self.btn_MoveDown= Tkinter.Button(self.tab_control,image= photo_down, cursor= 'hand2')
        self.btn_MoveDown.image= photo_down
        self.btn_MoveDown.place(x= self.btn_MoveUp.winfo_x(), y=self.btn_MoveUp.winfo_y()+ self.btn_MoveUp.winfo_reqheight()+ self.interval_y)
        self.root.update()
        photo_left= self.IconResize(self.saveParaPath+'img_Left.png')
        self.btn_MoveLeft= Tkinter.Button(self.tab_control,image= photo_left, cursor= 'hand2')
        self.btn_MoveLeft.image= photo_left
        self.btn_MoveLeft.place(x= self.btn_MoveDown.winfo_x()- self.btn_MoveDown.winfo_width()- self.interval_x, y=self.btn_MoveDown.winfo_y())
        self.root.update()
        photo_right= self.IconResize(self.saveParaPath+'img_Right.png')
        self.btn_MoveRight= Tkinter.Button(self.tab_control,image= photo_right, cursor= 'hand2')
        self.btn_MoveRight.image= photo_right
        self.btn_MoveRight.place(x= self.btn_MoveDown.winfo_x()+ self.btn_MoveDown.winfo_width()+ self.interval_x, y=self.btn_MoveDown.winfo_y())
        self.root.update()


        self.btn_MoveZUp= Tkinter.Button(self.tab_control,image= photo_up, cursor= 'hand2')
        self.btn_MoveZUp.image= photo_up
        self.btn_MoveZUp.place(x= self.btn_MoveRight.winfo_x()+ self.btn_MoveRight.winfo_reqwidth()+ self.interval_x*4, y=self.btn_MoveUp.winfo_y())
        self.root.update()
        self.btn_MoveZDown= Tkinter.Button(self.tab_control,image= photo_down, cursor= 'hand2')
        self.btn_MoveZDown.image= photo_down
        self.btn_MoveZDown.place(x= self.btn_MoveZUp.winfo_x(), y=self.btn_MoveDown.winfo_y())
        self.root.update()
        #'''
        #'''

        self.lbl_Xpos= Tkinter.Label(self.tab_control, text= 'X :',font= myfont12)
        #self.lbl_Xpos.place(x= self.interval_x, y = self.rdbtn_MvAmount_1.winfo_y()+ self.rdbtn_MvAmount_1.winfo_height()+self.interval_y)
        self.lbl_Xpos.place(x= self.interval_x, y = self.btn_MoveDown.winfo_y()+ self.btn_MoveDown.winfo_height()+self.interval_y*3)
        self.root.update()
        self.entry_Xpos= Tkinter.Entry(self.tab_control, font= myfont12, width=4)
        self.entry_Xpos.insert(Tkinter.END, "0")
        self.entry_Xpos.place(x= self.lbl_Xpos.winfo_x()+ self.lbl_Xpos.winfo_width(), y= self.lbl_Xpos.winfo_y())
        self.root.update()
        self.lbl_Ypos= Tkinter.Label(self.tab_control, text= 'Y :',font= myfont12)
        self.lbl_Ypos.place(x= self.entry_Xpos.winfo_x()+ self.entry_Xpos.winfo_width()+ self.interval_x, y = self.lbl_Xpos.winfo_y())
        self.root.update()
        self.entry_Ypos= Tkinter.Entry(self.tab_control, font= myfont12, width=4)
        self.entry_Ypos.insert(Tkinter.END, "0")
        self.entry_Ypos.place(x= self.lbl_Ypos.winfo_x()+ self.lbl_Ypos.winfo_width(), y= self.lbl_Ypos.winfo_y())
        self.root.update()
        
        self.lbl_Zpos= Tkinter.Label(self.tab_control, text= 'Z :',font= myfont12)
        self.lbl_Zpos.place(x= self.entry_Ypos.winfo_x()+ self.entry_Ypos.winfo_width()+ self.interval_x, y = self.lbl_Xpos.winfo_y())
        self.root.update()
        self.entry_Zpos= Tkinter.Entry(self.tab_control, font= myfont12, width=4)
        self.entry_Zpos.insert(Tkinter.END, "0")
        self.entry_Zpos.place(x= self.lbl_Zpos.winfo_x()+ self.lbl_Zpos.winfo_width(), y= self.lbl_Zpos.winfo_y())
        self.root.update()

        self.lbl_posUnit= Tkinter.Label(self.tab_control, text='(step)')
        self.lbl_posUnit.place(x= self.entry_Zpos.winfo_x()+ self.entry_Zpos.winfo_width(), y= self.entry_Zpos.winfo_y()+self.interval_y)
        self.root.update()
        self.btn_MoveTo= Tkinter.Button(self.tab_control, text= 'GO', command= self.btn_MoveTo_click,font= myfont12_Bold, bg= self.bgGreen, fg= 'white', activebackground= self.bgGreen_active, activeforeground= 'white')
        self.btn_MoveTo.place(x= self.lbl_posUnit.winfo_x()+ self.lbl_posUnit.winfo_reqwidth()+ self.interval_x, y=self.lbl_Ypos.winfo_y())
        self.root.update()

        #======[Scanning Control] ========
        self.lbl_Scan= Tkinter.Label(self.tab_control, text="[ AUTO-SCAN ]", font= myfont14)
        self.lbl_Scan.place(x= self.interval_x, y= self.btn_MoveTo.winfo_y()+ self.btn_MoveTo.winfo_height()+self.interval_y)
        self.root.update()

        self.lbl_Scan1stPt= Tkinter.Label(self.tab_control, text= '*Start point (X, Y):',font= myfont12)
        self.lbl_Scan1stPt.place(x= self.interval_x, y = self.lbl_Scan.winfo_y()+ self.lbl_Scan.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_1stXpos= Tkinter.Entry(self.tab_control, font= myfont12, width= 6)
        self.entry_1stXpos.insert(Tkinter.END, '{0}'.format(self.scan_X[0]))
        self.entry_1stXpos.place(x= self.lbl_Scan1stPt.winfo_x(), y= self.lbl_Scan1stPt.winfo_y()+ self.lbl_Scan1stPt.winfo_height())
        self.root.update()

        self.lbl_Scan1stPt_comma= Tkinter.Label(self.tab_control, text= ', ', font= myfont12)
        self.lbl_Scan1stPt_comma.place(x=self.entry_1stXpos.winfo_x()+self.entry_1stXpos.winfo_width(), y= self.entry_1stXpos.winfo_y())
        self.root.update()

        self.entry_1stYpos= Tkinter.Entry(self.tab_control, font= myfont12, width=6)
        self.entry_1stYpos.insert(Tkinter.END, '{0}'.format(self.scan_Y[0]))
        self.entry_1stYpos.place(x= self.lbl_Scan1stPt_comma.winfo_x()+self.lbl_Scan1stPt_comma.winfo_width(), y= self.lbl_Scan1stPt_comma.winfo_y())
        self.root.update()
       
        self.lbl_ScanInterval= Tkinter.Label(self.tab_control, text='* Interval (X, Y) :', font= myfont12)
        self.lbl_ScanInterval.place(x= self.entry_1stYpos.winfo_x()+ self.entry_1stYpos.winfo_reqwidth()+ self.interval_x*4, y= self.lbl_Scan1stPt.winfo_y())
        self.root.update()
        self.entry_ScanInterval_X= Tkinter.Entry(self.tab_control, font=myfont12, width=6)
        self.entry_ScanInterval_X.insert(Tkinter.END, '{0}'.format(self.scan_X[1]))
        self.entry_ScanInterval_X.place(x= self.lbl_ScanInterval.winfo_x(), y= self.lbl_ScanInterval.winfo_y()+self.lbl_ScanInterval.winfo_height())
        self.root.update()
        self.lbl_ScanInterval_comma= Tkinter.Label(self.tab_control, text= ', ', font= myfont12)
        self.lbl_ScanInterval_comma.place(x=self.entry_ScanInterval_X.winfo_x()+self.entry_ScanInterval_X.winfo_width(), y= self.entry_ScanInterval_X.winfo_y())
        self.root.update()
        self.entry_ScanInterval_Y= Tkinter.Entry(self.tab_control, font= myfont12, width=6)
        self.entry_ScanInterval_Y.insert(Tkinter.END, '{0}'.format(self.scan_Y[1]))
        self.entry_ScanInterval_Y.place(x= self.lbl_ScanInterval_comma.winfo_x()+self.lbl_ScanInterval_comma.winfo_width(), y= self.lbl_ScanInterval_comma.winfo_y())
        self.root.update()

        self.lbl_ScanAmount= Tkinter.Label(self.tab_control, text='* Scanning Step (X, Y) :', font= myfont12)
        self.lbl_ScanAmount.place(x= self.entry_1stXpos.winfo_x(), y= self.entry_1stXpos.winfo_y()+ self.entry_1stXpos.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_ScanAmount_X= Tkinter.Entry(self.tab_control, font=myfont12, width=6)
        self.entry_ScanAmount_X.insert(Tkinter.END, '{0}'.format(self.scan_X[2]))
        self.entry_ScanAmount_X.place(x= self.lbl_ScanAmount.winfo_x(), y= self.lbl_ScanAmount.winfo_y()+self.lbl_ScanAmount.winfo_height())
        self.root.update()
        self.lbl_ScanAmount_comma= Tkinter.Label(self.tab_control, text= ', ', font= myfont12)
        self.lbl_ScanAmount_comma.place(x=self.entry_ScanAmount_X.winfo_x()+self.entry_ScanAmount_X.winfo_width(),y= self.entry_ScanAmount_X.winfo_y())
        self.root.update()
        self.entry_ScanAmount_Y= Tkinter.Entry(self.tab_control, font= myfont12, width=6)
        self.entry_ScanAmount_Y.insert(Tkinter.END, '{0}'.format(self.scan_Y[2]))
        self.entry_ScanAmount_Y.place(x= self.lbl_ScanAmount_comma.winfo_x()+self.lbl_ScanAmount_comma.winfo_width(), \
                                      y= self.lbl_ScanAmount_comma.winfo_y())
        self.root.update()

        self.btn_StartScan= Tkinter.Button(self.tab_control, text= 'Start Scan', command= self.btn_StartScan_click,font= myfont12_Bold, fg= 'white', activeforeground='white', bg=self.bgGreen, activebackground=self.bgGreen_active, width= btn_width, height= btn_height)
        self.btn_StartScan.place(x= self.entry_ScanInterval_X.winfo_x()+ self.interval_x*6, y=self.lbl_ScanAmount.winfo_y()+self.interval_y*2)
        self.root.update()
        # ===== Image Processing =======
        self.btn_saveImg= Tkinter.Button(self.tab_imageprocess, text='Save Image', command= self.btn_saveImg_click,font= myfont14, width= btn_width, height= btn_height)
        self.btn_saveImg.place(x= self.interval_x, y= self.interval_y)
        self.root.update()

        self.lbl_scracth_detect= Tkinter.Label(self.tab_imageprocess, text="[ Binarization Setting ]", font= myfont14)
        self.lbl_scracth_detect.place(x= self.interval_x, y= self.btn_saveImg.winfo_y()+ self.btn_saveImg.winfo_reqheight()+ self.interval_y)
        self.root.update()
        
        self.btn_detect= Tkinter.Button(self.tab_imageprocess, text='Binarization', command= self.methond_SimpleBinary,font= myfont12_Bold, width= btn_width, height= btn_height, fg= 'white',activeforeground='white', bg= bgGray,activebackground= bgGray_active)
        self.btn_detect.place(x= self.lbl_scracth_detect.winfo_x()+ self.lbl_scracth_detect.winfo_reqwidth()+ self.interval_x, y= self.lbl_scracth_detect.winfo_y())
        self.root.update()
        
        self.scale_threshold_graylevel = Tkinter.Scale(self.tab_imageprocess , from_= 0 , to = 255 , orient = Tkinter.HORIZONTAL , label = "Gray_level", font = myfont12, width = 7, length = 300 )
        self.scale_threshold_graylevel.set(self.threshold_graylevel)
        self.scale_threshold_graylevel.place(x= self.lbl_scracth_detect.winfo_x(), y= self.lbl_scracth_detect.winfo_y()+ self.lbl_scracth_detect.winfo_height()+self.interval_y*2)
        #self.scale_threshold_graylevel.config(state= 'disabled')
        self.root.update()

        self.scale_threshold_size = Tkinter.Scale(self.tab_imageprocess, from_ = 0 , to = 500 , orient = Tkinter.HORIZONTAL , label = "contour_size", font = myfont12, width = 7, length = 300 )
        self.scale_threshold_size.set(self.threshold_size)

        self.scale_threshold_size.place(x= self.scale_threshold_graylevel.winfo_x(), y= self.scale_threshold_graylevel.winfo_y()+ self.scale_threshold_graylevel.winfo_height())
        self.root.update()

        
        
        # ===== Main Image Frame ======
        self.frame_width, self.frame_height= int(0.5*(self.screen_width-Left_width- self.interval_x*2)), int(0.5*(self.screen_height-self.FileMenu.winfo_reqheight()- self.statuslabel.winfo_reqheight() -self.interval_y*2))
        print '*** Frame w,h: ',self.frame_width, self.frame_height 
        self.frame= np.zeros((int(self.frame_height), int(self.frame_width),3),np.uint8)
        #frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
        result = Image.fromarray(self.frame)
        result = ImageTk.PhotoImage(result)
        self.panel = Tkinter.Label(self.root , image = result)
        self.panel.image = result
        self.panel.place(x=Left_width+self.interval_x, y= 0)
        self.root.update()
        # ====== Display merge Image Frame =====
        self.mergeframe_width, self.mergeframe_height= self.frame_width, self.frame_height*2+2
        self.mergeframe= np.zeros((int(self.mergeframe_height), int(self.mergeframe_width),3),np.uint8)
        #frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
        cv2.putText(self.mergeframe, 'Display Scanning Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
        result = Image.fromarray(self.mergeframe)
        result = ImageTk.PhotoImage(result)
        self.panel_mergeframe = Tkinter.Label(self.root , image = result)
        self.panel_mergeframe.image = result
        self.panel_mergeframe.place(x=self.panel.winfo_x()+ self.panel.winfo_reqwidth(), y= 0)
        self.root.update()
        # ====== One Shot Image Frame ======
        self.singleframe_width, self.singleframe_height= self.frame_width, self.frame_height
        self.singleframe= np.zeros((int(self.singleframe_height), int(self.singleframe_width),3),np.uint8)
        cv2.putText(self.singleframe, '1 shot Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
        result = Image.fromarray(self.singleframe)
        result = ImageTk.PhotoImage(result)
        self.panel_singleframe = Tkinter.Label(self.root , image = result)
        self.panel_singleframe.image = result
        self.panel_singleframe.place(x=self.panel.winfo_x(), y= self.panel.winfo_y()+ self.panel.winfo_height())
        self.root.update()
        
        # ====== UI callback setting ======
        self.panel.after(50, self.check_frame_update)
        self.lbl_CurrPos.after(5, self.UI_callback)
        self.statuslabel.after(5, self.check_status)
        self.panel_mergeframe.bind('<Button-1>',self.mouse_LeftClick)
        # ====== Override CLOSE function ==============
        self.root.protocol('WM_DELETE_WINDOW',self.on_exit)
        # ====== Thread ========
        self.main_run_judge= True
        #self.thread_main= threading.Thread(target= self.main_run)
        self.thread_main= class_MyThread.Thread(self.main_run)
        self.thread_main.start()
        self.scanning_judge= True
        #self.thread_scanning= threading.Thread(target= self.scanning_run)
        #self.thread_scanning= class_MyThread.Thread(self.scanning_run)
        #self.thread_scanning.start()
        time.sleep(0.7)
        if self.ArdMntr.connect: 
            self.ArdMntr.set_MaxSpeed(self.MaxSpeed[0],'x')
            self.ArdMntr.set_MaxSpeed(self.MaxSpeed[1],'y')
            self.ArdMntr.set_MaxSpeed(self.MaxSpeed[2],'z')
            self.ArdMntr.set_Acceleration(self.Acceleration[0],'x')
            self.ArdMntr.set_Acceleration(self.Acceleration[1],'y')
            self.ArdMntr.set_Acceleration(self.Acceleration[2],'z')

    def store_para(self, arg_filepath, arg_filename):
        tmp=[]
        tmp.append(self.scale_threshold_graylevel.get())
        tmp.append(self.scale_threshold_size.get())
        tmp.append([int(self.entry_1stXpos.get()), int(self.entry_ScanInterval_X.get()), int(self.entry_ScanAmount_X.get())])
        tmp.append( [int(self.entry_1stYpos.get()), int(self.entry_ScanInterval_Y.get()), int(self.entry_ScanAmount_Y.get())])
        tmp.append(self.limit)
        tmp.append(self.MaxSpeed)
        tmp.append(self.Acceleration)

        self.config.write_json(self.ItemList, tmp)
        print "Para set"

    # Override CLOSE function
    def on_exit(self):
        #When you click to exit, this function is called
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            self.store_para(self.saveParaPath, self.configName)
            print 'Close Main Thread...'
            self.main_run_judge= False
            self.ArdMntr.exit= True
            self.scanning_judge= False
            #self.CamMntr.stop_clean_buffer()
            #del(self.thread_main)
            self.thread_main.exit()
            print 'Close Arduino Thread...'
            #del(self.CamMntr.thread_clean_buffer)
            #print 'Close Scanning Thread...'
            #del(self.thread_scanning)
            print self.MaxSpeed
            
            self.CamMntr.release_cap()
            self.root.destroy()

    def UI_callback(self):
        if self.ArdMntr.connect== True:
            tmp_text= '(X, Y, Z)= ('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+', '+self.ArdMntr.cmd_state.strCurZ+')'
        else:
            tmp_text='Arduino Connection Refuesed!'

        self.lbl_CurrPos.config(text= tmp_text)
        self.lbl_CurrPos.after(10,self.UI_callback)
    
    def IconResize(self, arg_readPath, arg_zoom=1, arg_subsample= 4):
        photo_resize=PhotoImage(file=arg_readPath)
        photo_resize= photo_resize.zoom(arg_zoom)
        photo_resize= photo_resize.subsample(arg_subsample)
        return photo_resize

    def mouse_LeftClick(self, event):
        if self.checkmouse_panel_mergeframe:
            mouse_x, mouse_y= event.x, event.y
            #print '>> mouse(X,Y): ',mouse_x, mouse_y
            #print '>> split(X,Y): ', self.mergeframe_splitX, self.mergeframe_splitY

            begX= self.interval_x
            begY= self.mergeframe_spaceY
            tmp_X, tmp_Y= int((mouse_x-begX)/self.mergeframe_splitX), int((mouse_y-begY)/self.mergeframe_splitY)
            #print '>> RANGE(X,Y): ',begY+ self.mergeframe_splitY*self.scan_Y[2] ,begX+ self.mergeframe_splitX*self.scan_X[2]
            if begX< mouse_x < begX+ self.mergeframe_splitX*self.scan_Y[2] and begY< mouse_y< begY+ self.mergeframe_splitY*self.scan_X[2]:
                tmp_filename= '{0}_{1}'.format(tmp_Y*self.scan_X[1], tmp_X*self.scan_Y[1]) 
                #print 'click file: ', tmp_filename
                tmp_frame= cv2.imread(self.savePath+'Scanning/Raw_'+tmp_filename+'.jpg')
                self.imagename= tmp_filename
                self.singleframe= tmp_frame.copy()
                self.display_panel_singleframe(tmp_frame)

                mergeframe_canvas= self.mergeframe.copy()
                cv2.rectangle(mergeframe_canvas,(begX+self.mergeframe_splitX*tmp_X,begY+self.mergeframe_splitY*tmp_Y),(begX+self.mergeframe_splitX*(tmp_X+1), begY+self.mergeframe_splitY*(tmp_Y+1)),(0,255,100),2 )
                result = Image.fromarray(mergeframe_canvas)
                result = ImageTk.PhotoImage(result)
                self.panel_mergeframe.configure(image = result)
                self.panel_mergeframe.image = result
            

    def check_status(self):
        self.statuslabel.config(text= self.strStatus)
        self.statuslabel.after(10,self.check_status)

    def Lock_UI(self, arg_Lock):
        if arg_Lock:
            self.menubar.entryconfig('File', state='disabled')
            self.menubar.entryconfig('Setting', state='disabled')
            self.menubar.entryconfig('Communication', state='disabled')
            self.menubar.entryconfig('Image Processing', state='disabled')
            self.btn_MoveTo.config(state= 'disabled')
            self.entry_Xpos.config(state= 'disabled')
            self.entry_Ypos.config(state= 'disabled')
            self.entry_Zpos.config(state= 'disabled')
            self.btn_detect.config(state= 'disabled')
            self.btn_saveImg.config(state= 'disabled')
            self.entry_1stXpos.config(state= 'disabled')
            self.entry_1stYpos.config(state= 'disabled')
            self.entry_ScanInterval_X.config(state= 'disabled')
            self.entry_ScanInterval_Y.config(state= 'disabled')
            self.entry_ScanAmount_X.config(state= 'disabled')
            self.entry_ScanAmount_Y.config(state= 'disabled')
            self.checkmouse_panel_mergeframe= False
        else:
            self.menubar.entryconfig('File', state='normal')
            self.menubar.entryconfig('Setting', state='normal')
            self.menubar.entryconfig('Communication', state='normal')
            self.menubar.entryconfig('Image Processing', state='normal')
            self.btn_MoveTo.config(state= 'normal')
            self.entry_Xpos.config(state= 'normal')
            self.entry_Ypos.config(state= 'normal')
            self.entry_Zpos.config(state= 'normal')
            self.btn_detect.config(state= 'normal')
            self.btn_saveImg.config(state= 'normal')
            self.entry_1stXpos.config(state= 'normal')
            self.entry_1stYpos.config(state= 'normal')
            self.entry_ScanInterval_X.config(state= 'normal')
            self.entry_ScanInterval_Y.config(state= 'normal')
            self.entry_ScanAmount_X.config(state= 'normal')
            self.entry_ScanAmount_Y.config(state= 'normal')
            self.checkmouse_panel_mergeframe= True

    def plastic_set_background(self):
        frame= self.CamMntr.get_frame()
        self.imageProcessor.set_background(frame)

    def methond_OtsuBinary(self):
        print 'Start Otsu Binary.... '
        #result= self.CamMntr.subract_test()
        self.imageProcessor.set_threshold_size(int(self.scale_threshold_size.get()))
        self.imageProcessor.set_threshold_graylevel(int(self.scale_threshold_graylevel.get()))
        result= self.imageProcessor.get_contour(self.singleframe, True, self.savePath, 'Otsu_Binary_'+self.imagename, 1)
        self.display_panel_singleframe(result)

    def methond_SimpleBinary(self):
        print 'Start Binarization with ... '
        #result= self.CamMntr.subract_test()
        self.imageProcessor.set_threshold_size(int(self.scale_threshold_size.get()))
        self.imageProcessor.set_threshold_graylevel(int(self.scale_threshold_graylevel.get()))
        result= self.imageProcessor.get_contour(self.singleframe, True, self.savePath, 'Simple_Binary_'+self.imagename, 0)
        self.display_panel_singleframe(result)

    def set_ArdConnect(self):
        self.ArdMntr.connect_serial()

    def set_CamConnect(self):
        cameraID= CameraConnection(self.root, self.CamMntr.camera_id)
        print '*** ',cameraID.result, ', ', self.CamMntr.camera_id
        if cameraID.result is not None and cameraID.result != self.CamMntr.camera_id:
            print 'Switch Camera ID'
            self.CamMntr.connect_camera(cameraID.result)

    def set_Motor(self):
        if self.ArdMntr.connect:
            Var= MotorSetting(self.root, self.MaxSpeed, self.Acceleration)
            if Var.result is not None:
                print 'result: ',Var.result
                #self.MaxSpeed= [Var.result[0], Var.result[2]]
                #self.Acceleration= [Var.result[1], Var.result[3]]
                self.MaxSpeed= [Var.result[0], Var.result[2], Var.result[4]]
                self.Acceleration= [Var.result[1], Var.result[3], Var.result[5]]
                self.ArdMntr.set_MaxSpeed(self.MaxSpeed[0],'x')
                self.ArdMntr.set_MaxSpeed(self.MaxSpeed[1],'y')
                self.ArdMntr.set_MaxSpeed(self.MaxSpeed[2],'z')
                self.ArdMntr.set_Acceleration(self.Acceleration[0],'x')
                self.ArdMntr.set_Acceleration(self.Acceleration[1],'y')
                self.ArdMntr.set_Acceleration(self.Acceleration[2],'z')
            #self.ArdMntr.set_MaxSpeed()
        else:
            tkMessageBox.showerror("Error", "Arduino connection refused!\n Please check its connection.")


    def set_frame(self, frame):
        self.frame= frame
    
    def display_panel_singleframe(self, arg_frame):
        tmp_frame= cv2.cvtColor(arg_frame, cv2.COLOR_BGR2RGB)
        #tmp_frame = self.mark_cross_line(tmp_frame)
	tmp_frame= cv2.resize(tmp_frame,(self.singleframe_width,self.singleframe_height),interpolation=cv2.INTER_LINEAR)
        result = Image.fromarray(tmp_frame)
        result = ImageTk.PhotoImage(result)
        self.panel_singleframe.configure(image = result)
        self.panel_singleframe.image = result

    def reset_mergeframe(self):
        self.mergeframe= np.zeros((int(self.mergeframe_height), int(self.mergeframe_width),3),np.uint8)
        cv2.putText(self.mergeframe, 'Display Scanning Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)

    def set_mergeframe_size(self, arg_x, arg_y):
        self.mergeframe_splitX= int((self.mergeframe_width-self.interval_x*2)/arg_y)
        self.mergeframe_splitY= int((self.mergeframe_height-100)/arg_x)
    
    def display_panel_mergeframe(self, arg_frame, arg_stepX, arg_stepY): 
        tmp_frame= cv2.cvtColor(arg_frame, cv2.COLOR_BGR2RGB)
        tmp_frame= cv2.resize(tmp_frame,(self.mergeframe_splitX,self.mergeframe_splitY),interpolation=cv2.INTER_LINEAR)
        begX= self.interval_x+self.mergeframe_splitX*arg_stepX
        begY= self.mergeframe_spaceY+ self.mergeframe_splitY* arg_stepY 
        self.mergeframe[begY:begY+ self.mergeframe_splitY, begX: begX+ self.mergeframe_splitX]= tmp_frame
        #begY= self.mergeframe_height- 50- self.mergeframe_splitY*arg_stepY
        #self.mergeframe[begY-self.mergeframe_splitY:begY, begX: begX+ self.mergeframe_splitX]= tmp_frame
        self.mergeframe_stepX= arg_stepX
        self.mergeframe_stepY= arg_stepY
        print '>> mergeframe_splitY, splitX= ', self.mergeframe_splitY, ', ', self.mergeframe_splitX
        print '>> tmp_frame.shape[0,1]= ', tmp_frame.shape[0],', ',tmp_frame.shape[1]
        
        result = Image.fromarray(self.mergeframe)
        result = ImageTk.PhotoImage(result)
        self.panel_mergeframe.configure(image = result)
        self.panel_mergeframe.image = result

    def rdbtn_click(self):
        print 'rdVal',self.MvAmount.get() 

    def btn_StartScan_click(self):
        self.imageProcessor.set_threshold_size(int(self.scale_threshold_size.get()))
        self.imageProcessor.set_threshold_graylevel(int(self.scale_threshold_graylevel.get()))
        self.input_Zpos= int(self.entry_Zpos.get())
        print 'Start'
        if self.StartScan_judge:
            #===================================
            # Delete Scanning Thread
            #===================================
            self.StartScan_judge= False
            del(self.thread_scanning)
            self.Lock_UI(True)
            self.btn_StartScan.config(text= 'Start Scan', fg='white', activeforeground= 'white', bg= self.bgGreen,activebackground= self.bgGreen_active)
        else:
            if self.ArdMntr.connect:
                try:
                    self.reset_mergeframe()
                    self.scan_X= [int(self.entry_1stXpos.get()), int(self.entry_ScanInterval_X.get()), int(self.entry_ScanAmount_X.get())]
                    self.scan_Y= [int(self.entry_1stYpos.get()), int(self.entry_ScanInterval_Y.get()), int(self.entry_ScanAmount_Y.get())]
                    self.set_mergeframe_size(self.scan_X[2], self.scan_Y[2])
                    self.reset_mergeframe()
                    #print '### ', self.scan_X, self.scan_Y
                
                    self.ArdMntr.move_Coord(self.scan_X[0], self.scan_Y[0], self.input_Zpos)
                    if self.scan_X[0]+self.scan_X[1]*self.scan_X[2]<self.limit[0] | self.scan_Y[0]+self.scan_Y[1]*self.scan_Y[2]<self.limit[1]:
                        self.StartScan_judge= True
                        #=================================
                        # New Thread of Scanning process
                        #================================
                        self.thread_scanning= threading.Thread(target= self.scanning_run)
                        self.thread_scanning.start()
                        print '*** scanning...'
                    	self.Lock_UI(True)
                    	self.btn_StartScan.config(text= 'STOP Scan', fg='white', activeforeground= 'white', bg= self.bgRed, activebackground= self.bgRed_active)
                    else:
                        tkMessageBox.showerror("Error", "The scanning of X should be in [0~{0}]\nThe range of Y should be in [0~{1}]".format(self.limit[0],self.limit[1]))
                except:
                    tkMessageBox.showerror('Error', 'Please enter nubmer')
            else:
                tkMessageBox.showerror("Error", "Arduino connection refused!")


    def btn_saveImg_click(self):
        #self.saveImg= True
        #self.Lock_UI(False)
        self.imagename= 'Frame1'
        self.singleframe = self.CamMntr.get_frame()
        self.saveImg_function(self.singleframe, self.savePath, self.imagename)
        self.display_panel_singleframe(self.singleframe)


    def btn_MoveTo_click(self):
        if self.ArdMntr.connect:
            try:
                Target_X= int(self.entry_Xpos.get())
                Target_Y= int(self.entry_Ypos.get())
                Target_Z= int(self.entry_Zpos.get())
                if (Target_X>=0) & (Target_X<=self.limit[0]) & (Target_Y>=0) & (Target_Y<=self.limit[1]):
                    cmd= 'G00 X{0} Y{1} Z{2}'.format(Target_X, Target_Y, Target_Z)
                    #self.ArdMntr.serial_send(cmd)
                    print 'ArdMntr.move_Coord...'
                    self.ArdMntr.move_Coord(Target_X, Target_Y, Target_Z)
                    print 'Command: ',cmd
                    time.sleep(1)                
                else:
                    tkMessageBox.showerror("Error", "The range of X should be in [0~{0}]\nThe range of Y should be in [0~{1}]".format(self.limit[0],self.limit[1]))
            
            except:
                tkMessageBox.showerror("Error", "Please enter number!")
        else:
            tkMessageBox.showerror("Error", "Arduino connection refused!")

    def mark_cross_line(self , frame):
        w = frame.shape[0] / 2
        h = frame.shape[1] / 2
        cv2.line(frame , (h - 15 , w) , (h + 15 , w) , (255 , 0 , 0) , 1)
        cv2.line(frame , (h , w - 15) , (h , w + 15) , (255 , 0 , 0) , 1)
        return frame

    def saveImg_function(self, arg_frame,arg_savePath, arg_filename):
        # make sure output dir exists
        if(not path.isdir(arg_savePath)):
            makedirs(arg_savePath)
        #tmp= cv2.cvtColor(arg_frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(arg_savePath+arg_filename+'.jpg',arg_frame)
    
    def scanning_run(self):
        step=0
        #while self.scanning_judge:
        if self.StartScan_judge:
            print '>>> Scanning...'
            for step_X in range(0, self.scan_X[2]):
                for step_Y in range(0, self.scan_Y[2]):
                    if self.StartScan_judge== False:
                        break
                    if step_X % 2 ==0:
                        tmp_step_Y= step_Y
                    else:
                        tmp_step_Y= self.scan_Y[2]- step_Y-1
                    tmp_X, tmp_Y= self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ tmp_step_Y*self.scan_Y[1]
                    #tmp_X, tmp_Y= self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ step_Y*self.scan_Y[1]
                    print '>> X, Y: ', tmp_X, ', ', tmp_Y
                    #self.saveScanning= 'Raw_{0}_{1}.png'.format(self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ step_Y*self.scan_Y[1])
                    self.ArdMntr.move_Coord(tmp_X, tmp_Y, self.input_Zpos)
                    time.sleep(1)
                    while 1:
                        if (self.ArdMntr.cmd_state.is_ready()):
                            time.sleep(0.5)
                            #self.saveScanning= '{0}_'.format(step)+self.ArdMntr.cmd_state.strCurX+'_'+self.ArdMntr.cmd_state.strCurY
                            #self.saveScanning= self.ArdMntr.cmd_state.strCurX+'_'+self.ArdMntr.cmd_state.strCurY
                            self.saveScanning= '{0}_{1}'.format(tmp_X, tmp_Y)
                            frame= self.CamMntr.get_frame()
                            self.saveImg_function(frame, self.savePath+'Scanning/','Raw_'+self.saveScanning)
                            result= self.imageProcessor.get_contour(frame, True, self.savePath+'Scanning/', 'Detect_'+self.saveScanning,1)
                            self.display_panel_singleframe(result)
                            #self.display_panel_mergeframe(result, step_X, step_Y)
                            #self.display_panel_mergeframe(result, step_Y, step_X)
                            self.display_panel_mergeframe(result, tmp_step_Y, step_X)
                            
                            print self.saveScanning
                            #time.sleep(2)
                            break
                        else:
                            time.sleep(1)
                    if self.StartScan_judge== False:
                        break
                    step= step+1
            self.StartScan_judge= False
            self.Lock_UI(False)
            self.btn_StartScan.config(text= 'Start Scan', fg='white', activeforeground='white', bg= self.bgGreen, activebackground= self.bgGreen_active)
        else:
            time.sleep(0.2)
            step=0      


    def check_frame_update(self):
        result = Image.fromarray(self.frame)
        result = ImageTk.PhotoImage(result)
        self.panel.configure(image = result)
        self.panel.image = result
        self.panel.after(8, self.check_frame_update)

    def main_run(self):
        frame= self.CamMntr.get_frame()
        if frame is not -1:
            frame= cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.mark_cross_line(frame)
            frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
            text='Arduino Connection Refused ...'
            color= (0,0,0)
            if self.ArdMntr.connect== True:
                if self.StartScan_judge == False:
                    if self.ArdMntr.cmd_state.is_ready():
                        text= 'Idling ...'
                        color = (0 , 255 , 0)
                    else:
                        text= 'Moving ...'
                        color = (255,0,0)
                else:
                    if self.ArdMntr.cmd_state.is_ready():
                        text= 'Processing...'
                        color = (0 , 255 , 0)
                    else:
                        text= 'Scanning...'+'(X, Y)= ('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+')'
                        color = (255,0,0)
            cv2.putText(frame, text,(10,40),cv2.FONT_HERSHEY_SIMPLEX, 0.7,color,1)
            self.strStatus= text
            self.set_frame(frame)
        time.sleep(0.01)

root = Tkinter.Tk()
root.title("[Arduino] Stepper Control")
root.attributes('-zoomed', True) # FullScreen
app= App(root)
root.mainloop()
