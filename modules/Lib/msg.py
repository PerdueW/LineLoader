#!/usr/bin/python

class Msg:
   """ This class is used as Queue container being passed between sysMng, GUI and testMng.
    The format of the massage being passed through the queues is 
        name - name of the message, used to indentify what type of the message it is
        dictionary - dictonary list of information being passes 
   """
   def __init__(self, name="message",myDict = None):
      self._name = name
      if myDict is None:
         self.myDict = {}
      else:
         self.myDict = myDict.copy()
   def setMsgType(self, msgType):
      self._name = msgType
   
   def getMsgType(self):
      return self._name

   def addItem(self, name, value):
      self.myDict[name] = value

   def getItem(self, name):
      if name in self.myDict.keys():
         return self.myDict[name]
      else:
         return None

   def __str__(self):
      printStr = "MSG("+self._name+")\n"
      for key, value in self.myDict.iteritems():
         printStr += "   " + key + " : "
         if type(value).__name__ == 'str':
            printStr += value
         elif type(value).__name__ == 'int':
            printStr += str(value)
         elif type(value).__name__ == 'list':
            printStr += '['
            for x in value:
               if type(x).__name__ == 'str':
                  printStr += x
               elif type(x).__name__ == 'int':
                  printStr += str(x)
               elif type(x).__name__ == 'list':
                  printStr += '[]'
               else:
                  printStr += '--'
               printStr += ','
            printStr += ']'
         else:
            printStr += str(type(value))
         printStr += '\n'
         
      return printStr 

