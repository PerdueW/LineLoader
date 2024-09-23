#!/usr/bin/python


from multiprocessing import Process, Queue
import time
import socket
import select
import re
import os
import sys
import mysql.connector
from mysql.connector import Error, errorcode
import threading
import struct
from Tkinter import *
import netifaces
from device import DeviceInit
import io
import platform
import tarfile
import shutil


class SysManager(object):
    #bfdtTable = {'0':'18',   '1':'20',   '2':'18',   '3':'0',   '4':'0',   '5':'0',   '6':'3',   '8':'8',\
    #             '9':'8',    '10':'33',  '11':'34',  '16':'16', '17':'17', '18':'37', '28':'28', '30':'30',\
    #             '31':'31',  '32':'1',   '33':'1',   '34':'1',  '35':'35', '36':'18', '37':'31', '38':'38',\
    #             '39':'39',  '40':'40',  '41':'23',  '42':'2',  '43':'2',  '44':'2',  '45':'45', '46':'44',\
    #             '47':'47',  '48':'35',  '49':'48',  '50':'49', '51':'39', '52':'50', '53':'18', '54':'33',\
    #             '55':'35',  '56':'56',  '1000':'18',  '1001':'18',  '1002':'18',  '1003':'18'}
    def __init__(self,guiTxQ, guiRxQ):
        """ This is the System Manager process. Each device will be parsed in and given 
            an instance to handle proccess. The routine will then monitor the receive 
            Queue from the GUI and route the message to the appropriate Device for handling.
        """
        super(SysManager, self).__init__()
        self.TxQ = guiTxQ
        self.RxQ = guiRxQ
        self.myIP = None
        self.devices = {}           # devices holds {Mac: [model, IP, 'STATUS', grpID, (fail reason)]}
        self.models = []            # a list of all model names
        self.sock = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM), socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]        # initialize socket

        self.sysManTxQ = {}         # MsgTxQ queue for each device
        self.sysManRxQ = Queue()    # MsgRxQ belongs to SysMan
        self.loadedMac = []         # a list of loaded devices of all models
        self.vInfo = {}             # verification info storage

    def runProcess(self):
        """ This is the starting point of the SysMan process. It handles all commands sent from GUI.
        """
        self.setUpSocket()
        self.getMyIP()
        running = True
        while(running):
            # Parse commands
            if not self.RxQ.empty():
                msg = self.RxQ.get(timeout=1)
                if msg['name'] == "Exit":
                    self.closeSocket()
                    running = False
                elif msg['name'] == "getGroupStatus":
                    self.replyNumDevices()
                elif msg['name'] == "Load":
                    self.loadGroup(msg['data'])
                elif msg['name'] == "failedModels":
                    self.failedModels(msg['data'])
                elif msg['name'] == "failedMac":
                    self.failedMac(msg['data'])
                elif msg['name'] == "clearGroup":
                    self.clearGroup(msg['data'])
                else:
                    print "Unrecognized Request! Report to engineer"
            if not self.sysManRxQ.empty():
                self.getDeviceMsg()
            if len(self.loadedMac) > 0:
                self.verifyLoad()
            else:
                self.pollForDevice()
            time.sleep(0.01)

    def getMyIP(self):
        """ This function only retrieves IP address of the host.
            It should work with both Linux and Windows OS. Quits if can't
        """
        if "Linux" in platform.system():
            try:
                self.myIP = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
            except:
                self.myIP = netifaces.ifaddresses('enp0s3')[netifaces.AF_INET][0]['addr']
        elif "Windows" in platform.system():
            self.myIP = socket.gethostbyname(socket.gethostname())
        else:
            print "Cannot determine OS!"
            sys.exit()

    def replyNumDevices(self):
        """ This is the routine gets called when GUI wants a device count.
            It replies the number and status of devices for all models/groups.
            Returns a dictionary. Mac ending w/ 66:66:66 will trigger error state.
        """
        for x in self.devices.keys():
            if self.devices[x][0] not in self.models:
                self.models.append(self.devices[x][0])
            self.devices[x][3] = self.models.index(self.devices[x][0])
        groups = []
        for x in self.models:
            numBrd = 0
            passNum = 0
            failNum = 0
            groupStat = {}
            for y in self.devices.keys():
                if self.devices[y][0] == x:
                    numBrd += 1
                    if self.devices[y][2] not in groupStat:
                        groupStat[self.devices[y][2]] = 1
                    else:
                        groupStat[self.devices[y][2]] += 1
                    if self.devices[y][2] == 'PASS':
                        passNum += 1
                    elif self.devices[y][2] == 'FAIL':
                        failNum += 1
            msg1 = {'grpid':self.models.index(x), 'model':x, 'count':numBrd, 'status':groupStat}
            if (passNum + failNum) == numBrd:
                if failNum > 0:
                    msg1["Group Complete"] = "FAIL"
                else:
                    msg1["Group Complete"] = "PASS"
            if numBrd > 0:
                groups.append(msg1)
        if len(groups) is 0:
            msg = {'name':"getGroupStatusResp", 'data':'No Device Attached.'}
        else:
            msg = {'name':'getGroupStatusResp', 'data':groups}
        self.TxQ.put(msg)       

    def setUpSocket(self):
        """ Routine initializes socket for beacon receiving. It monitors 239.1.1.2@4097
            and 239.1.1.5@4121 which 102Btool does too.
        """
        for x in range(len(self.sock)):
            if x == 0:
                addr = ('',4097)
                mgroup = '239.1.1.2'
            elif x == 1:
                addr = ('',4121)
                mgroup = '239.1.1.5'
            self.sock[x].bind(addr)
            self.sock[x].setblocking(0)
            group = socket.inet_aton(mgroup)
            mreq = struct.pack('4sL',group, socket.INADDR_ANY)
            self.sock[x].setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def pollForDevice(self):
        """ Poll from sockets and fill up devices[] with new boards came in.
        """
        result = {}
        for x in range(len(self.sock)):
            while select.select([self.sock[x]],[],[],0)[0]:     #clear all beacons from socket
                data, address = self.sock[x].recvfrom(1024)
                if data.count(',')>17:
                    #print "data = ", data
                    splitData = str(data).split(',')
                    if splitData[4].split(chr(0))[-1] != '0' or splitData[0] != '493':
                        continue  #not our beacon format
                    mac = splitData[11]
                    model = splitData[7]
                    ip = splitData[5]
                    startup_ver = splitData[14]
                    if mac not in self.devices.keys():
                        if '66:66:66' not in mac:  #empty mac issue
                            self.devices[mac] = [model, ip, 'IDLE', 0, None]
                        else:
                            self.devices[mac] = [model, ip, 'ERROR', 0, None]
                    if mac not in result.keys():
                        try:
                            result[mac] = [splitData[9]+'.'+splitData[10]+'.'+splitData[21], startup_ver, ip, model]
                        except:
                            result[mac] = [splitData[9]+'.'+splitData[10]+'.0', startup_ver, ip, model]     # 806 doesn't have build rev
        return result

    def closeSocket(self):
        """ close all sockets.
        """
        for x in range(len(self.sock)):
            self.sock[x].close()

    def loadGroup(self, data):
        """ Solve the IP conflicts first. Create processes for devices in groups of 20.
            Send load commands to each process.
        """
        msg = {'name':'LoadResp', 'data':'Loading...', 'grpid':data['grpid']}
        self.TxQ.put(msg)
        self.solveIP(data['grpid'])
        data['path'] = self.prepareTar(data['path'], data['platform'], data['firmware'],data['script'])
        self.vInfo[data['grpid']] = data
        arguments = []
        n = 0
        for x in self.devices.keys():
            if self.devices[x][3] == data['grpid']:
                self.sysManTxQ[x] = Queue()
                if n < 20:  #somewhat Windows can't handle that many processes
                    arguments.append({'Mac':[x],'IP':[self.devices[x][1]],'TxQ':[self.sysManTxQ[x]]})
                else:
                    p = n%20
                    arguments[p]['Mac'].append(x)
                    arguments[p]['IP'].append(self.devices[x][1])
                    arguments[p]['TxQ'].append(self.sysManTxQ[x])
                n += 1
                msg = {'name':'Load'}
                msg.update(data)
                self.sysManTxQ[x].put(msg)
        # Create instances for devices
        for x in range(len(arguments)):
            proc = Process(target=DeviceInit, \
                           args=(arguments[x]['Mac'], arguments[x]['IP'], arguments[x]['TxQ'], self.sysManRxQ))
            proc.start()

    def solveIP(self, groupNum):
        """ This deals with IP conflicts. It looks through all IPs occupied in devices[]
            then determines the available IPs that can be assigned to boards. It should not
            set IPs if there is not conflict. Using 998 to set individual IPs. Using 997 to
            reset the boards.
        """
        mySubnet = (".").join(self.myIP.split(".")[:3])
        IPs = []
        IPsO = []
        conflicts = False
        for x in self.devices.keys():
            IPsO.append(int(self.devices[x][1].split('.')[-1])) #Record of occupied IPs
            if self.devices[x][3] == groupNum:
                IPs.append(int(self.devices[x][1].split('.')[-1]))
        for x in IPs:
            if IPsO.count(x) > 1: #duplicates exist
                conflicts = True
                break
        if not conflicts:
            return 0
        #   Send UDP broadcast to set all IPs
        IPsA = [str(i) for i in range(2,240) if i not in IPsO] #Available IPs to assign from
        self.sock[0].setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        for i in range(2): #Send twice just in case
            n = 0
            for x in self.devices.keys():
                if self.devices[x][3] == groupNum:
                    self.devices[x][2] = "Configuring IP"
                    self.devices[x][1] = mySubnet+'.'+IPsA[n]
                    msg = "998,0,0,0,0"+chr(0)*64
                    msg = msg[:64]+x+","+mySubnet+'.'+IPsA[n]+",255.255.255.0,"+mySubnet+".1"+chr(0)
                    self.sock[0].sendto(msg,('255.255.255.255', 4097))
                    msg1 = "997,0,0,0,0"+chr(0)*64
                    msg1 = msg1[:64]+x+","+chr(0)
                    self.sock[0].sendto(msg1,('255.255.255.255', 4097))
                    time.sleep(0.01)
                    n += 1

    def clearGroup(self, groupNum):
        """ This deletes boards from devices[]
        """
        for x in self.devices.keys():
            if self.devices[x][3] == groupNum:
                del self.devices[x]
        if groupNum in self.vInfo.keys():
            del self.vInfo[groupNum]
        msg = {'name':'clearGroupResp', 'data':'Cleared.', 'grpid':groupNum}
        self.TxQ.put(msg)

    def failedModels(self, groupNum):
        """ Pick failed devices belong to this requested group
        """
        failList = {}
        passList = {}
        for x in self.devices.keys():
            if self.devices[x][3] == groupNum:
                if self.devices[x][2] == 'FAIL':
                    failList[x] = self.devices[x][4]
                elif self.devices[x][2] == 'PASS':
                    passList[x] = 'PASS'
        data = {'Pass':passList,'Fail':failList}
        msg = {'name':'failedModelsResp', 'data':data, 'grpid':groupNum}
        self.TxQ.put(msg)

    def failedMac(self, mac):
        """ This responds the failing reasons with the mac.
        """
        if self.devices[mac][4] != None:
            msg = {'name':'failedMacResp','data':self.devices[mac][4]}
        else:
            msg = {'name':'failedMacResp','data':'PASS'}
        self.TxQ.put(msg)

    def getDeviceMsg(self):
        """ This routine handles the messages from device processes. It updates device status
            and communicate back to device processes.
        """
        while not self.sysManRxQ.empty():      #messages from sub-processes
            msg = self.sysManRxQ.get(timeout=1)
            if msg[0] == 'Load Complete' and msg[1] not in self.loadedMac:
                self.loadedMac.append(msg[1])
                self.devices[msg[1]][2] = msg[0]
            elif msg[0] == 'PASS' or msg[0] == 'FAIL':
                self.devices[msg[1]][2] = msg[0]
                self.devices[msg[1]][4] = msg[2]
                if msg[1] in self.sysManTxQ:
                    self.sysManTxQ[msg[1]].put({'name':'Exit'})
                    del self.sysManTxQ[msg[1]]
            elif msg[0] == 'PREDUMP':
                if msg[2].find('RESULT: FAIL') != -1:
                    self.devices[msg[1]][2] = 'FAIL'
                    self.devices[msg[1]][4] = msg[2]
                    if msg[1] in self.sysManTxQ:
                        del self.sysManTxQ[msg[1]]
                elif msg[2].find('RESULT: PASS') != -1:
                    self.devices[msg[1]][4] = msg[2]
            elif len(msg) == 2:
                self.devices[msg[1]][2] = msg[0]

    def verifyLoad(self):
        """ This routine looks for beacons after load competes. Then sends to device processes
            for verifications.
        """
        beacons = self.pollForDevice()
        for mac in beacons.keys():
            if mac in self.loadedMac:
                groupNum = self.devices[mac][3]
                msg1 = ''
                if beacons[mac][3] != self.vInfo[groupNum]['scan-device-type']:
                    msg1 += "scan-device-type Error\n"
                if beacons[mac][0] != self.vInfo[groupNum]['vapp']:
                    msg1 += "App version Error\n"
                if beacons[mac][1] != self.vInfo[groupNum]['vstartup']:
                    msg1 += "Vstartup Error\n"
                if msg1 != '':
                    self.devices[mac][2] = 'FAIL'
                    self.devices[mac][4] = msg1
                else:
                    self.sysManTxQ[mac].put({'name':'Verify', 'IP':beacons[mac][2], 'Mac':mac})
                self.loadedMac.remove(mac)

    def prepareTar(self, oldpath, platForm, firmWare, scriptName):
        """ This function untar 102B and script tar on PC for later use """
        upgradeTar = tarfile.open(oldpath)
        if "Linux" in platform.system():
            fileName = oldpath.split("/")[-1]
            oldpath = oldpath.rsplit("/",1)[0]+'/'
            newpath = oldpath + "temp/"
        elif "Windows" in platform.system():
            fileName = oldpath.split("\\")[-1]
            oldpath = oldpath.rsplit("\\",1)[0]+'\\'
            newpath = oldpath + "temp\\"
        else:
            print "Cannot determine OS!"
            return None
        if os.path.isdir(newpath):  #clean the diretory if already exists
            shutil.rmtree(newpath);
        if scriptName != '':
            scriptTar = tarfile.open(oldpath+scriptName)
            scriptTar.extractall(path=newpath)
            scriptTar.close()
        upgradeTar.extractall(path=newpath)
        upgradeTar.close()
        contentFile = open(newpath+"table_of_contents","r")    # get the inner tar file name
        for lines in contentFile:
            if (firmWare != '' and lines.find(firmWare+'=') != -1) or \
                (firmWare == '' and lines.find(platForm+'=') != -1):
                fileName = lines.split('=')[-1].rstrip('\n\r')
                break
        contentFile.close()
        return newpath+fileName

    def deleteTar(self, dPath):
        """ this function deletes the temp folder """
        if "Linux" in platform.system():
            newpath = dPath.rsplit("/",1)[0]
        elif "Windows" in platform.system():
            newpath = dPath.rsplit("\\",1)[0]
        if os.path.isdir(newpath):
            shutil.rmtree(newpath)

def SysManInit(guiQueue):
    """ This is Init function called by GUI
    """
    sysManProc = SysManager(guiQueue.txQ, guiQueue.rxQ)
    sysManProc.runProcess()

