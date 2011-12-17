import struct, sys

from twisted.internet import protocol
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred

class Novacom(Protocol):
    
    MAGIC = 0xdecafbad
    PACKET_MAX = 16384
    
    data = []
    buffer = ''
    ret = None
    oob = None
    header = None
    status = False
    
    def __init__(self):
        self.deferred_status = Deferred()
        self.deferred_return = Deferred()
            
    def dataReceived(self, data):
        self.buffer = ''.join([self.buffer, data])
        while len(self.buffer) > 0:
            if self.status:
                if not self.header and len(self.buffer) > 15:
                    self.header = struct.unpack('<IIII', self.buffer[0:16])
                    self.buffer = self.buffer[16:]
                if self.header: 
                    if len(self.buffer) >= self.header[2]:
                        if self.header[3] == 0:
                            new = self.buffer[:self.header[2]]
                            self.event_stdout(new)
                            self.data.append((0,new))
                            self.buffer = self.buffer[self.header[2]:]
                            self.header = None
                        elif self.header[3] == 1:
                            new = self.buffer[:self.header[2]]
                            self.event_stderr(new)
                            self.data.append((1,new))
                            self.buffer = self.buffer[self.header[2]:]
                            self.header = None
                        elif self.header[3] == 2:
                            self.oob = struct.unpack('<IIIII', self.buffer[:self.header[2]])
                            self.buffer = self.buffer[self.header[2]:]
                            self.header = None
                    else:
                        break
                if self.oob and self.oob[0] == 0:
                    if self.oob[1] == 1:
                        self.event_stdout_closed()
                    elif self.oob[1] == 2:
                        self.event_stderr_closed()
                    self.oob = None
                if self.oob and self.oob[0] == 2:
                    self.deferred_return.callback((self.oob[1], self.data))
                    self._reset()
            else:
                i = self.buffer.find('\n')
                msg = self.buffer[:i]
                self.deferred_status.callback(msg)
                if msg == 'ok 0':
                    self.status = True
                    self.buffer = self.buffer[i+1:]
                else:
                    self._reset()
    
    def event_stdout(self, data):
        pass
    
    def event_stderr(self, data):
        pass
    
    def event_stdout_closed(self):
        pass
    
    def event_stderr_closed(self):
        pass
        
    def _reset(self):
        self.stdout = ''
        self.stderr = ''
        self.buffer = ''
        self.oob = None
        self.header = None
        self.status = False
               
class DeviceCollector(Protocol):
    
    def __init__(self):
        self.devices = []
        self.finished = Deferred()
    
    def dataReceived(self, data):
        for d in data[:-1].split('\n'):
            d = d.split(' ')
            self.devices.append((int(d[0]), d[1], d[2], d[3]))
            
    def connectionLost(self, reason):
        self.finished.callback(self.devices)