import os
import sys
from multiprocessing import Process
from queueManager import QueMgr

       
class ValProcess:
    def __init__(self, target):
        self.que = QueMgr()
        queProc = self.que.createRxPair()
        self.proc = Process(target=target, args=(queProc,))
        self.proc.start()
       
    def sendTo(self, msg):
        self.que.sendTo(msg)
        
    def rxFrom(self):
        return self.que.rxFrom()
