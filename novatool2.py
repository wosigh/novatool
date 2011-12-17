#!/usr/bin/env python

import sys

from PySide.QtCore import *
from PySide.QtGui import *
import qt4reactor

app = QApplication(sys.argv)
qt4reactor.install()

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.internet.defer import Deferred
from novacom2 import Novacom

PORT = 59419

def novaCommand(protocol, command):
    protocol.transport.write('%s\n' % (command))
    return protocol.deferred_status

class MainWindow(QMainWindow):
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.novatool = QWidget(self)
        self.hbox = QHBoxLayout()
        self.getButton = QPushButton('Get File')
        QObject.connect(self.getButton, SIGNAL('clicked()'), self.getPressed)
        self.sendButton = QPushButton('Send File')
        QObject.connect(self.sendButton, SIGNAL('clicked()'), self.sendPressed)
        self.hbox.addWidget(self.getButton)
        self.hbox.addWidget(self.sendButton)
        self.novatool.setLayout(self.hbox)
        self.setCentralWidget(self.novatool)
        
        self.show()
        self.activateWindow()
        self.raise_()
        
    def getPressed(self):
        print 'getPressed'
        d = ClientCreator(reactor, Novacom).connectTCP('localhost', PORT)
        d = d.addCallback(novaCommand, 'get file://etc/palm-build-info')
        d.addCallback(lambda m: sys.stdout.write(m))
        #r.addCallback(lambda r, m: sys.stdout.write(r+'\n'+m))
        
    def sendPressed(self):
        print 'sendPressed'
        
               

if __name__ == '__main__':
    
    m = MainWindow()
    reactor.run()