#!/usr/bin/python

import time
import re
import sys
import telnetlib
import ftplib
import os
import platform


class Device(object):
    """ This is an instance handles all loading processes
        for a particular device. It communicates with SysMan.
    """
    def __init__(self, Mac, IP, RxQfromSM, TxQtoSM):
        super(Device, self).__init__()
        self.TxQ = TxQtoSM
        self.RxQ = RxQfromSM        # dictionary type
        self.mac = Mac
        self.ip = IP
        self.path = None
        self.model = None
        self.verify = {}

    def runProcess(self):
        """ This is the main process.
        """
        timer = False
        timerS = 1200
        tiktok = 0
        running = True
        stat = ['' for i in range(len(self.mac))]
        while(running):
            for x in range(len(self.RxQ)):
                if not self.RxQ[x].empty():
                    msg = self.RxQ[x].get(timeout=1)
                    if msg['name'] == 'Verify':
                        stat[x] = 'Verify'
                        if stat.count('Verify') == len(self.mac):
                            timer = False
                        self.VerifyLoad(msg)
                    elif msg['name'] == 'Exit':
                        stat[x] = 'Exit'
                        if stat.count('Exit') == len(self.mac):
                            running = False
                    elif x == 0 and msg['name'] == 'Load':
                        self.model = msg['model']
                        self.path = msg['path']
                        if self.LoadUpdate():
                            running = False
                            break
                        self.FileOperate(msg)
                        timer = True
                        timerS = len(self.mac)*2400 # 2400x0.05=120sec/board
                        tiktok = 0  
            if timer:
                tiktok += 1
                if tiktok >= timerS:
                    self.ReportFail()
                    timer = False
            time.sleep(0.050)

    def ReportFail(self):
        """ This routine handles timeout.
        """
        for x in range(len(self.mac)):
            msg1 = ['FAIL', self.mac[x], "Timeout Error\n"]
            self.TxQ.put(msg1)

    def telComm(self, tn, command):
        respond = ''
        tn.write(command+" \n")
        while respond.find('#') == -1:
            respond += tn.read_very_eager()
        return respond

    def GetModel(self):
        """ Get model, firmware and script using telnet.
        """
        for x in range(60):
            try:
                tn = telnetlib.Telnet(self.ip[0])
                break
            except:
                time.sleep(1)
        tn = self.startTelnet(self.ip[0])
        inifile = self.telComm(tn, "cat /mnt/factory.ini")
        tn.close()
        splitinifile = str(inifile).split('\r\n')
        script, model, firmware, platform = ['' for x in range(4)]
        for x in splitinifile:
            if 'model=' in x and 'sipmodel' not in x:
                model = x.lstrip("model=")
            elif 'firmware=' in x:
                firmware = x.lstrip("firmware=")
            elif 'platform=' in x:
                platform = x.lstrip("platform=")
            elif 'upgradescript=' in x:
                script = x.lstrip("upgradescript=")
        msg={'model':model, 'firmware':firmware, 'platform':platform, 'script':script}
        return msg

    def LoadUpdate(self):
        """ ftp scrip tar and run it first.
            If success:
                remove some apps
                ftp upgrade tar
                put network.ini aside
            Do NOT do above if fail
        """
        modelInfo = self.GetModel()
    # Determine file names based on OS
        if self.model.find(modelInfo['model']) < 0:
            print "Warning: Model not matched"
        if "Linux" in platform.system():
            upgradeTarName = self.path.split("/")[-1]
            self.path  = self.path.rsplit("/",1)[0] + '/'
        elif "Windows" in platform.system():
            upgradeTarName = self.path.split("\\")[-1]
            self.path = self.path.rsplit("\\",1)[0]+'\\'
    # FTP tar
        scriptFailed = 0
        for x in range(len(self.mac)):
            ftp = ftplib.FTP(self.ip[x], 'root', 'moonbase')
            ftp.cwd('/tmp')
            if os.path.isfile(self.path+'PreScript.tar') : # we have pre tar to load
                s = open(self.path+'PreScript.tar', 'rb')
                ftp.storbinary('STOR '+'PreScript.tar', s)
                s.close()
                if not self.RunPreScript(self.ip[x], self.mac[x]):
                    scriptFailed += 1
                    ftp.quit()
                    continue    # if PreScript fails, we skip the rest
            self.TxQ.put(['Loading Tar', self.mac[x]])
            f = open(self.path+upgradeTarName, 'rb')
            ftp.storbinary('STOR '+upgradeTarName, f)
            f.close()
            ftp.quit()
    # Telnet to process tar
            tn = self.startTelnet(self.ip[x])
            #tn.set_debuglevel(1)
            self.telComm(tn, "rm -rf /mnt/options.txt /mnt/bin/vip* /mnt/bin/vstartup /mnt/log/log*")
            self.telComm(tn, "cp /mnt/network.ini /mnt/networkOLD.ini")
            if len(modelInfo['script']) > 0:            # Run update script
                self.telComm(tn, modelInfo['script']+" /tmp/"+upgradeTarName)
            else:            # Untar file manually
                self.telComm(tn, "tar -xf /tmp/"+upgradeTarName+" -C /")
            self.telComm(tn, "mv /mnt/network.ini /mnt/networkNEW.ini")
            self.telComm(tn, "mv /mnt/networkOLD.ini /mnt/network.ini")
            strng = "sed -i \'s/ipaddr=.*/ipaddr="+self.ip[x]+"/g\' /mnt/network.ini"
            self.telComm(tn, str(strng))
            self.telComm(tn, "sed -i 's/dhcp=1/dhcp=0/g' /mnt/network.ini")
            gtway =  (".").join(self.ip[x].split(".")[:3])+".1"
            strng = "sed -i \'s/gateway=.*/gateway="+gtway+"/g\' /mnt/network.ini"
            self.telComm(tn, str(strng))
            tn.close()
        if scriptFailed > 0:
            return True  #PreScript.sh failed, no need to run the rest
        else:
            return False

    def RunPreScript(self, IP, MAC):
        """run the PreScript and send result to main"""
        self.TxQ.put(['Running PreSctipt', MAC])
        tn = self.startTelnet(IP)
        #tn.set_debuglevel(1)
        self.telComm(tn, "tar -xf /tmp/PreScript.tar -C /")
        scriptDump = self.telComm(tn, "/tmp/PreScript.sh")
        scriptDump.rstrip('#')
        msg1 = ['PREDUMP', MAC, scriptDump]
        self.TxQ.put(msg1)
        tn.close()
        if scriptDump.find('RESULT: FAIL') != -1:
            return False
        else:
            return True

    def startTelnet(self, IP):
        tn = telnetlib.Telnet(IP)
        #tn.set_debuglevel(1)
        tn.read_until("login: ")
        tn.write(b"root" + b"\n")
        tn.read_until("Password:")
        tn.write(b"moonbase" + b"\n")
        tn.read_until("#")
        return tn

    def FileOperate(self, msg):
        for x in range(len(self.mac)):
            tn = self.startTelnet(self.ip[x])
            #tn.set_debuglevel(1)
            if msg['DHCP']:
                self.telComm(tn, "sed -i 's/dhcp=0/dhcp=1/g' /mnt/networkNEW.ini")
            elif not msg['DHCP']:
                self.telComm(tn, "sed -i 's/dhcp=1/dhcp=0/g' /mnt/networkNEW.ini")
                self.telComm(tn, "sed -i \'s/ipaddr=.*/ipaddr=192.168.6.203/g\' /mnt/networkNEW.ini")
        #####################Here is the bf-device-type.ini section
            self.telComm(tn, "echo "+str(msg["device-type"])+" > /mnt/bf-device-type.ini")
            self.telComm(tn, "echo \'productName="+msg['product']+"\' >> /mnt/bf-device-type.ini")
            if msg['flashers'] != '':
                self.telComm(tn, "echo \'flashers="+msg['flashers']+"\' >> /mnt/bf-device-type.ini")
            if msg['inputs'] != '':
                self.telComm(tn, "echo \'inputs="+msg['inputs']+"\' >> /mnt/bf-device-type.ini")
            if msg['channels'] != '':
                self.telComm(tn, "echo \'channels="+msg['channels']+"\' >> /mnt/bf-device-type.ini")
            if msg['relays'] != '':
                self.telComm(tn, "echo \'relays="+msg['relays']+"\' >> /mnt/bf-device-type.ini")
            if msg['inputConfiguration'] != '':
                self.telComm(tn, "echo \'inputConfiguration="+msg['inputConfiguration']+"\' >> /mnt/bf-device-type.ini")
            if msg['bdtfirmware'] != '':
                self.telComm(tn, "echo \'firmware="+msg['bdtfirmware']+"\' >> /mnt/bf-device-type.ini")
        ############### InformaCast key and enable
            if msg['IC_E']:
                self.telComm(tn, "echo enabled=1 > /mnt/informacast.ini")
            elif not msg['IC_E']:
                self.telComm(tn, "rm /mnt/informacast.ini")
            options = False
            if msg['IC_L']:
                self.telComm(tn, "echo \'["+self.mac[x].lower()+"]\' > /mnt/options.txt")
                self.telComm(tn, "echo -n \'InformaCast=\' >> /mnt/options.txt")
                self.telComm(tn, "echo -n InformaCast"+self.mac[x].lower()+"valcom | md5sum >> /mnt/options.txt")
                self.telComm(tn, "sed -i 's/-//g' /mnt/options.txt")
                options = True
        ############### SynApps key and enable
            if msg['SYN_E']:
                self.telComm(tn, "echo enabled=1 > /mnt/synapps.ini")
            elif not msg['SYN_E']:
                self.telComm(tn, "rm /mnt/synapps.ini")
            if msg['SYN_L']:
                if not options:
                    self.telComm(tn, "echo \'["+self.mac[x].lower()+"]\' > /mnt/options.txt")
                self.telComm(tn, "echo -n \'synapps=\' >> /mnt/options.txt")
                self.telComm(tn, "echo -n synapps"+self.mac[x].lower()+"valcom | md5sum >> /mnt/options.txt")
                self.telComm(tn, "sed -i 's/-//g' /mnt/options.txt")
                options = True
        ###############
            if not options:     #delete options.txt if not created by us
                self.telComm(tn, "rm /mnt/options.txt")
            if msg['POL_E']:
                self.telComm(tn, "echo enabled=1 > /mnt/polycom.ini")
            elif not msg['POL_E']:
                self.telComm(tn, "echo enabled=0 > /mnt/polycom.ini")
            try:
                tn.write(b"reboot\n")       # reboot on some devices terminates telnet
                tn.read_until("#", 1)       # seems need a read after reboot anyway
                tn.close()
            except:
                pass
        time.sleep(8)              # this delay does not delay process. Let main process consume beacons
        for x in range(len(self.mac)):
            msg1 = ['Load Complete', self.mac[x]]
            self.TxQ.put(msg1)
        self.verify = msg

    def VerifyLoad(self, msg):
        msg1 = ""
        for x in range(60):
            try: # detected beacon but may not be able to connect yet
                ftp = ftplib.FTP(self.ip[x], 'root', 'moonbase')
                break
            except:
                time.sleep(1)
        if os.path.isfile(self.path+"PostScript.tar"): # we have a post tar to load
            ftp.cwd('/tmp')
            s = open(self.path+"PostScript.tar", 'rb')
            ftp.storbinary('STOR '+"PostScript.tar", s)
            s.close()
        ftp.quit()
        tn = self.startTelnet(msg['IP'])
        #tn.set_debuglevel(1)
        self.telComm(tn, "mv /mnt/networkNEW.ini /mnt/network.ini")
        self.telComm(tn, "cp /mnt/network.ini /mnt/factoryDefaults/network.ini")
        #self.telComm(tn, "cp /mnt/options.txt /mnt/factoryDefaults/options.txt")
        tn.write("/mnt/bin/vipRunStp & \n")
        time.sleep(0.5)
        tn.write("\n")
        tn.read_until('#')
        tn.read_until('#',1)
    ##########################
        if os.path.isfile(self.path+"PostScript.tar"): # We have PostScript.sh to run
            self.TxQ.put(['Running PostScript', msg['Mac']])
            self.telComm(tn, "tar -xf /tmp/PostScript.tar -C /")
            scriptDump = self.telComm(tn, "/tmp/PostScript.sh")
            msg1 += scriptDump.rstrip('#')
        inifile0 = self.telComm(tn, "cat /mnt/factory.ini")
        if len(self.verify['firmware']) > 0 and inifile0.find("firmware="+self.verify['firmware']) == -1:
            msg1 += "Firmware Error\n"
        if inifile0.find("macaddr="+msg['Mac']) == -1:
            msg1 += "Mac Address Error\n"
        inifile1 = self.telComm(tn, "cat /var/viprunstp.ver")
        if len(self.verify['viprunstp']) > 0 and inifile1.find(self.verify['viprunstp']) == -1:
            msg1 += "VipRunStp Error\n"
        inifile2 = self.telComm(tn, "cat /mnt/network.ini")
        if self.verify['DHCP']:
            if inifile2.find("dhcp=1") == -1:
                msg1 += "DHCP Setting Error\n"
        elif not self.verify['DHCP']:
            if inifile2.find("dhcp=0") == -1:
                msg1 +="DHCP Setting Error\n"
        inifile3 = self.telComm(tn, "cat /mnt/features.ini")
        if inifile3.find("No such file") == -1:
            if self.verify['IC_E'] and inifile3.find("InformaCast]\r\nstatus=Active") == -1:
                msg1 += "InformaCast Error\n"
            if self.verify['SYN_E'] and inifile3.find("synapps]\r\nstatus=Active") == -1:
                msg1 += "SynApps Error\n"
        else:
            if self.verify['IC_E']:
                inifile6 = self.telComm(tn, "cat /mnt/informacast.ini")
                if inifile6.find("enabled=1") == -1:
                    msg1 += "InformaCast Error\n"
                else:
                    self.telComm(tn, "cp /mnt/informacast.ini /mnt/factoryDefaults/informacast.ini")
            if self.verify['SYN_E']:
                inifile7 = self.telComm(tn, "cat /mnt/synapps.ini")
                if inifile7.find("enabled=1") == -1:
                    msg1 += "SynApps Error\n"
                else:
                    self.telComm(tn, "cp /mnt/synapps.ini /mnt/factoryDefaults/synapps.ini")
            inifile8 = self.telComm(tn, "cat /mnt/options.txt")
            if self.verify['IC_L'] and (inifile8.find(msg['Mac'].lower()) == -1 or inifile8.find("InformaCast=") == -1):
                msg1 += "InformaCast License Error\n"
            if self.verify['SYN_L'] and (inifile8.find(msg['Mac'].lower()) == -1 or inifile8.find("synapps=") == -1):
                msg1 += "SynApps License Error\n"
        inifile4 = self.telComm(tn, "cat /mnt/polycom.ini")
        if self.verify['POL_E'] and inifile4.find("enabled=1") == -1:
            msg1 += "PolyCom Error\n"
        elif self.verify['POL_E']:
            self.telComm(tn, "cp /mnt/polycom.ini /mnt/factoryDefaults/polycom.ini")
    # Here's the bf-device-type.ini verification part
     # inifile5 holds bf-device-type.ini. inifile0 holds factory.ini.
        inifile5 = self.telComm(tn, "cat /mnt/bf-device-type.ini")
        if inifile5.find("productName="+self.verify['product']) == -1:
            msg1 +="Product name not present in ini Error\n"
        if self.verify['flashers'] != '' and (inifile5.find("flashers="+self.verify['flashers']) == -1 or inifile0.find("flashers="+self.verify['flashers']) == -1):
            msg1 += "Flasher Error\n"
        if self.verify['inputs'] != '' and (inifile5.find("inputs="+self.verify['inputs']) == -1 or inifile0.find("inputs="+self.verify['inputs']) == -1):
            msg1 += "Number of inputs Error\n"
        if self.verify['channels'] != '' and (inifile5.find("channels="+self.verify['channels']) == -1 or inifile0.find("channels="+self.verify['channels']) == -1):
            msg1 += "Number of channels Error\n"
        if self.verify['relays'] != '' and (inifile5.find("relays="+self.verify['relays']) == -1 or inifile0.find("relays="+self.verify['relays']) == -1):
            msg1 += "Number of relays Error\n"
        if self.verify['inputConfiguration'] != '' and (inifile5.find("inputConfiguration="+self.verify['inputConfiguration']) == -1 or inifile0.find("inputconfiguration="+self.verify['inputConfiguration']) == -1):
            msg1 += "Number of inputConfiguration Error\n"
        if self.verify['bdtfirmware'] != '' and (inifile5.find("firmware="+self.verify['bdtfirmware']) == -1 or inifile0.find("firmware="+self.verify['bdtfirmware']) == -1):
            msg1 += "Firmware in bfdt Error\n"
    ##############
        if msg1 == "" or (msg1.find('RESULT: PASS') != -1 and msg1.find('Error') == -1):
            msg2 = ['PASS', msg['Mac'], msg1]
            try:
                tn.write(b'reboot\n')  # reboot on some devices terminates telnet
                tn.read_until('#',1)
                tn.close()
            except:
                pass
        else:
            msg2 = ['FAIL', msg['Mac'], msg1]
        self.TxQ.put(msg2)
        tn.close()


def DeviceInit(Mac, IP, RxQfromSM, TxQtoSM):
    """ Device process init for each device
    """
    DeviceMan = Device(Mac, IP, RxQfromSM, TxQtoSM)
    DeviceMan.runProcess()


