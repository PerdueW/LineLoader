import os
import sys
from multiprocessing import Queue


class QueMgr:
    def __init__(self, Rx=None, Tx=None):
        if Rx is None:
            self.rxQ = Queue()
        else:
            self.rxQ = Rx
            
        if Tx is None:
            self.txQ = Queue()
        else:
            self.txQ = Tx
            
    def sendTo(self, msg):
        self.txQ.put(msg)
        
    def rxFrom(self):
        if not self.rxQ.empty():
            return self.rxQ.get()
        else:
            return None         
 
    def createRxPair(self):
        return QueMgr(self.txQ, self.rxQ)
