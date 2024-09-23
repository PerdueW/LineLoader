#!/usr/bin/python

import Tkinter, tkFileDialog
import Tkinter as tk
import tkFont
import ttk as ttk 
import os
import os.path
import sys
import platform
import tkMessageBox
import threading
import socket
import multiprocessing
import time
from multiprocessing import Process, Queue
from ScrolledText import *
from modules import ValProcess
from modules import SysManInit
import csv
from collections import defaultdict
import pandas as pd
import re
import numpy as np
import mysql.connector
from mysql.connector import Error
import datetime

pd.set_option('display.max_columns', 50)
#serverip = "192.168.60.15"
#user = "valcom"
#passwd = "&&VALcom6969"
#database = "LineLoaderDB"
serverip = ""
user = ""
passwd = ""
database = ""
connect_timeout = 1

sizex = 1120
sizey = 650
posx  = 0
posy  = 0

csizex = 450
csizey = 100
cposx  = 0
cposy  = 0
'''
 This portion of the code will take the path from command line to where the files are stored for the program and 
 make them available to the rest of the program.
'''
        
class lineLoader:
    def __init__(self, root):
        '''
        This function called the function that creates the initial screen for the application and also sends 
        the initial command to SysManger to start collecting the MAC addresses and indentifying what device 
        type they belong to and how many there are of each device type. 
        ''' 
        self.win = 0
        self.btns = {}
        self.clearedGrps = []
        self.failwindowClicked = 0
        self.tosavetoDB = {}
        self.storedGroup = []
        self.loadinggroups = []
        self.remaininggroups = []
        self.workorders = {}
        self.resps = {}
        self.macClicked = 0
        self.macfailedreasonClicked = 0
        detectedOS = platform.system()
        #print "detectedOS = ", detectedOS
        if detectedOS == "Windows":
            self.win = 1
        else:
            self.win = 0
        self.main = ValProcess(SysManInit)   
        self.Gui() 
        self.queueMonitor()
        self.mainwinx = 0
        self.mainwiny = 0
                        
    def queueMonitor(self):   
        '''
        This function is the main function that controls the in comning messages from system manager
        and routes them to the appropriate function to be processed and data displayed for user
        review
        '''   
        self.storedResults = 0                                  
        msg = self.main.que.rxFrom()
        if msg is not None and msg is not "" and msg['name'] in self.resps:
            self.resps[msg['name']](msg)                                                      
        root.after(100, lambda : self.queueMonitor())
        
    def statusReply(self, msg):
        packet = msg['data']
        if packet == "No Device Attached.":
            msg = {"name":"getGroupStatus", "data":""}       
            self.main.que.sendTo(msg) 
            self.resps["getGroupStatusResp"] = self.statusReply
        else:
            self.updateGui(msg) 
                         
    def Gui(self):  
        '''
        This function created the actual User Interface and controls the locaton, font and
        other functions of the User Interface.
        '''  
        self.helv8 = tkFont.Font(family="Helvetica", size=8)
        self.helv8b = tkFont.Font(family="Helvetica", size=8, weight="bold")   
        self.helv9 = tkFont.Font(family="Helvetica", size=9)
        self.helv9b = tkFont.Font(family="Helvetica", size=9, weight="bold")    
        self.helv10 = tkFont.Font(family="Helvetica", size=10)
        self.helv10b = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.helv11 = tkFont.Font(family="Helvetica", size=11)
        self.helv11b = tkFont.Font(family="Helvetica", size=11, weight="bold")
        self.helv12 = tkFont.Font(family="Helvetica", size=12)
        self.helv12b = tkFont.Font(family="Helvetica", size=12, weight="bold")
        self.helv13 = tkFont.Font(family="Helvetica", size=13)
        self.helv13b = tkFont.Font(family="Helvetica", size=13, weight="bold")
        
        mainFrame = tk.Frame(root)
        mainFrame.grid(row=0, column=0)
        headerFrame = tk.Frame(mainFrame)
        headerFrame.grid(row=0, column=0, columnspan=5)
        deviceFrame =tk.Frame(mainFrame)
        deviceFrame.grid_columnconfigure(0, weight=1)
        deviceFrame.grid(row=1, column=0, rowspan=5, columnspan=6)             
        self.canvas=tk.Canvas(deviceFrame, width=1098, height=460)
        self.myscrollbar=tk.Scrollbar(deviceFrame, width=15, orient="vertical", command=self.canvas.yview)
        self.scrollableFrame=tk.Frame(self.canvas, width=1098, height=575, borderwidth=1)
        self.scrollableFrame.grid(row=0,column=0,sticky='nsew')
        self.myscrollbar.grid(row=0,column=6,sticky='ns')
        self.canvas.configure(yscrollcommand=self.myscrollbar.set)
        self.canvas.create_window((0,0), window=self.scrollableFrame, anchor='nw')
        self.canvas.grid(row=0,column=0, sticky='nw')
        self.scrollableFrame.bind("<Configure>",lambda event: self.myCanvasfunction(event))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        controlFrame =tk.Frame(mainFrame)
        controlFrame.grid(row=6, column=0, columnspan=6)
        if self.win == 1:
            grpLabel =  tk.Label(headerFrame, text="Group   ", width=7, font=self.helv11b)
            grpLabel.config(anchor='e')
            grpLabel.grid(row=0, column=0, sticky='w')
            
            modelLabel =  tk.Label(headerFrame, text="Device Type", width=33, font=self.helv11b)
            modelLabel.grid(row=0, column=1, sticky='w')
            
            nummodelLabel =  tk.Label(headerFrame, text="# Devices", width=7, font=self.helv11b)
            nummodelLabel.grid(row=0, column=2, sticky='w')
            
            loadLabel =tk.Label(headerFrame, text="", width=23, font=self.helv11b)
            loadLabel.grid(row=0, column=3, sticky='w')
            
            blankLabel1 =tk.Label(headerFrame, text="", width=23, font=self.helv11b)
            blankLabel1.grid(row=0, column=4, sticky='w')
            blankLabel2 =tk.Label(headerFrame, text="", width=23, font=self.helv11b)
            blankLabel2.grid(row=0, column=5, sticky='w')
        else:
            grpLabel =  tk.Label(headerFrame, text="Group   ", width=8, font=self.helv11b)
            grpLabel.config(anchor='e')
            grpLabel.grid(row=0, column=0, sticky='w')
            
            modelLabel =  tk.Label(headerFrame, text="Device Type", width=36, font=self.helv11b)
            modelLabel.grid(row=0, column=1, sticky='w')
            
            nummodelLabel =  tk.Label(headerFrame, text="# Devices", width=8, font=self.helv11b)
            nummodelLabel.grid(row=0, column=2, sticky='w')
            
            loadLabel =tk.Label(headerFrame, text="", width=24, font=self.helv11b)
            loadLabel.grid(row=0, column=3, sticky='w')
            
            blankLabel1 =tk.Label(headerFrame, text="", width=24, font=self.helv11b)
            blankLabel1.grid(row=0, column=4, sticky='w')
            blankLabel2 =tk.Label(headerFrame, text="", width=24, font=self.helv11b)
            blankLabel2.grid(row=0, column=5, sticky='w')
            
        controlpanelSpacer = tk.Label(controlFrame, text="", width=20, font=self.helv11b)
        controlpanelSpacer.grid(row=1, column=0, columnspan=6, sticky='e')
        exitBtn =tk.Button(controlFrame, text="Exit", command=self.close_window, width=10)
        exitBtn.grid(row=1, column=8, sticky='e')
        
        self.resps["getGroupStatusResp"] = self.statusReply
        msg = {"name":"getGroupStatus", "data":""}       
        self.main.que.sendTo(msg) 
        
    def myCanvasfunction(self, event):
        self.canvas.configure(scrollregion=(0,0,200,1098), width=1098, height=590)   

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta/120), "units")
        self.canvas.focus() 
        
    def updateGui(self, msg):
        """
        This function updates the initial program screen with the model and number of 
        macs associates with the model and also adds the 'LOAD' button to the interface
        to start the process of loading the devices with teh chosen configuration.
        """ 
        if msg['name'] == "LoadResp":
            initmsg = msg['data']
            status = initmsg['status']
            y      = initmsg['grpid']
            if status == "Loading...": 
                self.btns[y][3].configure(state = "disable")
                self.btns[y][4].configure(state = "disable")
                self.btns[y][4].configure(bg="#FFFFCC", text="Loading...")
                self.btns[y][5].configure(state = "disable")            
        else:        
            packet = msg['data']      
            for data in packet:
                y          = data['grpid'] 
                model      = data['model'] 
                deviceType = data['model'] 
                numMacs    = data['count'] 
                status     = data['status'] 
                             
                identifierpath = str(initialPath + "/device_type_identifiers.txt")                
                exists = os.path.isfile(identifierpath)
                if exists:
                    with open(initialPath + "/device_type_identifiers.txt") as deviceFile:
                        for line in deviceFile:
                            line = line.strip()
                            identifier, productName = line.partition("=")[::2]
                            if identifier == deviceType:
                                deviceType = productName
                            else:
                                pass    
                else:
                    tkMessageBox.showinfo('Device Type File Missing', 'Please verify your ' + '"' + 'device_type_identifiers' + '"' + ' file exists and restart the program.') 
                    self.close_window()       
                    return             
                
                if y not in self.btns:                
                    self.btns[y] = []
                    self.remaininggroups.append(y)
                    if self.win == 1:
                        groupLabel =  tk.Label(self.scrollableFrame, text=y, width=7, font=self.helv11)
                        self.btns[y].append(groupLabel)
                        groupLabel.grid(row=y, column=0)      
                        modelLabel =  tk.Label(self.scrollableFrame, text=deviceType, width=33, font=self.helv11)
                        self.btns[y].append(modelLabel)
                        modelLabel.grid(row=y, column=1)
                        nummodelLabel =  tk.Label(self.scrollableFrame, text=numMacs, width=7, font=self.helv11)
                        self.btns[y].append(nummodelLabel)
                        nummodelLabel.grid(row=y, column=2)
                        msg1 = {'grpid':y, 'model':model, 'deviceType':deviceType, 'numMacs':numMacs, 'count':numMacs, 'status':status}
                        loadBtn =tk.Button(self.scrollableFrame, text="Load", command=lambda msg1=msg1:self.config_window(msg1), width=23, height=3, font=self.helv11)
                        self.btns[y].append(loadBtn)
                        loadBtn.grid(row=y, column=3)   
                        statusBtn =tk.Button(self.scrollableFrame, text="Status", command=lambda msg1=msg1:self.getdMacResults(msg1), width=23, state='disabled', height=3, font=self.helv11)
                        self.btns[y].append(statusBtn)
                        statusBtn.grid(row=y, column=4)
                        clearBtn =tk.Button(self.scrollableFrame, text="Clear", command=lambda y=y:self.clearGroup(y), width=23, state='normal', height=3, font=self.helv11)
                        self.btns[y].append(clearBtn)
                        clearBtn.grid(row=y, column=5) 
                    else:
                        groupLabel =  tk.Label(self.scrollableFrame, text=y, width=8, font=self.helv11)
                        self.btns[y].append(groupLabel)
                        groupLabel.grid(row=y, column=0)      
                        modelLabel =  tk.Label(self.scrollableFrame, text=deviceType, width=36, font=self.helv11)
                        self.btns[y].append(modelLabel)
                        modelLabel.grid(row=y, column=1)
                        nummodelLabel =  tk.Label(self.scrollableFrame, text=numMacs, width=8, font=self.helv11)
                        self.btns[y].append(nummodelLabel)
                        nummodelLabel.grid(row=y, column=2)
                        msg1 = {'grpid':y, 'model':model, 'deviceType':deviceType, 'numMacs':numMacs, 'count':numMacs, 'status':status}
                        loadBtn =tk.Button(self.scrollableFrame, text="Load", command=lambda msg1=msg1:self.config_window(msg1), width=24, height=3, font=self.helv11)
                        self.btns[y].append(loadBtn)
                        loadBtn.grid(row=y, column=3)   
                        statusBtn =tk.Button(self.scrollableFrame, text="Status", command=lambda msg1=msg1:self.getdMacResults(msg1), width=24, state='disabled', height=3, font=self.helv11)
                        self.btns[y].append(statusBtn)
                        statusBtn.grid(row=y, column=4)
                        clearBtn =tk.Button(self.scrollableFrame, text="Clear", command=lambda y=y:self.clearGroup(y), width=24, state='normal', height=3, font=self.helv11)
                        self.btns[y].append(clearBtn)
                        clearBtn.grid(row=y, column=5) 
                else:
                    statuses = ''
                    for key in status:
                        statuses += key + " " + str(status[key]) + "\n"
                        if key == "IDLE": 
                            if y not in self.clearedGrps:
                                self.btns[y][2].configure(text=numMacs) 
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "normal") 
                                if y in self.remaininggroups:
                                    self.btns[y][3].configure(state = "normal") 
                                else:
                                    pass      
                            else:
                                pass  
                        if key == "Loading": 
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable")   
                            else:
                                pass 
                            for y in self.remaininggroups:
                                self.btns[y][3].configure(state = "normal")        
                        if key == "PASS":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass     
                        if key == "FAIL":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "Configuring IP":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "Running PreScript":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "Running PostScript":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "Loading Tar":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "Load Complete":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFFCC", text=statuses)
                                self.btns[y][5].configure(state = "disable") 
                            else:
                                pass
                        if key == "ERROR":
                            if y not in self.clearedGrps:
                                self.btns[y][3].configure(state = "disable")
                                self.btns[y][4].configure(state = "disable")
                                self.btns[y][4].configure(bg="#FFFF00", text=statuses)
                                self.btns[y][5].configure(state = "normal") 
                            else:
                                pass 
                         
                        if "Group Complete" in data: 
                            if y not in self.clearedGrps:
                                self.btns[y][2].configure(text=numMacs) 
                                self.btns[y][4].configure(state = "normal")
                                if data["Group Complete"] == "PASS":
                                    self.btns[y][4].configure(bg="#00cc00", text="Group Load Complete: Passed")
                                elif data["Group Complete"] == "FAIL":
                                    self.btns[y][4].configure(bg="#FF0000", text="Group Load Complete: Failed")
                                else:
                                    self.btns[y][4].configure(bg="#ccff00", text="Group Load Complete: Unknown")
                                self.btns[y][5].configure(state = "normal") 
                                if y in self.storedGroup:
                                    pass
                                else:   
                                    self.storedGroup.append(y)
                                    grpid = y
                                    msg = {'name':'failedModels', 'data': grpid}
                                    self.main.que.sendTo(msg)  
                            else:
                                pass
                        else:
                            if y not in self.clearedGrps:
                                pass
                            else:
                                pass 
                            for group in self.remaininggroups:
                                self.btns[group][3].configure(state = "normal") 
                        if self.macClicked == 0:
                            self.resps["failedModelsResp"] = self.storeResults
                        else:
                            pass
        self.resps["getGroupStatusResp"] = self.statusReply      
        msg = {"name":"getGroupStatus", "data":""}       
        self.main.que.sendTo(msg)
        self.mainwinx = root.winfo_x()
        self.mainwiny = root.winfo_y()
        
    def config_window(self, msg):
        """
        This function creates the Congiuration screen the user can enter via keyboard or scan 
        the configuration file they wish to use to load the devices. It will not allow the user
        proceed pass this step without entering a configuration file name.
        """                 
        y = msg['grpid']
        self.btns[y][3].configure(state = "disable")
        self.group = msg['grpid']
        self.deviceType = msg['deviceType'] 
        self.numMacs = msg['count']
        self.status = msg['status']
        
        with open(initialPath + "/device_type_identifiers.txt") as deviceFile:
                for line in deviceFile:
                    line = line.strip()
                    identifier, productName = line.partition("=")[::2]
                    if identifier == self.deviceType:
                        deviceType = productName
                    else:
                        pass         
        root.withdraw()
        self.cwindow = tk.Toplevel(root)
        self.cwindow.title(str(y) + " " + self.deviceType + " Product ID ")
        self.cwindow.wm_geometry("%dx%d+%d+%d" % (csizex,csizey,cposx,cposy)) 
        self.cwindow.resizable(width=False, height=False) 
        self.cwindow.update_idletasks()
        cw = self.cwindow.winfo_screenwidth()
        ch = self.cwindow.winfo_screenheight()
        csize = tuple(int(_) for _ in self.cwindow.geometry().split('+')[0].split('x'))
        cx = cw/2 - size[0]/2 + 300
        cy = ch/2 - size[1]/2 + 50
        self.cwindow.geometry("%dx%d+%d+%d" % (csize + (self.mainwinx, self.mainwiny)))
        configEntryLabel = tk.Label(self.cwindow, text="Product ID")
        configEntryLabel.config(width=10)
        configEntryLabel.grid(row=0, column=0, sticky='w')
        self.configEntry = tk.Entry(self.cwindow, width=30)
        self.configEntry.config(bg='white')
        self.configEntry.grid(row=0, column=1, columnspan=2)
        self.configEntry.focus_force() 
        woEntryLabel = tk.Label(self.cwindow, text="Workorder #")
        woEntryLabel.config(width=10)
        woEntryLabel.grid(row=1, column=0, sticky='w')
        self.woEntry = tk.Entry(self.cwindow, width=30)
        self.woEntry.config(bg='white')
        self.woEntry.grid(row=1, column=1, columnspan=2)
        directloadBtn =tk.Button(self.cwindow, text="Start Load", command=lambda msg=msg:self.startLoad(msg), width=13, font=self.helv10)
        directloadBtn.grid(row=0, column=4)        
        configBtn =tk.Button(self.cwindow, text="Configure Load", command=lambda msg=msg:self.setAnswer(msg), width=13, font=self.helv10)
        configBtn.grid(row=1, column=4)  
        backBtn =tk.Button(self.cwindow, text="Back", command=lambda msg=msg:self.close_configwindow(y), width=13, font=self.helv10)
        backBtn.grid(row=2, column=4)
        self.cwindow.protocol("WM_DELETE_WINDOW",  on_close)

    def setAnswer(self, msg):
        '''
        This function captures the product ype id either scnaned or typed in and verified if it is a valid
        product type for the devices connected and then called the optionsWindow function to display data
        conrtained in the device types configuration files.
        '''
        grpid = msg['grpid']
        deviceType = msg['deviceType']
        numMacs = msg['numMacs']
        productId = tk.StringVar()   
        productId = self.configEntry.get()
        productId = productId.upper()
        products = []
        workorder = tk.StringVar()   
        workorder = self.woEntry.get()
        workorder = workorder.upper()
        if workorder in self.workorders:
            pass
        else:
            self.workorders[grpid] = workorder
        if len(self.configEntry.get()) == 0:
            tkMessageBox.showinfo("No Input", "Please scan or type a Product ID")
            self.configEntry.focus_force()
        else:            
            exists = os.path.isfile(initialPath + "/FirmWare.csv")
            if exists:
                with open(initialPath + "/FirmWare.csv") as productFile:
                    productLine = pd.read_csv(productFile)
                    productLine.set_index('Product', inplace=True)
                    products =  productLine.index.values               
                if productId not in products:
                    tkMessageBox.showinfo("Unknown Product ID", "Please scan or type a valid Product ID")
                    self.configEntry.focus_force() 
                else:
                    msg = {"name":"retrieveproductData", "grpid":grpid, "deviceType": deviceType, "productId": productId, "numMacs": numMacs}
                    self.optionsWindow(msg)   
            else:
                tkMessageBox.showinfo('FirmWare File Missing', 'Please verify that the ' + '"' + 'FirmWare.csv' + '"' + ' file exists and try again.')
                self.configEntry.focus_force()                

    def owon_select(self, event=None): 
        '''
        This function handles getting values from the Models File and setting the values in the
        Options Window based on retrieved values.
        '''            
        version = self.owreleases.get()
        owdataset = self.owfuncGrpdata
        owdataset = owdataset.fillna('')
        owdataset = owdataset[['Function Group', 'Release Desc', 'File Name', 'APP Version', 'VipRunStp Version', 'vstartup Version', 
                               'Firmware', 'Platform']]
        funcGroups = owdataset['Function Group'].tolist()
        if funcGroups == '':
            tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "Function Group" in the Specific Model file.') 
            return
        elif self.owmainfuncGrp not in funcGroups:
            tkMessageBox.showinfo('File Integrity Issue', 'Please check for the "Function Group" in the Specific Model file.') 
            return 
        else:
            pass
        owdatasetValues = owdataset.loc[owdataset['Release Desc'] == version]
        owfilename = owdatasetValues.loc[:, ['File Name']].values
        owfilename = owfilename[0][0]
        self.owfilenameactual.config(text=owfilename)
        self.owfilename = owfilename
        if self.owfilename == '':
            tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "File Name" in the "FirmWare" file.') 
            return 
        else:
            pass
        owappversion = owdatasetValues.loc[:, ['APP Version']].values
        owappversion = owappversion[0][0]
        self.owappversionactual.config(text=owappversion)
        self.owappver = owappversion
        if self.owappver == '':
            tkMessageBox.showinfo('Missing File Component', 'Please verify that the "Application Version" in the Model Specific File exits.') 
            return 
        else:
            pass
        
        owVipRunStpVersion = owdatasetValues.loc[:, ['VipRunStp Version']].values
        owVipRunStpVersion = owVipRunStpVersion[0][0]
        self.owvipRunStpVersionactual.config(text= owVipRunStpVersion)
        self.owviprunstp = owVipRunStpVersion
        
        owvstartupVersion = owdatasetValues.loc[:, ['vstartup Version']].values
        owvstartupVersion = owvstartupVersion[0][0]
        self.owvstartupVersionactual.config(text=owvstartupVersion)
        self.owvstartup = owvstartupVersion
        
        owfirmware = owdatasetValues.loc[:, ['Firmware']].values
        owfirmware = owfirmware[0][0]
        self.owfirmwareactual.config(text=owfirmware)
        
        owplatform = owdatasetValues.loc[:, ['Platform']].values
        owplatform = owplatform[0][0]
        self.owplatformactual.config(text=owplatform)   
                                 
    def optionsWindow(self, msg):
        """
        This function creates the Options Window the user can either load the devices from the screen
        with the default confugrsations scanned in earlier or alter the confuguration as needed before
        loading the devices.
        """  
        detailswindowsMSG = msg
        self.cwindow.withdraw()
        group = msg['grpid']
        y = msg['grpid']
        self.group = msg['grpid']
        deviceType = msg['deviceType']
        numMacs = msg['numMacs'] 
        productId = msg['productId'] 
        devsLoaded = 0
        product = None
        
        owproductdata = pd.read_csv(initialPath + '/FirmWare.csv')
        if owproductdata['Product'].duplicated().any():
            #tkMessageBox.showinfo('Product Duplication Found', 'Duplicated Products Found. Fix Duplicates and restart program. Closing program. ')
            #msg = {"name":"Exit", "data":""}
            #self.main.que.sendTo(msg)  
            #sys.exit() 
            pass
        else:
            pass
        owproductdata.set_index("Product", inplace=True)
        owproductdata.head()
        owproductdata = owproductdata.replace(np.nan, '', regex=True)
        owproducts = owproductdata.index.get_values()
                    
        if productId in owproducts:
            owproduct  = productId
            owdesc = owproductdata.loc[productId, 'Description']
            owmodel = owproductdata.loc[productId, 'Model']
            self.owmodel = owproductdata.loc[productId, 'Model']
            self.owmainfuncGrp = owproductdata.loc[productId, 'Functional Group']
            if self.owmainfuncGrp == '':
                tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "Functional Group" Indicator is in the "FirmWare" file.') 
                self.close_configwindow(y) 
                return
            else:
                pass
                
            owicLic = owproductdata.loc[productId, 'IC License']
            owicLic = str(owicLic).upper()
            owicEnab = owproductdata.loc[productId, 'IC Enable']
            owicEnab = str(owicEnab).upper()
            owsynappsLic = owproductdata.loc[productId, 'SynApps License']
            owsynappsLic = str(owsynappsLic).upper()
            owsynappsEnab = owproductdata.loc[productId, 'SynApps Enable']
            owsynappsEnab = str(owsynappsEnab).upper()
            #polycomLic = productdata.loc[productId, 'Polycom  License']
            #icEnab = icEnab.upper()
            owpolycomEnab = owproductdata.loc[productId, 'PolyCom Enable']
            owpolycomEnab = str(owpolycomEnab).upper()
            owdhcpEnab = owproductdata.loc[productId, 'DHCP']
            owdhcpEnab = str(owdhcpEnab).upper()
            owflasherEnab = owproductdata.loc[productId, 'Flasher']
            owflasherEnab = str(owflasherEnab).upper()
            self.owbfdevtype = owproductdata.loc[productId, 'bf-device-type']
            
            self.owtransmitbfdevtype = owproductdata.loc[productId, 'bf-device-type']
            if self.owtransmitbfdevtype == '':
                tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "bf-device-type" value in the "FirmWare" file.')
                self.close_configwindow(y) 
                return
            else:
                self.owtransmitbfdevtype = int(self.owtransmitbfdevtype)
            if self.owbfdevtype == '':
                tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "bf-dev-type" is in the "FirmWare" file.') 
                self.close_configwindow(y) 
                return
            else:
                pass

            inputs = owproductdata.loc[productId, 'bdtinputs']
            if inputs == '':
                inputs = ''
            elif type(inputs) == str:
                tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Inputs" in FirmWare file is an Integer.') 
                self.close_configwindow(y) 
                return
            else:
                inputs = int(owproductdata.loc[productId, 'bdtinputs'])
                inputs = str(inputs)
            channels = owproductdata.loc[productId, 'bdtchannels']
            if channels == '':
                channels = ''
            elif type(channels) == str:
                tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Channels" in FirmWare file is an Integer.') 
                self.close_configwindow(y) 
                return
            else:
                channels = int(owproductdata.loc[productId, 'bdtchannels'])
                channels = str(channels)
            relays = owproductdata.loc[productId, 'bdtrelays']
            if relays == '':
                relays = ''
            elif type(relays) == str:
                tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Relays" in FirmWare file is an Integer.') 
                self.close_configwindow(y) 
                return
            else:
                relays = int(owproductdata.loc[productId, 'bdtrelays'])
                relays = str(relays)
            inputConfiguration = owproductdata.loc[productId, 'bdtinputConfiguration']
            if inputConfiguration == '':
                inputConfiguration = ''
            elif type(inputConfiguration) == str:
                tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Input Configuration" in FirmWare file is an Integer.') 
                self.close_configwindow(y) 
                return
            else:
                inputConfiguration = int(owproductdata.loc[productId, 'bdtinputConfiguration'])
                inputConfiguration = str(inputConfiguration)  
            flashers = owproductdata.loc[productId, 'bdtflashers']
            if flashers == '':
                flashers = ''
            elif type(flashers) == str:
                tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Flashers" in FirmWare file is an Integer.') 
                self.close_configwindow(y) 
                return
            else:
                flashers = int(owproductdata.loc[productId, 'bdtflashers'])
                flashers = str(flashers)                      
            bdtfirmware = str(owproductdata.loc[productId, 'bdtfirmware'])
            bdtfirmware = str(bdtfirmware)
            
            scanbfdevicetype = owproductdata.loc[productId, 'scan_bf-device-type']
            if scanbfdevicetype == '':
                tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "scan_bf-device-type" in the "FirmWare" file.') 
            else:
                scanbfdevicetype = int(scanbfdevicetype)
                scanbfdevicetype = str(scanbfdevicetype)               
        #with open(initialPath + "/device_type_identifiers.txt") as owdeviceFile:
        #    for line in owdeviceFile:
        #        line = line.strip()
        #        identifier, productName = line.partition("=")[::2]
        #        if int(identifier) == int(self.owbfdevtype):
        #            self.owbfdevtype = productName
        #            break
        #        else:
        #            pass 
             
        self.lwindow = tk.Toplevel(root)
        self.lwindow.title("[" + str(group) + "]" + " " + deviceType + " Product Load")
        lsizex = sizex
        lsizey = sizey
        self.lwindow.wm_geometry("%dx%d+%d+%d" % (lsizex,lsizey,posx,posy)) 
        self.lwindow.resizable(width=False, height=False) 
        self.lwindow.update_idletasks()
        lw = self.lwindow.winfo_screenwidth()
        lh = self.lwindow.winfo_screenheight()
        lsize = tuple(int(_) for _ in self.lwindow.geometry().split('+')[0].split('x'))
        lx = lw/2 - size[0]/2
        ly = lh/2 - size[1]/2 - 50
        self.lwindow.geometry("%dx%d+%d+%d" % (lsize + (self.mainwinx, self.mainwiny)))  
                
        owblankLabel = tk.Label(self.lwindow, text="")
        owblankLabel.config(width=20)
        owblankLabel.grid(row=0, column=0, sticky='w')
        
        owproductLabel = tk.Label(self.lwindow, text="Product:", font=self.helv11, anchor = 'w')
        owproductLabel.config(width=20)
        owproductLabel.grid(row=1, column=0, sticky='w')
        
        owproductText = tk.StringVar()
        owproductText = owproduct
        self.owproductLbl = tk.Label(self.lwindow, text=owproductText, font=self.helv11, anchor = 'w')
        self.owproductLbl.config(width=50)
        self.owproductLbl.grid(row=1, column=1, sticky='w')
        
        owdescLabel = tk.Label(self.lwindow, text="Description:", font=self.helv11, anchor = 'w')
        owdescLabel.config(width=20)
        owdescLabel.grid(row=2, column=0, columnspan=2, sticky='w')
        
        owdescText = tk.StringVar()
        owdescText = owdesc
        self.owdescription = tk.Label(self.lwindow, text=owdescText, font=self.helv11, anchor = 'w')
        self.owdescription.config(width=50)
        self.owdescription.grid(row=2, column=1, columnspan=3, sticky='w')
        
        owmodelLabel = tk.Label(self.lwindow, text="Model:", font=self.helv11, anchor = 'w')
        owmodelLabel.config(width=20)
        owmodelLabel.grid(row=3, column=0, sticky='w')
        
        owmodeltext = tk.StringVar()
        owmodeltext = owmodel
        self.owmodel = tk.Label(self.lwindow, text=owmodeltext, font=self.helv11, anchor = 'w')
        self.owmodel.config(width=50)
        self.owmodel.grid(row=3, column=1, sticky='w')
        
        owiclicLabel = tk.Label(self.lwindow, text="InformaCast License:", font=self.helv11, anchor = 'w')
        owiclicLabel.config(width=20)
        owiclicLabel.grid(row=5, column=0, sticky='w')
        
        owiclictext = tk.StringVar()
        owiclictext = owicLic
        self.iclicense = tk.Label(self.lwindow, text=owiclictext, font=self.helv11, anchor = 'w')
        self.iclicense.config(width=25)
        self.iclicense.grid(row=5, column=1, sticky='w')
        
        owicEnabLabel = tk.Label(self.lwindow, text="InformaCast Enabled:", font=self.helv11, anchor = 'w')
        owicEnabLabel.config(width=20)
        #owicEnabLabel.grid(row=5, column=2, sticky='w')
        
        self.owicEnabtext = tk.StringVar()
        #self.owicEnabtext = owicEnab
        self.owicEnable = ttk.Combobox(self.lwindow, textvariable=self.owicEnabtext, font=self.helv11, state='readonly')
        self.owicEnable.config(width=13, state='disabled')
        self.owicEnable['values'] = ('N', 'Y')
        #self.owicEnable.grid(row=5, column=3, sticky='w')
        if owicEnab == "Y":
            owicEnabConv = 1
        else:
            owicEnabConv = 0
        self.owicEnable.current(owicEnabConv)
        
        owsynappsLicLabel = tk.Label(self.lwindow, text="Synapps License:", font=self.helv11, anchor = 'w')
        owsynappsLicLabel.config(width=20)
        owsynappsLicLabel.grid(row=6, column=0, sticky='w')
        
        self.owsynappsLictext = tk.StringVar()
        self.owsynappsLictext = owsynappsLic
        self.owsynappslicense = tk.Label(self.lwindow, text=self.owsynappsLictext, font=self.helv11, anchor = 'w')
        self.owsynappslicense.config(width=25)
        self.owsynappslicense.grid(row=6, column=1, sticky='w')
        
        owsynappsEnabLabel = tk.Label(self.lwindow, text="Synapps Enabled:", font=self.helv11, anchor = 'w')
        owsynappsEnabLabel.config(width=20)
        #owsynappsEnabLabel.grid(row=6, column=2, sticky='w')
        
        self.owsynappsEnabtext = tk.StringVar()
        #self.owsynappsEnabtext = owsynappsEnab
        self.owsynappsEnable = ttk.Combobox(self.lwindow, textvariable=self.owsynappsEnabtext, font=self.helv11, state='readonly')
        self.owsynappsEnable.config(width=13, state='disabled')
        self.owsynappsEnable['values'] = ('N', 'Y')
        #self.owsynappsEnable.grid(row=6, column=3, sticky='w')
        if owsynappsEnab == "Y":
            owsynappsEnabConv = 1
        else:
            owsynappsEnabConv = 0
        self.owsynappsEnable.current(owsynappsEnabConv)
        
        owpolycomLicLabel = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        owpolycomLicLabel.config(width=20)
        #owpolycomLicLabel.grid(row=7, column=0, sticky='w')
        
        owpolycomLictext = tk.StringVar()
        #owpolycomLictext = polycomLic
        self.owpolycomlicense = tk.Label(self.lwindow, text="Not Used", font=self.helv11, anchor = 'w')
        self.owpolycomlicense.config(width=25)
        #self.owpolycomlicense.grid(row=7, column=1, sticky='w')
        
        owpolycomEnabLabel = tk.Label(self.lwindow, text="PolyCom Enabled:", font=self.helv11, anchor = 'w')
        owpolycomEnabLabel.config(width=20)
        #owpolycomEnabLabel.grid(row=7, column=2, sticky='w')
        
        self.owpolycomEnabtext = tk.StringVar()
        #owpolycomEnabtext = owpolycomEnab
        self.owpolycomEnable = ttk.Combobox(self.lwindow, textvariable=self.owpolycomEnabtext, font=self.helv11, state='readonly')
        self.owpolycomEnable.config(width=13, state='disabled')
        self.owpolycomEnable['values'] = ('N', 'Y')
        #self.owpolycomEnable.grid(row=7, column=3, sticky='w')
        if owpolycomEnab == "Y":
            owpolycomEnabConv = 1
        else:
            owpolycomEnabConv = 0
        self.owpolycomEnable.current(owpolycomEnabConv)
        
        owdhcpLabel = tk.Label(self.lwindow, text="DHCP Enabled:", font=self.helv11, anchor = 'w')
        owdhcpLabel.config(width=20)
        owdhcpLabel.grid(row=8, column=0, sticky='w')
        
        self.owdhcpEnabtext = tk.StringVar()
        #owdhcpEnabtext = owdhcpEnab
        self.owdhcpEnable = ttk.Combobox(self.lwindow, textvariable=self.owdhcpEnabtext, font=self.helv11, state='readonly')
        self.owdhcpEnable.config(width=13, state='disabled')
        self.owdhcpEnable['values'] = ('N', 'Y')
        self.owdhcpEnable.grid(row=8, column=1, sticky='w')
        if owdhcpEnab == "Y":
            owdhcpEnabConv = 1
        else:
            owdhcpEnabConv = 0
        self.owdhcpEnable.current(owdhcpEnabConv)  
        
        owflasherspLabel = tk.Label(self.lwindow, text="Flasher Enabled:", font=self.helv11, anchor = 'w')
        owflasherspLabel.config(width=20)
        owflasherspLabel.grid(row=9, column=0, sticky='w')
        
        self.owflasherEnabtext = tk.StringVar()
        #owflasherEnabtext = owflasherEnab
        self.owflasherEnable = ttk.Combobox(self.lwindow, textvariable=self.owflasherEnabtext, font=self.helv11, state='readonly')
        self.owflasherEnable.config(width=13, state='disabled')
        self.owflasherEnable['values'] = ('N', 'Y')
        self.owflasherEnable.grid(row=9, column=1, sticky='w')
        if owflasherEnab == "Y":
            owflasherEnabConv = 1
        else:
            owflasherEnabConv = 0
        self.owflasherEnable.current(owflasherEnabConv) 
        
        owbfdevtypeLabel = tk.Label(self.lwindow, text="BF Device Type:", font=self.helv11, anchor = 'w')
        owbfdevtypeLabel.config(width=20)
        owbfdevtypeLabel.grid(row=10, column=0, sticky='w')

        owbfdevtypeText = tk.StringVar()
        owbfdevtypeText = self.owtransmitbfdevtype
        owbfdevtypeText = int(owbfdevtypeText)
        self.owbfdevtypeLbl = tk.Label(self.lwindow, text=owbfdevtypeText, font=self.helv11, anchor = 'w')
        self.owbfdevtypeLbl.config(width=25)
        self.owbfdevtypeLbl.grid(row=10, column=1, sticky='w') 
                
        owscanbfdevicetypeLabel = tk.Label(self.lwindow, text="Scan BF Device Type:", font=self.helv11, anchor = 'w')
        owscanbfdevicetypeLabel.config(width=20)
        owscanbfdevicetypeLabel.grid(row=11, column=0, sticky='w')

        self.owscanbfdevicetypeLbl = tk.Label(self.lwindow, text=scanbfdevicetype, font=self.helv11, anchor = 'w')
        self.owscanbfdevicetypeLbl.config(width=25)
        self.owscanbfdevicetypeLbl.grid(row=11, column=1, sticky='w') 
        
        owmodel = owproductdata.loc[productId, 'Model'] 
        owpathtoModels = str(initialPath) + '/Model/' + str(owmodel) + '/' + str(owmodel) + '.csv'
        
        owexists = os.path.isfile(owpathtoModels)
        if owexists:        
            owacceptDTdata = pd.read_csv(owpathtoModels, dtype={'APP Version':str, 'vstartup Version':str, 'VipRunStp Version':str}, nrows=1, header=None)
            owacceptDTdata = owacceptDTdata.fillna('')       
            owacceptedDTs = owacceptDTdata.iloc[0,:]
            owacceptedDT = []
            for owentry in owacceptedDTs:
                if type(owentry) is np.int64:
                    owacceptedDT.append(owentry)
                else:
                    pass
        else:
            tkMessageBox.showinfo('Model File Missing', 'Please verify the' + '"'+ str(owmodel) + '"' + ' File exists and try again.')  
            self.close_loadcwindow() 
            return 
            
        #if int(identifier) in owacceptedDT:
        #    pass
        #else:
        #    tkMessageBox.showinfo('Model/Product ID Conflict', 'Please verify that the boards you are loading support the "PRODUCT ID" entered') 
        #    self.close_loadcwindow() 
        #    return 
                            
        owpathtoModels = str(initialPath) + '/Model/' + str(owmodel) + '/' + str(owmodel) + '.csv'
        owfileLocdata = pd.read_csv(owpathtoModels,  dtype={'APP Version':str, 'vstartup Version':str, 'VipRunStp Version':str}, nrows=2, header=None)
        owfileLocdata = owfileLocdata.fillna('')       
        owfileLocdata = owfileLocdata.iloc[1,1]
                        
        owpathtoModels = str(initialPath) + '/Model/' + str(owmodel) + '/' + str(owmodel)  + '.csv'
        self.owfuncGrpdata = pd.read_csv(owpathtoModels,  dtype={'APP Version':str, 'vstartup Version':str, 'VipRunStp Version':str}, skiprows=4)
        self.owfuncGrpdata.set_index('Function Group')
        self.owfuncGrpdata = self.owfuncGrpdata.fillna('')
        self.owmainfuncGrp = str(self.owmainfuncGrp)
        self.owmainfuncGrp = self.owmainfuncGrp.strip()
        self.owfuncGrpdata = self.owfuncGrpdata.loc[self.owfuncGrpdata['Function Group'] == self.owmainfuncGrp]
        
        if self.owfuncGrpdata['Default Release'].str.contains('Y').any():
            pass
        elif self.owfuncGrpdata['Default Release'].str.contains('y').any():
            self.owfuncGrpdata['Default Release'] = self.owfuncGrpdata['Default Release'].str.upper()
        else:
            self.owfuncGrpdata.ix[0, 'Default Release'] = 'Y'
                   
        owdefRelaseReleases = self.owfuncGrpdata[['Default Release', 'Release Desc']]
        owdefRelaseReleases.columns = ['Default_Release', 'Release_Desc']
        owdefaultRelease = owdefRelaseReleases.loc[owdefRelaseReleases['Default_Release'] == 'Y']
        owdefaultRelease = owdefaultRelease.reset_index(drop=True)
            
        owdefaultRelease = owdefaultRelease.iloc[0,1]
        
        releasesLabel = tk.Label(self.lwindow, text="Releases:", font=self.helv11, anchor = 'w')
        releasesLabel.config(width=20)
        releasesLabel.grid(row=12, column=0, sticky='w')

        self.owdefRelaseRelease = owdefRelaseReleases[owdefRelaseReleases.Default_Release == "Y"]
        self.owdefRelaseRelease = self.owdefRelaseRelease['Release_Desc']        
        self.owdefreleases = owdefRelaseReleases['Release_Desc'].tolist()      
    
        self.owreleasestext = tk.StringVar()
        #owreleasestext = owdefRelaseReleases
        self.owreleases = ttk.Combobox(self.lwindow, textvariable=self.owreleasestext, font=self.helv11, state='readonly')
        self.owreleases.config(width=13, state='disable')
        self.owreleases['values'] = self.owdefreleases
        self.owreleases.grid(row=12, column=1, sticky='w')
        self.owreleases.bind('<<ComboboxSelected>>', self.owon_select)
        owdefaultReleaseIndex = self.owdefreleases.index(owdefaultRelease)
        self.owreleases.current(owdefaultReleaseIndex)
        
        owfilenameLabel = tk.Label(self.lwindow, text="File Name:", font=self.helv11, anchor = 'w')
        owfilenameLabel.config(width=15)
        owfilenameLabel.grid(row=13, column=0, sticky='w')
        
        self.owfileName = tk.StringVar()
        self.owfilenameactual = tk.Label(self.lwindow, text=self.owfileName, font=self.helv11, anchor = 'w')
        self.owfilenameactual.config(width=50)
        self.owfilenameactual.grid(row=13, column=1, sticky='w')
        
        owappversionLabel = tk.Label(self.lwindow, text="Appversion:", font=self.helv11, anchor = 'w')
        owappversionLabel.config(width=15)
        owappversionLabel.grid(row=14, column=0, sticky='w')
        
        self.owappversionactual = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        self.owappversionactual.config(width=25)
        self.owappversionactual.grid(row=14, column=1, sticky='w')
        
        owvipRunStpVersionLabel = tk.Label(self.lwindow, text="VipRunStp Version:", font=self.helv11, anchor = 'w')
        owvipRunStpVersionLabel.config(width=15)
        owvipRunStpVersionLabel.grid(row=15, column=0, sticky='w')
        
        self.owvipRunStpVersionactual = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        self.owvipRunStpVersionactual.config(width=25)
        self.owvipRunStpVersionactual.grid(row=15, column=1, sticky='w')
        
        owvstartupVersionLabel = tk.Label(self.lwindow, text="vstartup Version:", font=self.helv11, anchor = 'w')
        owvstartupVersionLabel.config(width=15)
        owvstartupVersionLabel.grid(row=16, column=0, sticky='w')
        
        self.owvstartupVersionactual = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        self.owvstartupVersionactual.config(width=25)
        self.owvstartupVersionactual.grid(row=16, column=1, sticky='w')
        
        owfirmwareLabel = tk.Label(self.lwindow, text="Firmware:", font=self.helv11, anchor = 'w')
        owfirmwareLabel.config(width=16)
        #owfirmwareLabel.grid(row=17, column=0, sticky='w')   
        
        self.owfirmwareactual = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        self.owfirmwareactual.config(width=15)
        #self.owfirmwareactual.grid(row=17, column=1, sticky='w')     
        
        owplatformLabel = tk.Label(self.lwindow, text="Platform:", font=self.helv11, anchor = 'w')
        owplatformLabel.config(width=17)
        #owplatformLabel.grid(row=18, column=0, sticky='w')   
        
        self.owplatformactual = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        self.owplatformactual.config(width=15)
        #self.owplatformactual.grid(row=18, column=1, sticky='w')
           
        self.deviationExplanation = ""

        ##################  Start BDT Data  #########################
        
        #inputs = int(owproductdata.loc[productId, 'bdtinputs'])
        owinputsLabel = tk.Label(self.lwindow, text="Inputs:", font=self.helv11, anchor = 'w')
        owinputsLabel.config(width=15)
        owinputsLabel.grid(row=19, column=0, sticky='w')   
        
        self.owinputsactual = tk.Label(self.lwindow, text=inputs, font=self.helv11, anchor = 'w')
        self.owinputsactual.config(width=15)
        self.owinputsactual.grid(row=19, column=1, sticky='w')
        
        #channels = int(owproductdata.loc[productId, 'bdtchannels'])
        owchannelsLabel = tk.Label(self.lwindow, text="Channels:", font=self.helv11, anchor = 'w')
        owchannelsLabel.config(width=15)
        owchannelsLabel.grid(row=20, column=0, sticky='w')   
        
        self.owchannelsactual = tk.Label(self.lwindow, text=channels, font=self.helv11, anchor = 'w')
        self.owchannelsactual.config(width=15)
        self.owchannelsactual.grid(row=20, column=1, sticky='w')
        
        #relays = int(owproductdata.loc[productId, 'bdtrelays'])
        owrelaysLabel = tk.Label(self.lwindow, text="Relays:", font=self.helv11, anchor = 'w')
        owrelaysLabel.config(width=15)
        owrelaysLabel.grid(row=21, column=0, sticky='w')   
        
        self.owrelaysactual = tk.Label(self.lwindow, text=relays, font=self.helv11, anchor = 'w')
        self.owrelaysactual.config(width=15)
        self.owrelaysactual.grid(row=21, column=1, sticky='w')
        
        #inputConfiguration = int(owproductdata.loc[productId, 'bdtinputConfiguration'])
        owinputConfigurationLabel = tk.Label(self.lwindow, text="Input Configuration:", font=self.helv11, anchor = 'w')
        owinputConfigurationLabel.config(width=15)
        owinputConfigurationLabel.grid(row=22, column=0, sticky='w')   
        
        self.owinputConfigurationactual = tk.Label(self.lwindow, text=inputConfiguration, font=self.helv11, anchor = 'w')
        self.owinputConfigurationactual.config(width=15)
        self.owinputConfigurationactual.grid(row=22, column=1, sticky='w')
        
        #bdtfirmware = str(owproductdata.loc[productId, 'bdtfirmware'])
        owbdtFirmwareLabel = tk.Label(self.lwindow, text="BDT Firmware:", font=self.helv11, anchor = 'w')
        owbdtFirmwareLabel.config(width=15)
        owbdtFirmwareLabel.grid(row=23, column=0, sticky='w')   
        
        self.owbdtFirmwareactual = tk.Label(self.lwindow, text=bdtfirmware, font=self.helv11, anchor = 'w')
        self.owbdtFirmwareactual.config(width=15)
        self.owbdtFirmwareactual.grid(row=23, column=1, sticky='w')
        
        #flashers = int(owproductdata.loc[productId, 'bdtflashers'])
        #flashers = str(flashers)
        owbdtflashersLabel = tk.Label(self.lwindow, text="BDT Flashers:", font=self.helv11, anchor = 'w')
        owbdtflashersLabel.config(width=15)
        owbdtflashersLabel.grid(row=24, column=0, sticky='w')   
        
        self.owbdtflashersactual = tk.Label(self.lwindow, text=flashers, font=self.helv11, anchor = 'w')
        self.owbdtflashersactual.config(width=15)
        self.owbdtflashersactual.grid(row=24, column=1, sticky='w')

        ##################  End BDT Data  #########################
        
        owscriptLabel = tk.Label(self.lwindow, text="Script Name:", font=self.helv11, anchor = 'w')
        owscriptLabel.config(width=15)
        owscriptLabel.grid(row=25, column=0, sticky='w')
        
        self.owscriptName = str(owproductdata.loc[productId, 'script'])
        #self.owscriptName = tk.StringVar()
        self.owscriptNameactual = tk.Label(self.lwindow, text=self.owscriptName, font=self.helv11, anchor = 'w')
        self.owscriptNameactual.config(width=50)
        self.owscriptNameactual.grid(row=25, column=1, sticky='w')
        
        owblankLabel31 = tk.Label(self.lwindow, text="", font=self.helv11, anchor = 'w')
        owblankLabel31.config(width=15)
        owblankLabel31.grid(row=28, column=0, sticky='w')  
                  
        owdetailsBtn =tk.Button(self.lwindow, text="Details", command=lambda msg=detailswindowsMSG:self.detailsWindow(msg), width=13)
        owdetailsBtn.grid(row=29, column=0, sticky='w')
        
        owbackBtn =tk.Button(self.lwindow, text="Back", command=self.close_loadcwindow, width=13)
        owbackBtn.grid(row=30, column=0, sticky='w')  

        owloadBtn =tk.Button(self.lwindow, text="Load Devices", command=self.load_devices, width=13)
        owloadBtn.configure(bg="#FF3333")
        owloadBtn.grid(row=30, column=3, sticky='e')
        self.owon_select()            
        self.lwindow.protocol("WM_DELETE_WINDOW",  on_close)
           
    def dwon_select(self, event=None):
        '''
        This function handles getting values from the Models File and setting the values in the
        Details Window based on retrieved values.
        '''              
        version = self.dwreleases.get()
        self.dwOSVersion = self.dwreleases.current()
        self.owfuncGrpdata
        dwdataset = self.owfuncGrpdata
        dwdataset = dwdataset[['Release Desc', 'File Name', 'APP Version', 'VipRunStp Version', 'vstartup Version', 'Firmware', 'Platform']]
        dwdatasetValues = dwdataset.loc[dwdataset['Release Desc'] == version]
        dwfilename = dwdatasetValues.loc[:, ['File Name']].values
        dwfilename = dwfilename[0][0]
        self.dwfilenameactual.config(text=dwfilename)
        self.dwfilename = dwfilename
        
        dwappversion = dwdatasetValues.loc[:, ['APP Version']].values
        dwappversion = dwappversion[0][0]
        self.dwappversionactual.config(text=dwappversion)
        self.dwappver = dwappversion
        
        dwVipRunStpVersion = dwdatasetValues.loc[:, ['VipRunStp Version']].values
        dwVipRunStpVersion = dwVipRunStpVersion[0][0]
        self.dwvipRunStpVersionactual.config(text= dwVipRunStpVersion)
        self.dwviprunstp = dwVipRunStpVersion
        
        dwvstartupVersion = dwdatasetValues.loc[:, ['vstartup Version']].values
        dwvstartupVersion = dwvstartupVersion[0][0]
        self.dwvstartupVersionactual.config(text=dwvstartupVersion)
        self.dwvstartup = dwvstartupVersion
        
        dwfirmware = dwdatasetValues.loc[:, ['Firmware']].values
        dwfirmware = dwfirmware[0][0]
        self.dwfirmwareactual.config(text=dwfirmware)
        
        dwplatform = dwdatasetValues.loc[:, ['Platform']].values
        dwplatform = dwplatform[0][0]
        self.dwplatformactual.config(text=dwplatform)  
         
    def setIClicense(self, msg):
        """
        This function alters the InformCast indicator on the deatials screen to indicate if the license is enabled
        when the Informacat Enabled dropped down is altered. 
        """ 
        if self.dwicEnable.get() == "Y":
            self.dwiclicense.cget('text')
            if self.dwiclicense['text'] != 'Y':
               self.dwiclicense['text'] = 'Y'
            else:
               pass
        elif self.dwicEnable.get() == "N":
            self.dwiclicense.cget('text')
            if self.dwiclicense['text'] != 'N':
               self.dwiclicense['text'] = 'N'
            else:
               pass
               
    def setsynappslicense(self, msg):
        """
        This function alters the InformCast indicator on the deatials screen to indicate if the license is enabled
        when the Informacat Enabled dropped down is altered. 
        """ 
        if self.dwsynappsEnable.get() == "Y":
            self.dwsynappslicense.cget('text')
            if self.dwsynappslicense['text'] != 'Y':
               self.dwsynappslicense['text'] = 'Y'
            else:
               pass
        elif self.dwsynappsEnable.get() == "N":
            self.dwsynappslicense.cget('text')
            if self.dwsynappslicense['text'] != 'N':
               self.dwsynappslicense['text'] = 'N'
            else:
               pass
             
    def detailsWindow(self, detailswindowsMSG):
        """
        This function creates the Details Window the user can either load the devices from the screen
        with the default confugrsations scanned in earlier or alter the confuguration as needed before
        loading the devices.
        """  
        dwmsg = detailswindowsMSG
        self.cwindow.withdraw()
        dwgroup = dwmsg['grpid']
        self.dwgroup = dwmsg['grpid']
        dwdeviceType = dwmsg['deviceType']
        dwnumMacs = dwmsg['numMacs'] 
        dwproductId = dwmsg['productId'] 
        dwdevsLoaded = 0
        dwproduct = None                
        
        dwproduct                  = self.owproductLbl['text']
        dwdesc                     = self.owdescription['text']
        dwmodel                    = self.owmodel['text']
        self.dwmodel               = self.owmodel['text']
        self.dwmainfuncGrp         = self.owmainfuncGrp
        dwicLic                    = self.iclicense['text']
        dwicEnab                   = self.owicEnable.get()
        dwsynappsLic               = self.owsynappslicense['text']
        dwsynappsEnab              = self.owsynappsEnable.get()
        dwpolycomLic               = self.owpolycomlicense['text']
        dwpolycomEnab              = self.owpolycomEnable.get()
        dwdhcpEnab                 = self.owdhcpEnable.get()
        dwflasherEnab              = self.owflasherEnable.get()
        self.dwbfdevtype           = self.owbfdevtypeLbl['text']
        self.scanbfdevicetype      = self.owscanbfdevicetypeLbl['text']
        dwReleaseIndex             = self.owreleases.current()
        dwinputsactual             = self.owinputsactual['text']
        dwchannelsactual           = self.owchannelsactual['text']
        dwrelaysactual             = self.owrelaysactual['text']
        dwinputConfigurationactual = self.owinputConfigurationactual['text']
        bdtfirmware                = self.owbdtFirmwareactual['text']
        flashers                   = self.owbdtflashersactual['text']
        sname                      = self.owscriptNameactual['text']
            
        self.detailswindow = tk.Toplevel(root)
        self.detailswindow.title("[" + str(dwgroup) + "]" + " " + dwdeviceType + " Detailed Product Load")
        lsizex = sizex
        lsizey = sizey
        self.detailswindow.wm_geometry("%dx%d+%d+%d" % (lsizex,lsizey,posx,posy)) 
        self.detailswindow.resizable(width=False, height=False) 
        self.detailswindow.update_idletasks()
        lw = self.detailswindow.winfo_screenwidth()
        lh = self.detailswindow.winfo_screenheight()
        lsize = tuple(int(_) for _ in self.detailswindow.geometry().split('+')[0].split('x'))
        lx = lw/2 - size[0]/2
        ly = lh/2 - size[1]/2 - 50
        self.detailswindow.geometry("%dx%d+%d+%d" % (lsize + (self.mainwinx, self.mainwiny))) 
        
        dwproductLabel = tk.Label(self.detailswindow, text="Product:", font=self.helv11, anchor = 'w')
        dwproductLabel.config(width=25)
        dwproductLabel.grid(row=1, column=0, sticky='w')
        
        self.dwproductText = tk.StringVar()
        self.dwproductText = dwproduct
        self.dwproductLbl = tk.Label(self.detailswindow, text=self.dwproductText, font=self.helv11, anchor = 'w')
        self.dwproductLbl.config(width=50)
        self.dwproductLbl.grid(row=1, column=1, sticky='w')
        
        dwdescLabel = tk.Label(self.detailswindow, text="Description:", font=self.helv11, anchor = 'w')
        dwdescLabel.config(width=25)
        dwdescLabel.grid(row=2, column=0, sticky='w')
        
        self.dwdescText = tk.StringVar()
        self.dwdescText = dwdesc
        self.dwdescription = tk.Label(self.detailswindow, text=self.dwdescText, font=self.helv11, anchor = 'w')
        self.dwdescription.config(width=50)
        self.dwdescription.grid(row=2, column=1, columnspan=3, sticky='w')
        
        dwmodelLabel = tk.Label(self.detailswindow, text="Model:", font=self.helv11, anchor = 'w')
        dwmodelLabel.config(width=25)
        dwmodelLabel.grid(row=3, column=0, sticky='w')
        
        self.dwmodeltext = tk.StringVar()
        self.dwmodeltext = dwmodel
        self.dwmodel = tk.Label(self.detailswindow, text=self.dwmodeltext, font=self.helv11, anchor = 'w')
        self.dwmodel.config(width=50)
        self.dwmodel.grid(row=3, column=1, sticky='w')
        
        dwfuncGrpLabel = tk.Label(self.detailswindow, text="Functional Group:", font=self.helv11, anchor = 'w')
        dwfuncGrpLabel.config(width=25)
        dwfuncGrpLabel.grid(row=4, column=0, sticky='w')
        
        self.dwfuncGrptext = tk.StringVar()
        self.dwfuncGrptext = self.dwmainfuncGrp
        self.dwfuncGrp = tk.Label(self.detailswindow, text=self.dwfuncGrptext, font=self.helv11, anchor = 'w')
        self.dwfuncGrp.config(width=50)
        self.dwfuncGrp.grid(row=4, column=1, sticky='w')
        
        dwiclicLabel = tk.Label(self.detailswindow, text="InformaCast License:", font=self.helv11, anchor = 'w')
        dwiclicLabel.config(width=25)
        dwiclicLabel.grid(row=5, column=0, sticky='w')
        
        self.dwiclictext = tk.StringVar()
        self.dwiclictext = dwicLic
        self.dwiclicense = tk.Label(self.detailswindow, text=self.dwiclictext, font=self.helv11, anchor = 'w')
        self.dwiclicense.config(width=50)
        self.dwiclicense.grid(row=5, column=1, sticky='w')
        
        dwicEnabLabel = tk.Label(self.detailswindow, text="InformaCast Enabled:", font=self.helv11, anchor = 'w')
        dwicEnabLabel.config(width=25)
        dwicEnabLabel.grid(row=5, column=2, sticky='w')
        
        self.dwicEnabtext = tk.StringVar()
        #self.dwicEnabtext = dwicEnab
        self.dwicEnable = ttk.Combobox(self.detailswindow, textvariable=self.dwicEnabtext, font=self.helv11)
        self.dwicEnable.config(width=5)
        self.dwicEnable['values'] = ('N', 'Y')
        self.dwicEnable.grid(row=5, column=3, sticky='w')
        if dwicEnab == "Y":
            icEnabConv = 1
        else:
            icEnabConv = 0
        self.dwicEnable.current(icEnabConv)        
        self.dwicEnable.bind('<<ComboboxSelected>>', self.setIClicense)
        
        dwsynappsLicLabel = tk.Label(self.detailswindow, text="Synapps License:", font=self.helv11, anchor = 'w')
        dwsynappsLicLabel.config(width=25)
        dwsynappsLicLabel.grid(row=6, column=0, sticky='w')
        
        self.dwsynappsLictext = tk.StringVar()
        self.dwsynappsLictext = dwsynappsLic
        self.dwsynappslicense = tk.Label(self.detailswindow, text=self.dwsynappsLictext, font=self.helv11, anchor = 'w')
        self.dwsynappslicense.config(width=20)
        self.dwsynappslicense.grid(row=6, column=1, sticky='w')
        
        dwsynappsEnabLabel = tk.Label(self.detailswindow, text="Synapps Enabled:", font=self.helv11, anchor = 'w')
        dwsynappsEnabLabel.config(width=20)
        dwsynappsEnabLabel.grid(row=6, column=2, sticky='w')
        
        self.dwsynappsEnabtext = tk.StringVar()
        self.dwsynappsEnabtext = dwsynappsEnab
        self.dwsynappsEnable = ttk.Combobox(self.detailswindow, textvariable=self.dwsynappsEnabtext, font=self.helv11)
        self.dwsynappsEnable.config(width=5)
        self.dwsynappsEnable['values'] = ('N', 'Y')
        self.dwsynappsEnable.grid(row=6, column=3, sticky='w')
        if dwsynappsEnab == "Y":
            synappsEnabConv = 1
        else:
            synappsEnabConv = 0
        self.dwsynappsEnable.current(synappsEnabConv)
        self.dwsynappsEnable.bind('<<ComboboxSelected>>', self.setsynappslicense)
        
        dwpolycomLicLabel = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        dwpolycomLicLabel.config(width=25)
        dwpolycomLicLabel.grid(row=7, column=0, sticky='w')
        
        self.dwpolycomLictext = tk.StringVar()
        self.dwpolycomLictext = dwpolycomLic
        self.dwpolycomlicense = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwpolycomlicense.config(width=20)
        self.dwpolycomlicense.grid(row=7, column=1, sticky='w')
        
        dwpolycomEnabLabel = tk.Label(self.detailswindow, text="PolyCom Enabled:", font=self.helv11, anchor = 'w')
        dwpolycomEnabLabel.config(width=25)
        dwpolycomEnabLabel.grid(row=7, column=2, sticky='w')
        
        self.dwpolycomEnabtext = tk.StringVar()
        #self.dwpolycomEnabtext = dwpolycomEnab
        self.dwpolycomEnable = ttk.Combobox(self.detailswindow, textvariable=self.dwpolycomEnabtext, font=self.helv11)
        self.dwpolycomEnable.config(width=5)
        self.dwpolycomEnable['values'] = ('N', 'Y')
        self.dwpolycomEnable.grid(row=7, column=3, sticky='w')
        if dwpolycomEnab == "Y":
            polycomEnabConv = 1
        else:
            polycomEnabConv = 0
        self.dwpolycomEnable.current(polycomEnabConv)
        
        dwdhcpLabel = tk.Label(self.detailswindow, text="DHCP Enabled:", font=self.helv11, anchor = 'w')
        dwdhcpLabel.config(width=25)
        dwdhcpLabel.grid(row=8, column=0, sticky='w')
        
        self.dwdhcpEnabtext = tk.StringVar()
        #self.dwdhcpEnabtext = dwdhcpEnab
        self.dwdhcpEnable = ttk.Combobox(self.detailswindow, textvariable=self.dwdhcpEnabtext, font=self.helv11)
        self.dwdhcpEnable.config(width=5)
        self.dwdhcpEnable['values'] = ('N', 'Y')
        self.dwdhcpEnable.grid(row=8, column=1, sticky='w')
        if dwdhcpEnab == "Y":
            dhcpEnabConv = 1
        else:
            dhcpEnabConv = 0
        self.dwdhcpEnable.current(dhcpEnabConv)  
        
        dwflasherspLabel = tk.Label(self.detailswindow, text="Flasher Enabled:", font=self.helv11, anchor = 'w')
        dwflasherspLabel.config(width=25)
        dwflasherspLabel.grid(row=9, column=0, sticky='w')
        
        self.dwflasherEnabtext = tk.StringVar()
        #self.dwflasherEnabtext = dwflasherEnab
        self.dwflasherEnable = ttk.Combobox(self.detailswindow, textvariable=self.dwflasherEnabtext, font=self.helv11)
        self.dwflasherEnable.config(width=5)
        self.dwflasherEnable['values'] = ('N', 'Y')
        self.dwflasherEnable.grid(row=9, column=1, sticky='w')
        if dwflasherEnab == "Y":
            flasherEnabConv = 1
        else:
            flasherEnabConv = 0
        self.dwflasherEnable.current(flasherEnabConv) 
        
        dwbfdevtypeLabel = tk.Label(self.detailswindow, text="BF Device Type:", font=self.helv11, anchor = 'w')
        dwbfdevtypeLabel.config(width=25)
        dwbfdevtypeLabel.grid(row=10, column=0, sticky='w')

        self.dwbfdevtypeText = tk.StringVar()
        self.dwbfdevtypeText = self.dwbfdevtype
        self.dwbfdevtypeLbl = tk.Label(self.detailswindow, text=self.dwbfdevtypeText, font=self.helv11, anchor = 'w')
        self.dwbfdevtypeLbl.config(width=15)
        self.dwbfdevtypeLbl.grid(row=10, column=1, sticky='w') 
        
        dwscanbfdevicetypeLabel = tk.Label(self.detailswindow, text="Scanned BF Device Type:", font=self.helv11, anchor = 'w')
        dwscanbfdevicetypeLabel.config(width=25)
        dwscanbfdevicetypeLabel.grid(row=10, column=2, sticky='w')

        scanbfdevicetype = tk.StringVar()
        scanbfdevicetype = self.scanbfdevicetype
        self.dwscanbfdevicetypeLbl = tk.Label(self.detailswindow, text=scanbfdevicetype, font=self.helv11, anchor = 'w')
        self.dwscanbfdevicetypeLbl.config(width=15)
        self.dwscanbfdevicetypeLbl.grid(row=10, column=3, sticky='w')

        dwscanbfdevicetypeLabel = tk.Label(self.detailswindow, text="Scan BF-Dev-Type Name:", font=self.helv11, anchor = 'w')
        dwscanbfdevicetypeLabel.config(width=25)
        dwscanbfdevicetypeLabel.grid(row=11, column=2, sticky='w')

        with open(initialPath + "/device_type_identifiers.txt") as scanneddeviceFile:
            for line in scanneddeviceFile:
                line = line.strip()
                identifier, productName = line.partition("=")[::2]
                if int(identifier) == int(scanbfdevicetype):
                    scanbfdevicetypeName = productName
                else:
                    pass        
        self.dwscanbfdevicetypeLbl = tk.Label(self.detailswindow, text=scanbfdevicetypeName, font=self.helv11, anchor = 'w')
        self.dwscanbfdevicetypeLbl.config(width=25)
        self.dwscanbfdevicetypeLbl.grid(row=11, column=3, sticky='w') 
                               
        dwpathtoModels = str(initialPath) + '/Model/' + str(dwmodel) + '/' + str(dwmodel) + '.csv'
        self.dwfuncGrpdata = pd.read_csv(dwpathtoModels, dtype={'APP Version':str, 'vstartup Version':str, 'VipRunStp Version':str}, skiprows=4)
        self.dwfuncGrpdata.set_index('Function Group')
        self.dwfuncGrpdata = self.dwfuncGrpdata.fillna('')
        
        self.dwfuncGrpdata = self.dwfuncGrpdata.loc[self.dwfuncGrpdata['Function Group'] == self.dwmainfuncGrp]  
        if self.dwfuncGrpdata['Default Release'].str.contains('Y').any():
            pass
        elif self.dwfuncGrpdata['Default Release'].str.contains('y').any():
            self.dwfuncGrpdata['Default Release'] = self.dwfuncGrpdata['Default Release'].str.upper()
        else:
            self.dwfuncGrpdata.ix[0, 'Default Release'] = 'Y'   
        
        self.dwfuncGrpdata = self.dwfuncGrpdata.fillna('')              
        dwdefRelaseReleases = self.dwfuncGrpdata[['Default Release', 'Release Desc']]
        dwdefRelaseReleases.columns = ['Default_Release', 'Release_Desc']
        dwdefaultRelease = dwdefRelaseReleases.loc[dwdefRelaseReleases['Default_Release'] == 'Y']
        dwdefaultRelease = dwdefaultRelease.reset_index(drop=True)    
        dwdefaultRelease = dwdefaultRelease.iloc[0,1]
        dwreleasesLabel = tk.Label(self.detailswindow, text="Releases:", font=self.helv11, anchor = 'w')
        dwreleasesLabel.config(width=20)
        dwreleasesLabel.grid(row=11, column=0, sticky='w')

        dwdefRelaseRelease = dwdefRelaseReleases[dwdefRelaseReleases.Default_Release == "Y"]
        dwdefRelaseRelease = dwdefRelaseRelease['Release_Desc']        
        dwdefreleases = dwdefRelaseReleases['Release_Desc'].tolist()       
        self.dwreleasestext = tk.StringVar()
        self.dwreleasestext = dwdefRelaseReleases
        self.dwreleases = ttk.Combobox(self.detailswindow, textvariable=self.dwreleasestext, font=self.helv11)
        self.dwreleases.config(width=40)
        self.dwreleases['values'] = dwdefreleases
        self.dwreleases.grid(row=11, column=1, sticky='w')
        self.dwreleases.bind('<<ComboboxSelected>>', self.dwon_select)
        dwdefaultReleaseIndex = dwdefreleases.index(dwdefaultRelease)
        self.dwreleases.current(dwReleaseIndex)
        
        dwdiviationReasonLabel = tk.Label(self.detailswindow, text="Deviation Explanation:", font=self.helv11, anchor = 'w')
        dwdiviationReasonLabel.config(width=20)
        dwdiviationReasonLabel.grid(row=12, column=2, sticky='w')
        
        self.dwdiviationReason = tk.Text(self.detailswindow, height=6, width=35, font=self.helv11)
        self.dwdiviationReason.config(bg='white')
        self.dwdiviationReason.grid(row=13, rowspan=4, column=2, columnspan=3, sticky='w')
        
        dwfilenameLabel = tk.Label(self.detailswindow, text="File Name:", font=self.helv11, anchor = 'w')
        dwfilenameLabel.config(width=25)
        dwfilenameLabel.grid(row=12, column=0, sticky='w')
        
        self.dwfileName = tk.StringVar()
        self.dwfilenameactual = tk.Label(self.detailswindow, text=self.dwfileName, font=self.helv11, anchor = 'w')
        self.dwfilenameactual.config(width=45)
        self.dwfilenameactual.grid(row=12, column=1, columnspan=3, sticky='w')
        
        dwappversionLabel = tk.Label(self.detailswindow, text="Appversion:", font=self.helv11, anchor = 'w')
        dwappversionLabel.config(width=20)
        dwappversionLabel.grid(row=13, column=0, sticky='w')
        
        self.dwappversionactual = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwappversionactual.config(width=20)
        self.dwappversionactual.grid(row=13, column=1, sticky='w')
        
        dwvipRunStpVersionLabel = tk.Label(self.detailswindow, text="VipRunStp Version:", font=self.helv11, anchor = 'w')
        dwvipRunStpVersionLabel.config(width=20)
        dwvipRunStpVersionLabel.grid(row=14, column=0, sticky='w')
        
        self.dwvipRunStpVersionactual = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwvipRunStpVersionactual.config(width=20)
        self.dwvipRunStpVersionactual.grid(row=14, column=1, sticky='w')
        
        dwvstartupVersionLabel = tk.Label(self.detailswindow, text="vstartup Version:", font=self.helv11, anchor = 'w')
        dwvstartupVersionLabel.config(width=20)
        dwvstartupVersionLabel.grid(row=15, column=0, sticky='w')
        
        self.dwvstartupVersionactual = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwvstartupVersionactual.config(width=20)
        self.dwvstartupVersionactual.grid(row=15, column=1, sticky='w')
        
        dwfirmwareLabel = tk.Label(self.detailswindow, text="Firmware:", font=self.helv11, anchor = 'w')
        dwfirmwareLabel.config(width=20)
        dwfirmwareLabel.grid(row=16, column=0, sticky='w')   
        
        self.dwfirmwareactual = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwfirmwareactual.config(width=20)
        self.dwfirmwareactual.grid(row=16, column=1, sticky='w')     
        
        dwplatformLabel = tk.Label(self.detailswindow, text="Platform:", font=self.helv11, anchor = 'w')
        dwplatformLabel.config(width=20)
        dwplatformLabel.grid(row=17, column=0, sticky='w')   
        
        self.dwplatformactual = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        self.dwplatformactual.config(width=20)
        self.dwplatformactual.grid(row=17, column=1, sticky='w')
        
        ###################
        dwinputsLabel = tk.Label(self.detailswindow, text="Inputs:", font=self.helv11, anchor = 'w')
        dwinputsLabel.config(width=15)
        dwinputsLabel.grid(row=18, column=0, sticky='w')   
        
        self.dwinputsactual = tk.Label(self.detailswindow, text=dwinputsactual, font=self.helv11, anchor = 'w')
        self.dwinputsactual.config(width=15)
        self.dwinputsactual.grid(row=18, column=1, sticky='w')

        dwchannelsLabel = tk.Label(self.detailswindow, text="Channels:", font=self.helv11, anchor = 'w')
        dwchannelsLabel.config(width=15)
        dwchannelsLabel.grid(row=19, column=0, sticky='w')   
        
        self.dwchannelsactual = tk.Label(self.detailswindow, text=dwchannelsactual, font=self.helv11, anchor = 'w')
        self.dwchannelsactual.config(width=15)
        self.dwchannelsactual.grid(row=19, column=1, sticky='w')

        dwrelaysLabel = tk.Label(self.detailswindow, text="Relays:", font=self.helv11, anchor = 'w')
        dwrelaysLabel.config(width=15)
        dwrelaysLabel.grid(row=20, column=0, sticky='w')   
        
        self.dwrelaysactual = tk.Label(self.detailswindow, text=dwrelaysactual, font=self.helv11, anchor = 'w')
        self.dwrelaysactual.config(width=15)
        self.dwrelaysactual.grid(row=20, column=1, sticky='w')

        dwdwinputConfigurationLabel = tk.Label(self.detailswindow, text="Input Configuration:", font=self.helv11, anchor = 'w')
        dwdwinputConfigurationLabel.config(width=15)
        dwdwinputConfigurationLabel.grid(row=21, column=0, sticky='w')   
        
        self.dwrelaysactual = tk.Label(self.detailswindow, text=dwinputConfigurationactual, font=self.helv11, anchor = 'w')
        self.dwrelaysactual.config(width=15)
        self.dwrelaysactual.grid(row=21, column=1, sticky='w')
        
        dwbdtFirmwareLabel = tk.Label(self.detailswindow, text="BDT Firmware:", font=self.helv11, anchor = 'w')
        dwbdtFirmwareLabel.config(width=15)
        dwbdtFirmwareLabel.grid(row=22, column=0, sticky='w')   
        
        self.dwbdtFirmwareactual = tk.Label(self.detailswindow, text=bdtfirmware, font=self.helv11, anchor = 'w')
        self.dwbdtFirmwareactual.config(width=15)
        self.dwbdtFirmwareactual.grid(row=22, column=1, sticky='w')
        
        dwbdtslasherseLabel = tk.Label(self.detailswindow, text="BDT Flashers:", font=self.helv11, anchor = 'w')
        dwbdtslasherseLabel.config(width=15)
        dwbdtslasherseLabel.grid(row=23, column=0, sticky='w')   
        
        self.dwbdtbdtslashersactual = tk.Label(self.detailswindow, text=flashers, font=self.helv11, anchor = 'w')
        self.dwbdtbdtslashersactual.config(width=15)
        self.dwbdtbdtslashersactual.grid(row=23, column=1, sticky='w')
        
        ###################
        
        dwscriptLabel = tk.Label(self.detailswindow, text="Script Name:", font=self.helv11, anchor = 'w')
        dwscriptLabel.config(width=15)
        dwscriptLabel.grid(row=24, column=0, sticky='w')
                
        dwscriptname = tk.StringVar(value=sname)
        self.dwscriptEntry = tk.Entry(self.detailswindow, width=30, textvariable=dwscriptname, font=self.helv11)
        self.dwscriptEntry.config(width=45, bg='white')
        self.dwscriptEntry.grid(row=24, column=1, columnspan=3, sticky='w')
                
        dwblankLabel31 = tk.Label(self.detailswindow, text="", font=self.helv11, anchor = 'w')
        dwblankLabel31.config(width=20)
        dwblankLabel31.grid(row=27, column=0, sticky='w')  

        self.dwon_select()    
        cancelBtn =tk.Button(self.detailswindow, text="Cancel", command=self.cancel_advacecwindow, width=15)
        cancelBtn.grid(row=28, column=1, sticky='w')    
        applyBtn =tk.Button(self.detailswindow, text="Apply", command=self.set_optionswindow, width=15)
        applyBtn.grid(row=28, column=2, sticky='w')   

    def set_optionswindow(self, event=None):  
        '''
        This function handles getting values form the Details Window and setting the values in the
        Options Window based on retrieved values.
        '''                  
        self.updatedProduct           = self.dwproductLbl['text']
        self.updatedDescription       = self.dwdescription['text']
        self.updatedModel             = self.dwmodel['text']
        self.updatedFunctionalGroup   = self.dwfuncGrp['text'] 
        self.updatedICLicense         = self.dwiclicense['text']
        self.updatedSynappsLicense    = self.dwsynappslicense['text']               
        self.owsynappslicense.config(text=self.updatedSynappsLicense)
        self.iclicense.config(text=self.updatedICLicense)  
        
        self.updatedICEnabled         = self.dwicEnable.get()
        if self.updatedICEnabled == "Y":
            self.updatedICEnabled = 1
        else:
            self.updatedICEnabled = 0
            
        self.updatedSynappsEnabled    = self.dwsynappsEnable.get()
        if self.updatedSynappsEnabled == "Y":
            self.updatedSynappsEnabled = 1
        else:
            self.updatedSynappsEnabled = 0
            
        self.updatedPolyComEnabled    = self.dwpolycomEnable.get()
        if self.updatedPolyComEnabled == "Y":
            self.updatedPolyComEnabled = 1
        else:
            self.updatedPolyComEnabled = 0
            
        self.updatedDHCPEnabled       = self.dwdhcpEnable.get()
        if self.updatedDHCPEnabled == "Y":
            self.updatedDHCPEnabled = 1
        else:
            self.updatedDHCPEnabled = 0
            
        self.updatedFlasherEnabled    = self.dwflasherEnable.get()
        if self.updatedFlasherEnabled == "Y":
            self.updatedFlasherEnabled = 1
        else:
            self.updatedFlasherEnabled = 0
            
        self.updatedBFDeviceType      = self.dwbfdevtypeLbl['text'] 
        self.updatedReleaseSelection  = self.dwreleases.current()
        self.updatedFilename          = self.dwfilenameactual['text'] 
        self.updatedAPPVersion        = self.dwappversionactual['text']
        self.updatedVipRunStpVersion  = self.dwvipRunStpVersionactual['text']
        self.updatedvstartupVersion   = self.dwvstartupVersionactual['text']
        self.updatedfirmwareVersion   = self.dwfirmwareactual['text'] 
        self.updatedPlatformVersion   = self.dwplatformactual['text']
        self.updatescriptname         = self.dwscriptEntry.get()
        self.deviationExplanation     = self.dwdiviationReason.get(1.0, "end-1c")      
        self.deviationExplanation     = self.deviationExplanation.strip()
        self.owicEnable.current(self.updatedICEnabled)         
        self.owsynappsEnable.current(self.updatedSynappsEnabled)            
        self.owpolycomEnable.current(self.updatedPolyComEnabled)            
        self.owdhcpEnable.current(self.updatedDHCPEnabled)               
        self.owflasherEnable.current(self.updatedFlasherEnabled)            
        self.owreleases.current(self.updatedReleaseSelection) 
           
        self.owfilenameactual.config(text=self.updatedFilename)         
        self.owappversionactual.config(text=self.updatedAPPVersion)            
        self.owvipRunStpVersionactual.config(text=self.updatedVipRunStpVersion)            
        self.owvstartupVersionactual.config(text=self.updatedvstartupVersion)               
        self.owfirmwareactual.config(text=self.updatedfirmwareVersion)            
        self.owplatformactual.config(text=self.updatedPlatformVersion) 
        self.owscriptNameactual.config(text=self.updatescriptname) 
                
        if self.deviationExplanation == "":
            tkMessageBox.showinfo("Missing Deviation Explanation", "Please enter the reason for this deviation.") 
            self.dwdiviationReason.focus_force()
        else:
            self.owon_select()  
            self.cancel_advacecwindow() 
            
    def startLoad(self, msg):
        """
        This function allows the user to load the devices directly from the product scan screen disregarding
        the options and details screens.
        """  
        grpid      = msg['grpid']
        y          = grpid
        deviceType = msg['deviceType']
        numMacs    = msg['numMacs']
        self.btns[y][3].configure(state = "disable")
        
        productId = tk.StringVar()   
        productId = self.configEntry.get()
        productId = productId.upper()
        products  = []
        workorder = tk.StringVar()   
        workorder = self.woEntry.get()
        workorder = workorder.upper()
        if workorder in self.workorders:
            pass
        else:
            self.workorders[grpid] = workorder        
        if len(self.configEntry.get()) == 0:
            tkMessageBox.showinfo("No Input", "Please scan or type a Product ID")
            self.configEntry.focus_force()
        else:            
            exists = os.path.isfile(initialPath + "/FirmWare.csv")
            if exists:
                with open(initialPath + "/FirmWare.csv") as productFile:
                    exists = os.path.isfile(initialPath + "/FirmWare.csv")
            if exists:
                with open(initialPath + "/FirmWare.csv") as productFile:
                    productLine = pd.read_csv(productFile)
                    productLine.set_index('Product', inplace=True)
                    products =  productLine.index.values    
                if productId not in products:
                    tkMessageBox.showinfo("Unknown Product ID", "Please scan or type a valid Product ID")
                    self.configEntry.focus_force() 
                else:                   
                    startloadData = pd.read_csv(initialPath + '/FirmWare.csv')
                    if startloadData['Product'].duplicated().any():
                        #tkMessageBox.showinfo('Product Duplication Found', 'Duplicated Products Found. Fix Duplicates and restart program. Closing program. ')
                        #msg = {"name":"Exit", "data":""}
                        #self.main.que.sendTo(msg)  
                        #sys.exit() 
                        pass
                    else:
                        pass
                    startloadData.set_index("Product", inplace=True)
                    startloadData.head()
                    startloadData = startloadData.replace(np.nan, '', regex=True)
                    slproducts = startloadData.index.get_values()
                    if productId in slproducts:
                        slproduct  = productId
                        sldesc = startloadData.loc[productId, 'Description']
                        slmodel = startloadData.loc[productId, 'Model']
                        self.slmodel = startloadData.loc[productId, 'Model']
                        self.slmainfuncGrp = startloadData.loc[productId, 'Functional Group']
                        if self.slmainfuncGrp == '':
                            tkMessageBox.showinfo('File Integrity Issue', 'Please check for a Functional Group Indicator in the "FirmWare" file.') 
                            return 
                        else:
                            pass
                        slicLic = startloadData.loc[productId, 'IC License']
                        slicLic = str(slicLic).upper()
                        slicEnab = startloadData.loc[productId, 'IC Enable']
                        slicEnab = str(slicEnab).upper()
                        slsynappsLic = startloadData.loc[productId, 'SynApps License']
                        slsynappsLic = str(slsynappsLic).upper()
                        slsynappsEnab = startloadData.loc[productId, 'SynApps Enable']
                        slsynappsEnab = str(slsynappsEnab).upper()
                        #polycomLic = productdata.loc[productId, 'Polycom  License']
                        polycomLic = "Not Used"
                        #icEnab = icEnab.upper()
                        slpolycomEnab = startloadData.loc[productId, 'PolyCom Enable']
                        slpolycomEnab = str(slpolycomEnab).upper()
                        sldhcpEnab = startloadData.loc[productId, 'DHCP']
                        sldhcpEnab = str(sldhcpEnab).upper()
                        slflasherEnab = startloadData.loc[productId, 'Flasher']
                        slflasherEnab = str(slflasherEnab).upper()
                        self.slbfdevtype = startloadData.loc[productId, 'bf-device-type']
                        scriptname = startloadData.loc[productId, 'script']  

                        if self.slbfdevtype == '':
                            tkMessageBox.showinfo('File Integrity Issue', 'Please check for a bf-dev-type in the "FirmWare" file.') 
                            return 
                        else:
                            pass                        
                        scanbfdevicetype = int(startloadData.loc[productId, 'scan_bf-device-type'])
                        inputs = startloadData.loc[productId, 'bdtinputs']
                        if inputs == '':
                            inputs = ''
                        else:
                            inputs = int(startloadData.loc[productId, 'bdtinputs'])
                            inputs = str(inputs)
                        channels = startloadData.loc[productId, 'bdtchannels']
                        if channels == '':
                            channels = ''
                        else:
                            channels = int(startloadData.loc[productId, 'bdtchannels'])
                            channels = str(channels)
                        relays = startloadData.loc[productId, 'bdtrelays']
                        if relays == '':
                            relays = ''
                        else:
                            relays = int(startloadData.loc[productId, 'bdtrelays'])
                            relays = str(relays)
                        inputConfiguration = startloadData.loc[productId, 'bdtinputConfiguration']
                        if inputConfiguration == '':
                            inputConfiguration = ''
                        else:
                            inputConfiguration = int(startloadData.loc[productId, 'bdtinputConfiguration'])
                            inputConfiguration = str(inputConfiguration)  
                        flashers = startloadData.loc[productId, 'bdtflashers']
                        if flashers == '':
                            flashers = ''
                        elif type(flashers) == str:
                            tkMessageBox.showinfo('File Integrity Issue', 'Please verify "Inputs" in FirmWare file is an Integer.') 
                            self.close_configwindow(y) 
                            return                            
                        else:
                            flashers = int(startloadData.loc[productId, 'bdtflashers'])
                            flashers = str(flashers)                      
                        bdtfirmware = str(startloadData.loc[productId, 'bdtfirmware'])
                        bdtfirmware = str(bdtfirmware)                        
                                        
                    with open(initialPath + "/device_type_identifiers.txt") as sldeviceFile:
                        for line in sldeviceFile:
                            line = line.strip()
                            identifier, productName = line.partition("=")[::2]
                            if int(identifier) == int(self.slbfdevtype):
                                self.slbfdevtype = productName
                                break
                            else:
                                pass      
                    slmodel = startloadData.loc[productId, 'Model'] 
                    slpathtoModels = str(initialPath) + '/Model/' + str(slmodel) + '/' + str(slmodel) + '.csv'
                    
                    slexists = os.path.isfile(slpathtoModels)
                    if slexists:        
                        slacceptDTdata = pd.read_csv(slpathtoModels, nrows=1, header=None)
                        slacceptDTdata = slacceptDTdata.fillna('')       
                        slacceptedDTs = slacceptDTdata.iloc[0,:]
                        slacceptedDT = []
                        for slentry in slacceptedDTs:
                            if type(slentry) is np.int64:
                                slacceptedDT.append(slentry)
                            else:
                                pass
                    else:
                        tkMessageBox.showinfo('Model File Missing', 'Please verify the' + '"'+ str(slmodel) + '"' + ' File exists and try again.')  
                        self.close_loadcwindow() 
                        return 
                    if scanbfdevicetype in slacceptedDT:
                        pass
                    else:
                        tkMessageBox.showinfo('Model/Product ID Conflict', 'Please verify the boards you are loading support the "PRODUCT ID"') 
                        return 
                    scanbfdevicetype = str(scanbfdevicetype)             
                    slpathtoModels = str(initialPath) + '/Model/' + str(slmodel) + '/' + str(slmodel) + '.csv'
                    slfileLocdata = pd.read_csv(slpathtoModels, nrows=2, header=None)
                    slfileLocdata = slfileLocdata.fillna('')       
                    slfileLocdata = slfileLocdata.iloc[1,1]
                                    
                    slpathtoModels = str(initialPath) + '/Model/' + str(slmodel) + '/' + str(slmodel)  + '.csv'
                    self.slfuncGrpdata = pd.read_csv(slpathtoModels, dtype={'APP Version':str, 'vstartup Version':str, 'VipRunStp Version':str}, skiprows=4)
                    self.slfuncGrpdata.set_index('Function Group')
                    self.slfuncGrpdata = self.slfuncGrpdata.fillna('')
                    funcGroups = self.slfuncGrpdata['Function Group'].tolist()
                    if funcGroups == '':
                        tkMessageBox.showinfo('File Integrity Issue', 'Please verify that there are Function Group(s) present in Model Specific File') 
                        return 
                    elif self.slmainfuncGrp not in funcGroups:
                        tkMessageBox.showinfo('File Integrity Issue', 'Please verify the Function Group is in the Model Specific File.') 
                        return 
                    else:
                        pass
                    self.slmainfuncGrp = str(self.slmainfuncGrp)
                    self.slmainfuncGrp = self.slmainfuncGrp.strip()
                    self.slfuncGrpdata = self.slfuncGrpdata.loc[self.slfuncGrpdata['Function Group'] == self.slmainfuncGrp]
                    if self.slfuncGrpdata['Default Release'].str.contains('Y').any():
                        pass
                    elif self.slfuncGrpdata['Default Release'].str.contains('y').any():
                        self.slfuncGrpdata['Default Release'] = self.slfuncGrpdata['Default Release'].str.upper()
                    else:
                        self.slfuncGrpdata.ix[0, 'Default Release'] = 'Y'
                                                   
                    sldefRelaseReleases = self.slfuncGrpdata[['Default Release', 'Release Desc']]
                    sldefRelaseReleases.columns = ['Default_Release', 'Release_Desc']
                    sldefaultRelease = sldefRelaseReleases.loc[sldefRelaseReleases['Default_Release'] == 'Y']
                    sldefaultRelease = sldefaultRelease.reset_index(drop=True)                        
                    sldefaultRelease = sldefaultRelease.iloc[0,1]                    
                    self.sldefRelaseRelease = sldefRelaseReleases[sldefRelaseReleases.Default_Release == "Y"]
                    self.sldefRelaseRelease = self.sldefRelaseRelease['Release_Desc']        
                    self.sldefreleases = sldefRelaseReleases['Release_Desc'].tolist()
                    
                    index = self.slfuncGrpdata.loc[self.slfuncGrpdata['Default Release']=='Y'].index[0]
                    self.slfuncGrpdata = self.slfuncGrpdata.loc[self.slfuncGrpdata['Default Release'] == 'Y']
                    
                    model      = slmodel
                    group      = grpid
                    vapp       = self.slfuncGrpdata.loc[index,'APP Version']
                    if vapp == '':
                        tkMessageBox.showinfo('Missing File Component', 'Please verify that the "Application Version" is present in the "' 
                        + str(slmodel) + '" File exits and try again.') 
                        return 
                    else:
                        pass
                    vstartup   = self.slfuncGrpdata.loc[index,'vstartup Version']
                    viprunstp  = self.slfuncGrpdata.loc[index,'VipRunStp Version']
                    slfilename = self.slfuncGrpdata.loc[index,'File Name']
                    if slfilename == '':
                            tkMessageBox.showinfo('File Integrity Issue', 'Please check for a "File Name" in the "FirmWare" file.') 
                            return 
                    else:
                        pass
                    if self.win == 1:
                        tarpath = initialPath + '\\Model\\' + model + '\\' + slfilename
                    elif self.win == 0:
                        tarpath = str(initialPath) + '/Model/' + model + '/' + slfilename
                    else:
                        print "Verify Operating System is supported by the program"                    
                    exists = os.path.isfile(tarpath)
                    if exists:
                        pass
                    else:
                        tkMessageBox.showinfo('Tar File Missing', 'Please verify that the "' + slfilename + '" File exits and try again.') 
                        return                            
                    devType  = int(startloadData.loc[productId, 'bf-device-type'])
                    
                    IC_L     = slicLic
                    if IC_L == 'Y':
                        IC_L = True
                    else:
                        IC_L = False
                    IC_E     = slicEnab
                    if IC_E == 'Y':
                        IC_E = True
                    else:
                        IC_E = False 
                    SYN_L    = slsynappsLic
                    if SYN_L == 'Y':
                        SYN_L = True
                    else:
                        SYN_L = False
                    SYN_E    = slsynappsEnab
                    if SYN_E == 'Y':
                        SYN_E = True
                    else:
                        SYN_E = False
                    POL_E    = slpolycomEnab
                    if POL_E == 'Y':
                        POL_E = True
                    else:
                        POL_E = False
                    DHCP     = sldhcpEnab
                    if DHCP == 'Y':
                        DHCP = True
                    else:
                        DHCP = False           
                    FLSH     = slflasherEnab
                    if FLSH == 'Y':
                        FLSH = True
                    else:
                        FLSH = False           
                    firmware   = self.slfuncGrpdata.loc[index, 'Firmware']
                    platForm   = self.slfuncGrpdata.loc[index, 'Platform']                                    
                    deviationReason = "" 
                                                    
                    data = {"grpid":group, "vapp": str(vapp), "vstartup":str(vstartup), "viprunstp":str(viprunstp), "path":tarpath,
                            "model":model, "device-type":str(devType), "scan-device-type":scanbfdevicetype, "IC_L":IC_L , 
                            "SYN_L":SYN_L, "IC_E":IC_E , "SYN_E":SYN_E, "POL_E":POL_E, "DHCP":DHCP, "flashers":flashers, 
                            "firmware":firmware, "product":productId, "inputs":inputs, "channels":channels, "relays":relays, 
                            "inputConfiguration": inputConfiguration, "bdtfirmware":bdtfirmware, "script":scriptname, "platform":platForm}     
                    msg2 = {"name":"Load", "data":data}  
                    self.resps["getGroupStatusResp"] = self.statusReply
                    self.main.que.sendTo(msg2)
                    print "msg2 = ", msg2
                    self.close_configwindow(y)

                    with open(initialPath + "/device_type_identifiers.txt") as scanneddeviceFile:
                        for line in scanneddeviceFile:
                            line = line.strip()
                            identifier, productName = line.partition("=")[::2]
                            if int(identifier) == int(scanbfdevicetype):
                                scanbfdevicename = productName
                            else:
                                pass
                    
                    savetodb = {
                     "productId":productId,
                     "desc":sldesc,
                     "model":model,
                     "mainfuncGrp":self.slmainfuncGrp,
                     "icLic":IC_L,
                     "icEnab":IC_E,
                     "synappsLic":SYN_L,
                     "synappsEnab":SYN_E,
                     "polycomLic":polycomLic,
                     "polycomEnab":POL_E,
                     "dhcpEnab":DHCP,
                     "flasherEnab":FLSH,
                     "bfdevtype":devType,
                     "scanbfdevicetype": scanbfdevicetype,
                     "scanbfdevicename": scanbfdevicename,
                     "release":sldefaultRelease,
                     "fileName":slfilename,
                     "appversion":str(vapp),
                     "viprunstpver":str(viprunstp),
                     "vstartupver":str(vstartup),
                     "firmware":firmware,
                     "platform":platForm,
                     #"shopordernum":,
                     "deviationReason":deviationReason,
                     "inputs":str(inputs),
                     "channels":str(channels),
                     "relays":str(relays),
                     "inputConfiguration": str(inputConfiguration),
                     "bdtfirmware":str(bdtfirmware),
                     "bdtflashers":str(flashers),
                     "script":str(scriptname)
                    } 
                    if group in self.tosavetoDB:
                        pass
                    else:
                        self.tosavetoDB[group] = savetodb 
                    self.remaininggroups.remove(group)   
                    
                    for group in self.remaininggroups:
                        self.btns[group][3].configure(state = "disable")
                                             
            else:
                tkMessageBox.showinfo('FirmWare File Missing', 'Please verify that the ' + '"' + 'FirmWare.csv' + '"' + ' file exists and try again.')
                self.configEntry.focus_force()  
            
                                                        
    def load_devices(self):
        '''
        This function is the actual function that captures the data from the optionsWindow screen and then
        sends the data along with the load command to load the devices with the configuration load.
        '''
        productId = self.owproductLbl['text']
        model = self.owmodel['text']
        group = self.group
        vapp = self.owappversionactual['text']
        vstartup = self.owvstartupVersionactual['text']
        viprunstp = self.owvipRunStpVersionactual['text']
        if self.win == 1:
            tarpath = initialPath + '\\Model\\' + model + '\\' + self.owfilename
        elif self.win == 0:
            tarpath = str(initialPath) + '/Model/' + model + '/' + self.owfilename
        else:
            print "Verify Operating System is supported by the program"        
        exists = os.path.isfile(tarpath)
        if exists:
            pass
        else:
            tkMessageBox.showinfo('Tar File Missing', 'Please verify that the "' + self.owfilename + '" File exits and try again.') 
            return    
        scanbfdevicetype = self.owscanbfdevicetypeLbl['text'] 
        IC_L     = self.iclicense['text']
        if IC_L == 'Y':
            IC_L = True
        else:
            IC_L = False
        IC_E     = self.owicEnable.get()
        if IC_E == 'Y':
            IC_E = True
        else:
            IC_E = False 
        SYN_L    = self.owsynappslicense['text']
        if SYN_L == 'Y':
            SYN_L = True
        else:
            SYN_L = False
        SYN_E    = self.owsynappsEnable.get()
        if SYN_E == 'Y':
            SYN_E = True
        else:
            SYN_E = False
        POL_E    = self.owpolycomEnable.get()
        if POL_E == 'Y':
            POL_E = True
        else:
            POL_E = False
        polycomLic = "Not Used"
        DHCP     = self.owdhcpEnable.get()
        if DHCP == 'Y':
            DHCP = True
        else:
            DHCP = False           
        FLSH     = self.owflasherEnable.get()
        if FLSH == 'Y':
            FLSH = True
        else:
            FLSH = False           
        firmware = self.owfirmwareactual['text']
        platForm = self.owplatformactual['text']
        
        inputs             = str(self.owinputsactual['text'])
        channels           = str(self.owchannelsactual['text'])
        relays             = str(self.owrelaysactual['text'])
        inputConfiguration = str(self.owinputConfigurationactual['text'])
        bdtfirmware        = str(self.owbdtFirmwareactual['text'])
        flashers           = self.owbdtflashersactual['text']   
        devType            = self.owbfdevtypeLbl['text']    
        devType            = int(devType)  
        scriptname         = self.owscriptNameactual['text'] 
        data = {"grpid":group, "vapp": str(vapp), "vstartup":str(vstartup), "viprunstp":str(viprunstp), "path":tarpath,
                "model":model, "device-type":str(devType), "scan-device-type":scanbfdevicetype, "IC_L":IC_L , "SYN_L":SYN_L, 
                "IC_E":IC_E , "SYN_E":SYN_E, "POL_E":POL_E, "DHCP":DHCP, "flashers":flashers, "firmware":firmware, "product":productId, 
                "inputs":inputs, "channels":channels, "relays":relays, "inputConfiguration": inputConfiguration, "bdtfirmware":bdtfirmware,
                "script":scriptname, "platform":platForm}       
        msg2 = {"name":"Load", "data":data}  
        self.resps["getGroupStatusResp"] = self.statusReply
        self.main.que.sendTo(msg2) 
        self.deviationExplanation = self.deviationExplanation.encode("utf-8")
        print "msg2 = ", msg2

        with open(initialPath + "/device_type_identifiers.txt") as scanneddeviceFile:
                        for line in scanneddeviceFile:
                            line = line.strip()
                            identifier, productName = line.partition("=")[::2]
                            if int(identifier) == int(scanbfdevicetype):
                                scanbfdevicename = productName
                            else:
                                pass                            
        
        savetodb = {
         "productId":productId,
         "desc":self.owdescription['text'],
         "model":model,
         "mainfuncGrp":self.owmainfuncGrp,
         "icLic":IC_L,
         "icEnab":IC_E,
         "synappsLic":SYN_L,
         "synappsEnab":SYN_E,
         "polycomLic":self.owpolycomlicense['text'],
         "polycomEnab":POL_E,
         "dhcpEnab":DHCP,
         "flasherEnab":FLSH,
         "bfdevtype":devType,
         "scanbfdevicetype": scanbfdevicetype,
         "scanbfdevicename": scanbfdevicename,
         "release":self.owreleases.get(),
         "fileName":self.owfilename,
         "appversion":str(vapp),
         "viprunstpver":str(viprunstp),
         "vstartupver":str(vstartup),
         "firmware":firmware,
         "platform":platForm,
         #"shopordernum":,
         "deviationReason":self.deviationExplanation,
         "inputs":str(inputs),
         "channels":str(channels),
         "relays":str(relays),
         "inputConfiguration": str(inputConfiguration),
         "bdtfirmware":str(bdtfirmware),
         "bdtflashers":str(flashers),
         "script":str(scriptname)
        }
        if group in self.tosavetoDB:
            pass
        else: 
            self.tosavetoDB[group] = savetodb        
        self.close_loadcwindow()
        self.cwindow.destroy()
        root.deiconify()
        self.remaininggroups.remove(group)
        
    def getdMacResults(self, msg):
        '''
        This function simply sends the message to system manager to send the MAC Results
        to GUI so that they can be displayed for user review.
        '''
        grpid = msg['grpid']
        msg = {'name':'failedModels', 'data': grpid}
        if self.failwindowClicked == 0:
            self.main.que.sendTo(msg)
            self.failwindowClicked = 1
            self.resps['failedModelsResp']=self.macresults_window
            self.macClicked = 1
        else:
            pass

    def macresults_window(self, msg):
        macResults = msg['data']        
        """
        This function creates the Failed MACs screen that shows all the macs that failed during the 
        load process.
        """ 
        rfailedMacs = msg['data']['Fail']
        rpassedMacs = msg['data']['Pass'] 
        self.macresultswindow = tk.Toplevel(root)
        self.macresultswindow.title("MAC Results")
        sizex = 592
        sizey = 500
        self.macresultswindow.wm_geometry("%dx%d+%d+%d" % (sizex,sizey,posx,posy)) 
        self.macresultswindow.resizable(width=False, height=False) 
        self.macresultswindow.update_idletasks()
        aw = self.macresultswindow.winfo_screenwidth()
        ah = self.macresultswindow.winfo_screenheight()
        asize = tuple(int(_) for _ in self.macresultswindow.geometry().split('+')[0].split('x'))
        ax = aw/2 - size[0]/2 + 275
        ay = ah/2 - size[1]/2 
        self.macresultswindow.geometry("%dx%d+%d+%d" % (asize + (self.mainwinx, self.mainwiny))) 
         
        if self.win == 1:           
            failedMacs = ScrolledText(self.macresultswindow, height=50, width=31)
            failedMacs.grid(row=1, rowspan=7, column=0, columnspan=2, sticky='ns')
            passedMacs = ScrolledText(self.macresultswindow, height=50, width=31)
            passedMacs.grid(row=1, rowspan=7, column=2, columnspan=2, sticky='ns')
            
            FailedMacLabel = tk.Label(failedMacs, text="Failed MACs:", font=self.helv11, anchor = 'center')
            FailedMacLabel.config(width=30)
            FailedMacLabel.grid(row=0, column=0, columnspan=3, sticky='w')
                        
            PassedMacLabel = tk.Label(passedMacs, text="Passed MACs:", font=self.helv11, anchor = 'center')
            PassedMacLabel.config(width=30)
            PassedMacLabel.grid(row=0, column=2, columnspan=3, sticky='w')
        else:
            failedMacs = ScrolledText(self.macresultswindow, height=50, width=35)
            failedMacs.grid(row=1, rowspan=7, column=0, columnspan=2, sticky='ns')
            passedMacs = ScrolledText(self.macresultswindow, height=50, width=35)
            passedMacs.grid(row=1, rowspan=7, column=2, columnspan=2, sticky='ns')
            
            FailedMacLabel = tk.Label(failedMacs, text="Failed MACs:", font=self.helv11, anchor = 'center')
            FailedMacLabel.config(width=34)
            FailedMacLabel.grid(row=0, column=0, columnspan=3, sticky='w')
                        
            PassedMacLabel = tk.Label(passedMacs, text="Passed MACs:", font=self.helv11, anchor = 'center')
            PassedMacLabel.config(width=34)
            PassedMacLabel.grid(row=0, column=2, columnspan=3, sticky='w')
        
        fx = 1 
        rx = 1            
        if macResults == None:
            pass
        else: 
            if self.win == 1:                       
                for mac in rfailedMacs:                       
                    macBtn = tk.Button(failedMacs, text=mac, width=38)
                    macBtn.config(command=lambda mac=mac, macBtn = macBtn: self.getFailReason(mac, macBtn))
                    macBtn.grid(row=fx, column=0, sticky='e') 
                    fx += 1  
                for mac in rpassedMacs:                       
                    macBtn = tk.Button(passedMacs, text=mac, width=38)
                    macBtn.grid(row=rx, column=2, sticky='e')    
                    rx += 1 
            else:
                for mac in rfailedMacs:                       
                    macBtn = tk.Button(failedMacs, text=mac, width=31)
                    macBtn.config(command=lambda mac=mac, macBtn = macBtn: self.getFailReason(mac, macBtn))
                    macBtn.grid(row=fx, column=0, sticky='e') 
                    fx += 1  
                for mac in rpassedMacs:                       
                    macBtn = tk.Button(passedMacs, text=mac, width=31)
                    macBtn.grid(row=rx, column=2, sticky='e')    
                    rx += 1      
                   
        closeBtn = tk.Button(self.macresultswindow, text="Close", command=self.closefailed_window, width=13)
        closeBtn.grid(row=33, column=2, sticky='e')
        
    def getFailReason(self, mac, macBtn):   
        msg = {"name":"failedMac", "data":mac}  
        if self.macfailedreasonClicked == 0:
            self.main.que.sendTo(msg) 
            self.resps['failedMacResp'] = self.macFailReasonDisplay
            self.macfailedreasonClicked = 1
        else:
            pass
                    
    def macFailReasonDisplay(self, msg):
        data = msg["data"]        
        self.macFailReasonDisp = tk.Toplevel(root)
        self.macFailReasonDisp.title('MAC Fail Reason(s)')
        lsizex = 567
        lsizey = 260
        self.macFailReasonDisp.wm_geometry("%dx%d+%d+%d" % (lsizex,lsizey,self.mainwinx, self.mainwiny)) 
        self.macFailReasonDisp.resizable(width=False, height=False) 
        self.macFailReasonDisp.update_idletasks()
        lw = self.macFailReasonDisp.winfo_screenwidth()
        lh = self.macFailReasonDisp.winfo_screenheight()
        lsize = tuple(int(_) for _ in self.macFailReasonDisp.geometry().split('+')[0].split('x'))
        lx = lw/2 - size[0]/2 + 375
        ly = lh/2 - size[1]/2 
        self.macFailReasonDisp.geometry("%dx%d+%d+%d" % (lsize + (self.mainwinx, self.mainwiny))) 
        if self.win == 1:  
            failedMacs = ScrolledText(self.macFailReasonDisp, height=14, width=67, wrap=tk.WORD)
            failedMacs.grid(column=0, row=0, sticky='WE', columnspan=3, padx=2)
            failedMacs.insert('1.0', data)
        else:
            failedMacs = ScrolledText(self.macFailReasonDisp, height=13, width=68, wrap=tk.WORD)
            failedMacs.grid(column=0, row=0, sticky='WE', columnspan=3, padx=2)
            failedMacs.insert('1.0', data)

        closeBtn = tk.Button(self.macFailReasonDisp, text="Close", command=self.failedMACreason_window, width=13)
        closeBtn.grid(row=1, column=1, sticky='e')
        
    def clearGroup(self, grpid): 
        '''
        This function simply sends the message to system manager to clear the group(s) the user wants 
        deleted from its queue.
        '''
        y = grpid
        self.btns[y][5].configure(state = "disabled")
        msg3 = {"name":"clearGroup", "data":grpid}
        self.main.que.sendTo(msg3)
        self.resps["clearGroupResp"] = self.removeRow
        self.keepClearBtnDisabled(y)
        if y in self.storedGroup:
            self.storedGroup.remove(y)
        else:
            pass
        if y in self.remaininggroups:
            self.remaininggroups.remove(y)
        else:
            pass
        if y in self.workorders:
            del self.workorders[y]
        else:
            pass
        if y in self.tosavetoDB:
            del self.tosavetoDB[y]
        else:
            pass        
        
    def keepClearBtnDisabled(self, y):
        '''
        This function keeps track of cleared rows so that the clear button stays disabled
        after it is clicked to clear the row of test results.
        '''
        if y in self.clearedGrps:
            pass
        else:
            self.clearedGrps.append(y)        

    def removeRow(self, msg): 
        '''
        This function clear the row(s) of data that the user wants cleared from the GUI after 
        system manger clears it group data.
        '''   
        grpid = msg['grpid']
        y = grpid
        self.btns[y][5].configure(state = "disable")   
        self.btns[y][0].destroy()
        self.btns[y][1].destroy()
        self.btns[y][2].destroy()
        self.btns[y][3].destroy()
        self.btns[y][4].destroy()
        self.btns[y][5].destroy()
        del self.btns[y]
        self.clearedGrps.remove(y)
                             
    def close_window (self):
        '''
        This function send the exit command to system manager to close out all queues and 
        processes and then closed the GUI.
        '''     
        msg = {"name":"Exit", "data":""}
        self.main.que.sendTo(msg)  
        root.destroy()
        
    def failedMACreason_window(self):
        self.macfailedreasonClicked = 0
        self.macFailReasonDisp.destroy()
        
    def close_configwindow (self, grpid): 
        y = grpid
        self.cwindow.destroy()
        root.deiconify()
        self.btns[y][3].configure(state = "normal")
        
    def close_loadcwindow (self): 
        self.lwindow.destroy()
        self.cwindow.deiconify() 
          
    def cancel_advacecwindow (self): 
        self.detailswindow.destroy()
        
    def ok_advacecwindow (self): 
        self.detailswindow.destroy()
        
    def closeallmacs_window(self): 
        self.allmacswindow.destroy()
                
    def closefailed_window(self): 
        self.macresultswindow.destroy()
        self.failwindowClicked = 0
        self.macClicked = 0
        
    def storeResults(self, msg):
        macsandReasons = msg['data']
        y = msg['grpid']
        failedMacsDict = {}
        passedmacsDict = {}
        testedmacs = {}  
        failedMacsDict = macsandReasons['Fail']
        passedmacsDict = macsandReasons['Pass']
        for mac, statusreason in failedMacsDict.iteritems():
            status = 'Fail'
            testedmacs[mac] =  [status, statusreason]
        for mac, statusreason in passedmacsDict.iteritems():
            status = 'Pass'
            testedmacs[mac] =  [status, statusreason]        
        workorder = self.workorders[y]
        self.btns[y][4].configure(bg="#ffff00", text="Saving to Database")
        time.sleep(1)
        self.win = 0
        detectedOS = platform.system()
        if detectedOS == "Windows":
            self.win = 1
        else:
            self.win = 0
        colstoSave = self.tosavetoDB[y]
        for name in colstoSave:
            if name == 'desc':
                colstoSave['description'] = colstoSave['desc']
                colstoSave['description'] = colstoSave.pop('desc', '')
            if name == 'release':
                colstoSave['brelease'] = colstoSave['release']
                colstoSave['brelease'] = colstoSave.pop('release', '')
        try:
            conn = mysql.connector.connect(host=serverip, user=user, password=passwd, database=database, connect_timeout=connect_timeout)
            x = 0
            if conn.is_connected():
                cursor = conn.cursor()
                dbsql = "show columns from LineLoader"
                cursor.execute(dbsql)
                results = list(cursor.fetchall())
                for result in results:
                    result = str(results[x][0])
                    if result in colstoSave:
                        pass
                    else:                          
                        pass
                    x = x + 1
                for mac, maclist in testedmacs.iteritems():
                    mac = mac
                    actualmac = mac
                    maclist = maclist
                    status = maclist[0]
                    statusreason = maclist[1]
                    workorder = self.workorders[y]
                    now = datetime.datetime.now()
                    storedtimeActual = str(now)[:19]
                    storedtime = str(now)[:19]
                    storedtime = storedtime.replace('-', '')
                    storedtime = storedtime.replace(':', '')
                    storedtime = storedtime.replace(' ', '')
                    mac = mac.replace(':','')
                    insertion = ("insert into LineLoader (mac, productId, description, model, mainfuncGrp, icLic, icEnab, synappsLic," + 
                        "synappsEnab, polycomLic, polycomEnab, dhcpEnab, flasherEnab, bfdevtype, brelease, fileName, appversion, " +
                        "viprunstpver, vstartupver, inputs, channels, relays, inputConfiguration, bdtfirmware, status, statusreason, " + 
                        "firmware, platform, deviationReason, storedtime, workorder, bdtflashers, scanbfdevicetype, scanbfdevicename, script)" +
                        " values ('" + actualmac + "', '" + colstoSave['productId'] + "', '" + colstoSave['description'] + "', '" + colstoSave['model'] 
                        + "', '" + colstoSave['mainfuncGrp'] + "', '" + str(colstoSave['icLic']) + "', '"
                        + str(colstoSave['icEnab']) + "', '" + str(colstoSave['synappsLic']) + "', '" + str(colstoSave['synappsEnab']) + "', '"
                        + str(colstoSave['polycomLic']) + "', '" + str(colstoSave['polycomEnab']) + "', '" + str(colstoSave['dhcpEnab']) + "', '"
                        + str(colstoSave['flasherEnab']) + "', '" + str(int(colstoSave['bfdevtype'])) + "', '" + colstoSave['brelease'] + "', '"
                        + colstoSave['fileName'] + "', '" + colstoSave['appversion'] + "', '" + str(colstoSave['viprunstpver']) + "', '" 
                        + colstoSave['vstartupver'] + "', '" + str(colstoSave['inputs']) + "', '" + str(colstoSave['channels']) + "', '" 
                        + str(colstoSave['relays']) + "', '" + str(colstoSave['inputConfiguration']) + "', '" + str(colstoSave['bdtfirmware']) 
                        + "', '" + status + "', '" + statusreason + "', '" + str(colstoSave['firmware']) + "', '" + str(colstoSave['platform']) 
                        + "', '" + str(colstoSave['deviationReason']) + "', '" + str(storedtimeActual) + "', '" + str(workorder)
                        + "', '" + str(colstoSave['bdtflashers']) + "', '" + str(colstoSave['scanbfdevicetype']) 
                        + "', '" + str(colstoSave['scanbfdevicename']) + "', '" + str(colstoSave['script']).strip() + "')")
                    result = cursor.execute(insertion)
            try:
                os.makedirs("SavedInserts")
            except OSError:
                if self.win == 1:
                    path = ("SavedInserts\\")
                elif self.win == 0:
                    path = ("SavedInserts/")
                else:
                    print "Verify Operating System is supported by the program"                       
                dirList=os.listdir(path)
                for filename in dirList:
                    with open(path + filename, 'r') as insertfile:
                        insertString = insertfile.read()
                        insertString = insertString[1:-1]
                        cursor.execute(insertString)
                        insertfile.close()
                        os.remove(path + filename)                    
            conn.commit()            
            conn.close()                               
        except Error as error:
            print error
            print "Unable to connect to the database."
            try:
                os.makedirs('SavedInserts')
                print "Creating directory"
                print "Saving data to new directory"
                for mac, maclist in testedmacs.iteritems():
                    mac = mac
                    actualmac = mac
                    maclist = maclist
                    status = maclist[0]
                    statusreason = maclist[1]
                    workorder = self.workorders[y]
                    now = datetime.datetime.now()
                    storedtimeActual = str(now)[:19]
                    storedtime = str(now)[:19]
                    storedtime = storedtime.replace('-', '')
                    storedtime = storedtime.replace(':', '')
                    storedtime = storedtime.replace(' ', '')
                    mac = mac.replace(':','')
                    if self.win == 1:
                        path = ("SavedInserts\\" + mac + "__" + storedtime + ".txt")
                    elif self.win == 0:
                        path = ("SavedInserts/" + mac + "__" + storedtime + ".txt")
                    else:
                        print "Verify Operating System is supported by the program"                      
                    filetoopen = open(path,"w+")
                    filetoopen.close()
                    insertion = ("insert into LineLoader (mac, productId, description, model, mainfuncGrp, icLic, icEnab, synappsLic," + 
                        "synappsEnab, polycomLic, polycomEnab, dhcpEnab, flasherEnab, bfdevtype, brelease, fileName, appversion, " +
                        "viprunstpver, vstartupver, inputs, channels, relays, inputConfiguration, bdtfirmware, status, statusreason, " + 
                        "firmware, platform, deviationReason, storedtime, workorder, bdtflashers, scanbfdevicetype, scanbfdevicename, script)" +
                        " values ('" + actualmac + "', '" + colstoSave['productId'] + "', '" + colstoSave['description'] + "', '" + colstoSave['model'] 
                        + "', '" + colstoSave['mainfuncGrp'] + "', '" + str(colstoSave['icLic']) + "', '"
                        + str(colstoSave['icEnab']) + "', '" + str(colstoSave['synappsLic']) + "', '" + str(colstoSave['synappsEnab']) + "', '"
                        + str(colstoSave['polycomLic']) + "', '" + str(colstoSave['polycomEnab']) + "', '" + str(colstoSave['dhcpEnab']) + "', '"
                        + str(colstoSave['flasherEnab']) + "', '" + str(int(colstoSave['bfdevtype'])) + "', '" + colstoSave['brelease'] + "', '"
                        + colstoSave['fileName'] + "', '" + colstoSave['appversion'] + "', '" + str(colstoSave['viprunstpver']) + "', '" 
                        + colstoSave['vstartupver'] + "', '" + str(colstoSave['inputs']) + "', '" + str(colstoSave['channels']) + "', '" 
                        + str(colstoSave['relays']) + "', '" + str(colstoSave['inputConfiguration']) + "', '" + str(colstoSave['bdtfirmware']) 
                        + "', '" + status + "', '" + statusreason + "', '" + str(colstoSave['firmware']) + "', '" + str(colstoSave['platform']) 
                        + "', '" + str(colstoSave['deviationReason']) + "', '" + str(storedtimeActual) + "', '" + str(workorder)
                        + "', '" + str(colstoSave['bdtflashers']) + "', '" + str(colstoSave['scanbfdevicetype']) 
                        + "', '" + str(colstoSave['scanbfdevicename']) + "', '" + str(colstoSave['script']).strip() + "')")
                    mac = mac.replace(':','')
                    if self.win == 1:
                        path = ("SavedInserts\\" + mac + "__" + storedtime + ".txt")
                    elif self.win == 0:
                        path = ("SavedInserts/" + mac + "__" + storedtime + ".txt")
                    else:
                        print "Verify Operating System is supported by the program"                      
                    filetoopen = open(path,"w+") 
                    filetoopen.write("'" + insertion + "\n")
                    filetoopen.close()
            except OSError:
                print "Saving data to new file"
                for mac, maclist in testedmacs.iteritems():
                    mac = mac
                    actualmac = mac
                    maclist = maclist
                    status = maclist[0]
                    statusreason = maclist[1]
                    workorder = self.workorders[y]
                    now = datetime.datetime.now()
                    storedtimeActual = str(now)[:19]
                    storedtime = str(now)[:19]
                    storedtime = storedtime.replace('-', '')
                    storedtime = storedtime.replace(':', '')
                    storedtime = storedtime.replace(' ', '')
                    mac = mac.replace(':','')
                    if self.win == 1:
                        path = ("SavedInserts\\" + mac + "__" + storedtime + ".txt")
                    elif self.win == 0:
                        path = ("SavedInserts/" + mac + "__" + storedtime + ".txt")
                    else:
                        print "Verify Operating System is supported by the program"                      
                    filetoopen = open(path,"w+")
                    filetoopen.close()
                    insertion = ("insert into LineLoader (mac, productId, description, model, mainfuncGrp, icLic, icEnab, synappsLic," + 
                        "synappsEnab, polycomLic, polycomEnab, dhcpEnab, flasherEnab, bfdevtype, brelease, fileName, appversion, " +
                        "viprunstpver, vstartupver, inputs, channels, relays, inputConfiguration, bdtfirmware, status, statusreason, " + 
                        "firmware, platform, deviationReason, storedtime, workorder, bdtflashers, scanbfdevicetype, scanbfdevicename, script)" +
                        " values ('" + actualmac + "', '" + colstoSave['productId'] + "', '" + colstoSave['description'] + "', '" + colstoSave['model'] 
                        + "', '" + colstoSave['mainfuncGrp'] + "', '" + str(colstoSave['icLic']) + "', '"
                        + str(colstoSave['icEnab']) + "', '" + str(colstoSave['synappsLic']) + "', '" + str(colstoSave['synappsEnab']) + "', '"
                        + str(colstoSave['polycomLic']) + "', '" + str(colstoSave['polycomEnab']) + "', '" + str(colstoSave['dhcpEnab']) + "', '"
                        + str(colstoSave['flasherEnab']) + "', '" + str(int(colstoSave['bfdevtype'])) + "', '" + colstoSave['brelease'] + "', '"
                        + colstoSave['fileName'] + "', '" + colstoSave['appversion'] + "', '" + str(colstoSave['viprunstpver']) + "', '" 
                        + colstoSave['vstartupver'] + "', '" + str(colstoSave['inputs']) + "', '" + str(colstoSave['channels']) + "', '" 
                        + str(colstoSave['relays']) + "', '" + str(colstoSave['inputConfiguration']) + "', '" + str(colstoSave['bdtfirmware']) 
                        + "', '" + status + "', '" + statusreason + "', '" + str(colstoSave['firmware']) + "', '" + str(colstoSave['platform']) 
                        + "', '" + str(colstoSave['deviationReason']) + "', '" + str(storedtimeActual) + "', '" + str(workorder)
                        + "', '" + str(colstoSave['bdtflashers']) + "', '" + str(colstoSave['scanbfdevicetype']) 
                        + "', '" + str(colstoSave['scanbfdevicename']) + "', '" + str(colstoSave['script']).strip() + "')")
                    filetoopen = open(path,"w+")
                    filetoopen.write("'" + insertion + "\n")
                    filetoopen.close()
        self.btns[y][4].configure(bg="#33ff00", text="Database Save Complete")
        time.sleep(1)
         
def on_close():
    app.close_window() 

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if len(sys.argv) == 2:
        initialPath = sys.argv[1]
    else:
        print ("Please verify and reenter the command and path to the file location where your files are stored.")
        sys.exit() 
    root = tk.Tk()
    root.title("Valcom Loader Release 4")
    root.wm_geometry("%dx%d+%d+%d" % (sizex,sizey,posx,posy))
    root.resizable(width=False, height=False)
    root.update_idletasks()
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    size = tuple(int(_) for _ in root.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    root.geometry("%dx%d+%d+%d" % (size + (x, y)))
    app = lineLoader(root)
    root.protocol("WM_DELETE_WINDOW",  on_close)
    root.mainloop()
