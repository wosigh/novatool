import struct, sys

from twisted.internet import protocol
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred

class NovacomDebug(LineReceiver):
    
    delimiter = '\n'
    
    def lineReceived(self, line):
        tmp = line
        i = tmp.find(']')
        date = tmp[:i+1]
        tmp = tmp[i+2:]
        i = tmp.find(' ')
        cmd = tmp[:i].split(':')[0]
        if cmd == 'removing' or cmd == 'dev':
            self.devicesChanged()
        self.event_debug(line)
        
    def event_debug(self, msg):
        pass
            
    def devicesChanged(self):
        pass

class Novacom(Protocol):
    
    MAGIC = 0xdecafbad
    PACKET_MAX = 16384
    
    stdout = ''
    stderr = ''
    buffer = ''
    ret = None
    oob = None
    header = None
    status = False
        
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
                            self.cmd_stdout_event(new)
                            self.stdout = ''.join([self.stdout, new])
                            self.buffer = self.buffer[self.header[2]:]
                            self.header = None
                        elif self.header[3] == 1:
                            new = self.buffer[:self.header[2]]
                            self.cmd_stderr_event(new)
                            self.stderr = ''.join([self.stderr, new])
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
                        self.cmd_stdout(self.stdout)
                    elif self.oob[1] == 2:
                        self.cmd_stderr(self.stderr)
                    self.oob = None
                if self.oob and self.oob[0] == 2:
                    self.cmd_return(self.oob[1])
                    self._reset()
            else:
                i = self.buffer.find('\n')
                msg = self.buffer[:i]
                if msg == 'ok 0':
                    self.cmd_status(msg)
                    self.status = True
                    self.buffer = self.buffer[i+1:]
                else:
                    self.error(msg)
                    self._reset()
                    
    def cmd_status(self, msg):
        pass
                
    def cmd_return(self, ret):
        pass
    
    def cmd_stdout_event(self, data):
        pass
    
    def cmd_stderr_event(self, data):
        pass
                
    def cmd_stdout(self, data):
        pass
        
    def cmd_stderr(self, data):
        pass
    
    def error(self, error):
        pass
        
    def _reset(self):
        self.stdout = ''
        self.stderr = ''
        self.buffer = ''
        self.oob = None
        self.header = None
        self.status = False
        
class DeviceCollector(Protocol):
    
    def __init__(self, finished):
        self.devices = []
        self.finished = finished
    
    def dataReceived(self, data):
        for d in data[:-1].split('\n'):
            d = d.split(' ')
            self.devices.append((int(d[0]), d[1], d[2], d[3]))
            
    def connectionLost(self, reason):
        self.finished.callback(self.devices)