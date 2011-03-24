#!/usr/bin/env python

from PySide.QtCore import *
from PySide.QtGui import *
from devicebutton import *
import qt4reactor
import sys, tempfile, shutil, subprocess, os, platform, struct, tarfile, shlex
import locale, gettext, urllib2, json
from systeminfo import *
from httpunzip import *
from config import *

APP_NAME = 'novatool'

app = QApplication(sys.argv)
qt4reactor.install()

from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator, ReconnectingClientFactory
from twisted.internet.error import ConnectionRefusedError
from novacom import DeviceCollector, Novacom, NovacomDebug

import resources

jar = 'http://palm.cdnetworks.net/rom/pre2/p210sfr03082011/wrep210rod/webosdoctorp103ueuna-wr.jar'

PREWARE = 'http://get.preware.org/org.webosinternals.preware.ipk'
       
NOVA_WIN32  = 'resources/NovacomInstaller_x86.msi'
NOVA_WIN64  = 'resources/NovacomInstaller_x64.msi'
NOVA_MACOSX = 'resources/NovacomInstaller.pkg.tar.gz'

NOVA_LINUX32 = 'https://cdn.downloads.palm.com/sdkdownloads/2.1.0.519/sdkBinaries/palm-novacom_1.0.64_i386.deb'
NOVA_LINUX64 = 'https://cdn.downloads.palm.com/sdkdownloads/2.1.0.519/sdkBinaries/palm-novacom_1.0.64_amd64.deb'

REMOTE_TEMP = '/media/internal/.developer'

def chunk_read(response, total_size, chunk_size=8192, report_hook=None):
    bytes_so_far = 0
    data = ''

    while 1:
        chunk = response.read(chunk_size)
        bytes_so_far += len(chunk)

        if not chunk:
            break
    
        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)
        
        data = ''.join([data,chunk])

    return data

def ncuz_callback(p, msg):
    pass

def download_novacom_installer(platform, url, path):
    dl = None
    if platform == 'Windows':
        if is_win64():
            dl = http_unzip(url, [NOVA_WIN64], path, strip=True, ncuz_callback)
        else:
            dl = http_unzip(url, [NOVA_WIN32], path, strip=True, ncuz_callback)
    elif platform == 'Darwin':
        dl = http_unzip(url, [NOVA_MACOSX], path, strip=True, ncuz_callback)
    return dl[0]

def cmd_getFile(protocol, file):
    
    protocol.file__ = file
    protocol.transport.write('get file://%s\n' % (file))

def cmd_sendFile(protocol, file, dest):
    
    protocol.file__ = file
    protocol.transport.write('put file://%s\n' % (dest))
    
def cmd_memBoot(protocol, file):
    
    protocol.file__ = file
    protocol.transport.write('boot mem://%s\n')

def cmd_bootie_run(protocol, command):
    
    protocol.stdin__ = command
    protocol.transport.write('run file://\n')

def cmd_run(protocol, parse, command):
    if parse:
        args = shlex.split(command)
        for i in range(0,len(args)):
            args[i] = args[i].replace(' ','\\ ').replace('"','\\"')
        command = ' '.join(args)
    protocol.transport.write('run file://%s\n' % (command))
    
def cmd_installIPKG(protocol, file):
    f = open(file,'r')
    total_size = os.stat(file).st_size
    protocol.gui.state.setText('Stage 1: Loading IPK')
    protocol.data__ = chunk_read(f, total_size, report_hook=protocol.chunk_report)
    f.close()
    protocol.file__ = file.split('/')[-1]
    protocol.transport.write('put file://%s/%s\n' % (REMOTE_TEMP, protocol.file__))

def cmd_installIPKG_URL(protocol, url):
    req = urllib2.Request(url)
    f = urllib2.urlopen(req)
    total_size = int(f.info().getheader('Content-Length').strip())
    protocol.gui.state.setText('Stage 1: Downloading IPK')
    protocol.data__ = chunk_read(f, total_size, report_hook=protocol.chunk_report)
    f.close()
    protocol.file__ = url.split('/')[-1]
    protocol.transport.write('put file://%s/%s\n' % (REMOTE_TEMP, protocol.file__))
    
class NovacomGet(Novacom):
    
    file__ = None

    def __init__(self, gui):
        self.gui = gui
        
    def cmd_return(self, ret):
        self.transport.loseConnection()
                
    def cmd_stdout(self, data):
        msgBox = QMessageBox()
        msgBox.setText('The file has been retrieved successfully.')
        msgBox.setInformativeText('Do you want to save the file?')
        msgBox.setStandardButtons(QMessageBox.Discard | QMessageBox.Open | QMessageBox.Save )
        msgBox.setDefaultButton(QMessageBox.Save)
        msgBox.setDetailedText(data)
        ret = msgBox.exec_()
        
        if ret == QMessageBox.Save:
            filename = self.file__.split('/')[-1]
            filename = QFileDialog.getSaveFileName(self.gui, 'Save file', filename)
            print filename
            if filename[0]:
                f = open(str(filename[0]), 'w')
                f.write(data)
                f.close()
        elif ret == QMessageBox.Open:
            f = tempfile.NamedTemporaryFile(dir=self.gui.tempdir, delete=False)
            f.write(data)
            f.close()
            if self.gui.platform == 'Darwin':
                subprocess.call(['open',f.name])
            elif self.gui.platform == 'Windows':
                subprocess.call(['start',f.name])
            else:
                subprocess.call(['xdg-open',f.name])

class NovacomSend(Novacom):
    
    file__ = None

    def __init__(self, gui):
        self.gui = gui
        
    def cmd_status(self, msg):
        msgBox = QMessageBox()
        ok = False
        if msg == 'ok 0':
            datalen = len(self.file__)
            written = 0
            while written < datalen:
                towrite = datalen - written
                if towrite > self.PACKET_MAX:
                    towrite = self.PACKET_MAX
                self.transport.write(struct.pack('<IIII',self.MAGIC,1,towrite,0)+self.file__[written:written+towrite])
                written += towrite
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',0,0,0,0,0))
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',2,0,0,0,0))
            self.transport.loseConnection()
            ok = True
            if ok:
                msgBox.setText('The file has been sent successfully.')
            else:
                msgBox.setText('The file fail to be sent.')
                msgBox.setInformativeText(msg)
            msgBox.exec_()
        
class NovacomRun(Novacom):
    
    stdin__ = None

    def __init__(self, gui):
        self.gui = gui
        
    def cmd_return(self, ret):
        self.transport.loseConnection()

    def cmd_stdout_event(self, data):
        if self.gui:
            self.gui.output.setText(''.join([self.gui.output.toPlainText(),data]))
        else:
            sys.stdout.write(data)
        
    def cmd_stderr_event(self, data):
        if self.gui:
            self.gui.output.setText(''.join([self.gui.output.toPlainText(),data]))
        else:
            sys.stderr.write(data)
            
    def cmd_status(self, msg):
        if msg == 'ok 0' and self.stdin__:
            datalen = len(self.stdin__)
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,datalen,0)+self.stdin__)
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',0,0,0,0,0))
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',2,0,0,0,0))
                
        
class NovacomListDir(Novacom):

    def __init__(self, gui):
        self.gui = gui
        
    def cmd_stdout(self, data):
        fdata = []
        for line in data[:-1].split('\n'):
            space = line.find(' ')
            modes = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            id = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            owner = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            group = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            size = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            dow = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            month = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            day = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            time = line[:space]
            line = line[space:].lstrip()
            space = line.find(' ')
            year = line[:space]
            path = line[space:].lstrip()
            fdata.append((path, size, modes, '%s:%s' % (owner, group)))
        self.gui.fileListModel = RemoteFileModel(fdata, self.gui.fileListHeader, self.gui)
        self.gui.fileList.setModel(self.gui.fileListModel)
            

class NovacomInstallIPKG(Novacom):
    
    file__ = None
    data__ = None
    port__ = None
    
    def __init__(self, gui, port):
        self.gui = gui
        self.port = port
        
    def chunk_report(self, bytes_so_far, chunk_size, total_size):
        percent = int( float(bytes_so_far) / total_size * 100 )
        self.gui.progress.setValue(percent)
        
    def cmd_stderr_event(self, data):
        resp = json.loads(data[data.find(',')+1:].strip())
        if resp.has_key('returnValue') and resp['returnValue']:
            self.gui.state.setText('Stage 2')
            self.gui.progress.setValue(0)
        elif resp.has_key('status'):
            self.gui.state.setText('Stage 2: %s' % (resp['status']))
            self.gui.progress.setValue(self.gui.progress.value()+20)
            if resp['status'] == 'SUCCESS' or resp['status'].startswith('FAILED'):
                self.transport.loseConnection()
                self.gui.closeButton.setEnabled(True)
    
    def cmd_status(self, msg):
        if msg == 'ok 0' and self.port:
            datalen = len(self.data__)
            written = 0
            while written < datalen:
                towrite = datalen - written
                if towrite > self.PACKET_MAX:
                    towrite = self.PACKET_MAX
                self.transport.write(struct.pack('<IIII',self.MAGIC,1,towrite,0)+self.data__[written:written+towrite])
                written += towrite
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',0,0,0,0,0))
            self.transport.write(struct.pack('<IIII',self.MAGIC,1,20,2))
            self.transport.write(struct.pack('<IIIII',2,0,0,0,0))
            self.transport.loseConnection()
            c = ClientCreator(reactor, NovacomInstallIPKG, self.gui, None)
            d = c.connectTCP('localhost', self.port)
            d.addCallback(cmd_run, False, '/usr/bin/luna-send -i luna://com.palm.appinstaller/installNoVerify {\"subscribe\":true,\"target\":\"/media/internal/.developer/%s\",\"uncompressedSize\":0}' % (self.file__))

class NovacomDebugClient(NovacomDebug):
    
    def __init__(self, gui):
        self.gui = gui
        self.gui.debugProto = self
        
    def connectionMade(self):
        self.gui.updateStatusBar(True, 'Connected to novacomd.')
        ClientCreator(reactor, DeviceCollectorClient, self.gui).connectTCP('localhost', 6968)

    def connectionLost(self, reason):
        self.gui.updateStatusBar(False, 'Connection to novacomd lost.')
        for device in self.gui.deviceButtons:
            device.hide()
            self.gui.deviceBoxLayout.removeWidget(device)
            del device
            
        self.gui.activeDevice = None
        b = QLabel('<h2>No Connected Devices</h2>')
        b.setAlignment(Qt.AlignCenter)
        self.gui.deviceButtons = [b]
        self.gui.deviceBoxLayout.addWidget(self.gui.deviceButtons[0])

        
    def devicesChanged(self):
        ClientCreator(reactor, DeviceCollectorClient, self.gui).connectTCP('localhost', 6968)
        
class DeviceCollectorClient(DeviceCollector):
    
    def __init__(self, gui):
        self.gui = gui
        
    def connectionLost(self, reason):
        self.gui.devices = self.devices        
        ndev = len(self.devices)
        for device in self.gui.deviceButtons:
            device.hide()
            self.gui.deviceBoxLayout.removeWidget(device)
            del device
        
        noActive = True
        if ndev > 0:
            self.gui.deviceButtons = [None] * ndev 
            for i in range(0,ndev):
                self.gui.deviceButtons[i] = DeviceButton(self.gui, self.devices[i])
                if self.devices[i][1] == self.gui.activeDevice:
                    noActive = False
                    self.gui.deviceButtons[i].setActive(True)
                else:
                    self.gui.deviceButtons[i].setActive(False)
                self.gui.deviceBoxLayout.addWidget(self.gui.deviceButtons[i])
            if noActive:
                self.gui.activeDevice = self.devices[0][1]
                self.gui.deviceButtons[0].setActive(True)
            self.gui.setWidgetsEnabled(True)
            if self.gui.getActiveMode() == 'linux':
                self.gui.bootie.setIcon(QIcon(':/resources/icons/buttons/nuvola_apps_usb.png'))
                self.gui.bootie.setText('Recovery\nMode')
            elif self.gui.getActiveMode() == 'bootie':
                self.gui.bootie.setIcon(QIcon(':/resources/icons/buttons/restart.png'))
                self.gui.bootie.setText('Reset')
        else:
            self.gui.setWidgetsEnabled(False)
            self.gui.activeDevice = None
            self.gui.deviceButtons = [QLabel('<h2>No Connected Devices</h2>')]
            self.gui.deviceButtons[0].setAlignment(Qt.AlignCenter)
            self.gui.deviceBoxLayout.addWidget(self.gui.deviceButtons[0])

    def editLabel(self, label):
        label.setReadOnly(True)
        if label.text() == self.gui.devices[label.devid][3]:
            if self.gui.config['device_aliases'][self.gui.devices[label.devid][1]]:
                del self.gui.config['device_aliases'][self.gui.devices[label.devid][1]]
        else:
            self.gui.config['device_aliases'][self.gui.devices[label.devid][1]] = label.text()
        self.gui.save_config()

class DebugFactory(ReconnectingClientFactory):
    
    maxDelay = 10
    factor = 1.05
    
    def __init__(self, gui):
        self.gui = gui
    
    def buildProtocol(self, addr):
        self.resetDelay()
        return NovacomDebugClient(self.gui)
    
    def startedConnecting(self, connector):
        self.gui.updateStatusBar(False, 'Connecting to novacomd ...')

    def clientConnectionLost(self, connector, reason):
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        self.gui.updateStatusBar(False, 'Connection to novacomd lost!')

    def clientConnectionFailed(self, connector, reason):
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        self.gui.updateStatusBar(False, 'Connection to novacomd failed!')

class ProgressDlg(QDialog):

    def __init__(self, port, parent=None):
        super(ProgressDlg, self).__init__(parent)
        self.setModal(True)
        self.setMinimumSize(300,125)
        self.buttonBox = QDialogButtonBox()
        self.closeButton = self.buttonBox.addButton(self.buttonBox.Close)
        self.closeButton.setEnabled(False)
        QObject.connect(self.closeButton, SIGNAL('clicked()'), self.close)
        pglayout = QVBoxLayout()
        self.state = QLabel('Stage 1')
        self.state.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        pglayout.addWidget(self.state)
        pglayout.addWidget(self.progress)
        pglayout.addWidget(self.buttonBox)
        self.setLayout(pglayout)
        self.setWindowTitle('Progress')
        self.open()
        
class InstallDlg(QDialog):
    
    def __init__(self, port, parent=None):
        super(InstallDlg, self).__init__(parent)
        self.port = port
        self.path = None
        self.setModal(True)
        self.buttonBox = QDialogButtonBox()
        self.cancelButton = self.buttonBox.addButton(self.buttonBox.Cancel)
        self.installButton = self.buttonBox.addButton(self.buttonBox.Ok)
        self.installButton.setText('Install')
        QObject.connect(self.installButton, SIGNAL('clicked()'), self.install)
        QObject.connect(self.cancelButton, SIGNAL('clicked()'), self.close)
        cmdlayout = QHBoxLayout()
        self.cmdLabel = QLabel('File or URL:')
        self.cmd = QLineEdit()
        self.cmd.setMinimumWidth(500)
        self.dir = QPushButton()
        self.dir.setIcon(QIcon(':/resources/icons/buttons/folder.png'))
        QObject.connect(self.dir, SIGNAL('clicked()'), self.pickfile)
        cmdlayout.addWidget(self.cmdLabel)
        cmdlayout.addWidget(self.cmd)
        cmdlayout.addWidget(self.dir)
        layout = QVBoxLayout()
        layout.addLayout(cmdlayout)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.setWindowTitle("Install IPKG")
    
    def pickFile(self):
        if self.exec_():
            return self.path
        else:
            return None
        
    def install(self):
        text = str(self.cmd.text())
        if text:
            self.path = text
            self.setResult(True)
            self.done(True)
        
    def pickfile(self):
        self.cmd.setText(str(QFileDialog.getOpenFileName(self, caption='IPKG', filter='IPKG (*.ipk)')[0]))
        
class RemoteFileModel(QAbstractTableModel): 
    
    def __init__(self, datain, headerdata, parent=None, *args): 
        QAbstractTableModel.__init__(self, parent, *args) 
        self.arraydata = datain
        self.headerdata = headerdata
    
    def rowCount(self, parent):
        if self.arraydata:
            return len(self.arraydata)
        else:
            return 0
    
    def columnCount(self, parent):
        if self.arraydata:
            return len(self.arraydata[0])
        else:
            return 0 
    
    def data(self, index, role): 
        if not index.isValid(): 
            return None
        elif role != Qt.DisplayRole: 
            return None
        return self.arraydata[index.row()][index.column()] 
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[col]
        return None
    
class TypeSortDelegate(QStyledItemDelegate):
    
    def __init__(self, parent=None):
        super(TypeSortDelegate, self).__init__(parent)
        self.parent = parent

    def paint(self, painter, option, index):
        model = self.parent.getModel()
        offset = option.rect.height() / 2 - 8
        if model.arraydata[index.row()] and model.arraydata[index.row()][2][0] == 'd':
            painter.drawPixmap(option.rect.x()+4,option.rect.y()+offset,QPixmap(':/resources/icons/buttons/folder_blue.png'))
        else:
            painter.drawPixmap(option.rect.x()+4,option.rect.y()+offset,QPixmap(':/resources/icons/buttons/file.png'))
        option.rect.setX(option.rect.x()+20)
        QStyledItemDelegate.paint(self, painter, option, index)

class fileListEvent(QObject):
    
    def __init__(self, parent):
        super(fileListEvent, self).__init__(parent)
        self.parent = parent
    
    def eventFilter(self, object, event):

        if event.type() == QEvent.MouseButtonDblClick:
            idx = self.parent.fileList.selectedIndexes()[0].row()
            if self.parent.path == '/':
                self.parent.path = '%s%s' % (self.parent.path, self.parent.fileListModel.arraydata[idx][0])
            else:
                self.parent.path = '%s/%s' % (self.parent.path, self.parent.fileListModel.arraydata[idx][0])
            if self.parent.path != '/':
                if self.parent.fileListModel.arraydata[idx][0] == '.':
                    self.parent.path = self.parent.path[:-2]
                elif self.parent.fileListModel.arraydata[idx][0] == '..':
                    end = self.parent.path[:self.parent.path.rfind('/')].rfind('/')
                    self.parent.path = self.parent.path[:end]
            if self.parent.path == '' or self.parent.path == '/.':
                self.parent.path = '/'
            if self.parent.fileListModel.arraydata[idx][2][0] == 'd':
                self.parent.listDir()
            else:
                self.parent.setResult(True)
                self.parent.done(True)
        return False
  
class FileDlg(QDialog):
    
    def __init__(self, port, parent=None, path='/'):
        super(FileDlg, self).__init__(parent)
        self.port = port
        self.path = path
        
        self.setMinimumSize(500,400)
        
        self.delegate = TypeSortDelegate(self)
        
        self.fileList = QTableView()
        self.fileList.setItemDelegateForColumn(0,self.delegate)
        self.fileListHeader = ['Path','Size','Mode','Owner/Group']
        self.fileListModel = RemoteFileModel([], self.fileListHeader, self)
        self.fileList.setModel(self.fileListModel)
        self.fileList.setShowGrid(False)
        self.fileList.verticalHeader().setVisible(False)
        self.fileList.horizontalHeader().setStretchLastSection(True)
        self.fileList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fileList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.fileList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fileList.viewport().installEventFilter(fileListEvent(self))        
                
        buttonBox = QDialogButtonBox()
        closeButton = buttonBox.addButton(buttonBox.Cancel)
        installButton = buttonBox.addButton(buttonBox.Ok)
        #QObject.connect(installButton, SIGNAL('clicked()'), self.install)
        QObject.connect(closeButton, SIGNAL('clicked()'), self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.fileList)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        self.setWindowTitle("Pick File")
        
        self.listDir()
        
    def listDir(self):
        c = ClientCreator(reactor, NovacomListDir, self)
        d = c.connectTCP('localhost', self.port)
        d.addCallback(cmd_run, True, '/bin/ls -lae %s' % self.path)
        
    def getModel(self):
        return self.fileListModel
    
    def pickFile(self):
        if self.exec_():
            return self.path
        else:
            return None

class RunDlg(QDialog):
    
    def __init__(self, port, mode, parent=None):
        super(RunDlg, self).__init__(parent)
        self.gui = parent
        self.port = port
        self.mode = mode
        buttonBox = QDialogButtonBox()
        closeButton = buttonBox.addButton(buttonBox.Close)
        QObject.connect(closeButton, SIGNAL('clicked()'), self.close)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        font = self.output.font()
        font.setFamily('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        fm = QFontMetrics(font)
        self.output.setFont(font)
        self.output.setMinimumWidth(fm.widthChar('X')*80)
        self.output.setMinimumHeight(fm.widthChar('X')*39)
        cmdlayout = QHBoxLayout()
        cmdLabel = QLabel('Command:')
        self.cmd = QLineEdit()
        run = QPushButton('Run')
        QObject.connect(run, SIGNAL('clicked()'), self.run)
        cmdlayout.addWidget(cmdLabel)
        cmdlayout.addWidget(self.cmd)
        cmdlayout.addWidget(run)
        layout = QVBoxLayout()
        layout.addLayout(cmdlayout)
        layout.addWidget(self.output)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        self.setWindowTitle("Run Command")
        
    def run(self):
        text = str(self.cmd.text())
        if text:
            self.output.clear()
            if self.gui.getActiveMode() == 'linux':
                c = ClientCreator(reactor, NovacomRun, self)
                d = c.connectTCP('localhost', self.port)
                d.addCallback(cmd_run, True, text)
            elif self.gui.getActiveMode() == 'bootie':
                c = ClientCreator(reactor, NovacomRun, self)
                d = c.connectTCP('localhost', self.port)
                d.addCallback(cmd_bootie_run, text)
        
class MainWindow(QMainWindow):
    def __init__(self, config_file, config, platform, tempdir):
        super(MainWindow, self).__init__()

        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        langs = []
        lc, encoding = locale.getdefaultlocale()
        if (lc):
            langs = [lc]
        language = os.environ.get('LANGUAGE', None)
        if (language):
            langs += language.split(":")
        langs += ['it','de_CH','en_US']
        gettext.bindtextdomain(APP_NAME, self.local_path)
        gettext.textdomain(APP_NAME)
        self.lang = gettext.translation(APP_NAME, self.local_path
                                        , languages=langs, fallback = True)
        _ = self.lang.gettext
        
        self.config_file = config_file
        self.config = config
        
        self.setMinimumWidth(550)
        self.setMinimumHeight(475)
        
        self.debugProto = None
        
        self.platform = platform
        self.tempdir = tempdir
        
        self.devices = []
        self.activeDevice = None
        
        self.deviceButtons = []
        
        self.setWindowIcon(QIcon('novacomInstaller.ico'))
        
        screen = QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
        
        self.novatool = QWidget(self)
        self.hbox = QVBoxLayout()        
        self.main = QHBoxLayout()
        self.tabs = QTabWidget()
        
        self.deviceBox = QGroupBox(_('Devices'))
        self.deviceBoxLayout = QHBoxLayout()
        self.deviceBox.setLayout(self.deviceBoxLayout)
                       
        self.Fbuttons = QHBoxLayout()
        self.Kbuttons = QHBoxLayout()
        self.buttons = QHBoxLayout()
        
        self.getFileButton = QToolButton()
        self.getFileButton.setFixedWidth(96)
        self.getFileButton.setIcon(QIcon(':/resources/icons/buttons/document-import.png'))
        self.getFileButton.setText('Get\nFile')
        self.getFileButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.getFileButton.setIconSize(QSize(48,48))
        self.getFileButton.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.getFileButton, SIGNAL('clicked()'), self.getFile)
        self.Fbuttons.addWidget(self.getFileButton)
                
        self.sendFileButton = QToolButton()
        self.sendFileButton.setFixedWidth(96)
        self.sendFileButton.setIcon(QIcon(':/resources/icons/buttons/document-export.png'))
        self.sendFileButton.setText('Send\nFile')
        self.sendFileButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.sendFileButton.setIconSize(QSize(48,48))
        self.sendFileButton.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.sendFileButton, SIGNAL('clicked()'), self.sendFile)
        self.Fbuttons.addWidget(self.sendFileButton)
        
        self.memBootButton = QToolButton()
        self.memBootButton.setFixedWidth(96)
        self.memBootButton.setIcon(QIcon(':/resources/icons/buttons/media-flash.png'))
        self.memBootButton.setText('Mem\nBoot')
        self.memBootButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.memBootButton.setIconSize(QSize(48,48))
        self.memBootButton.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.memBootButton, SIGNAL('clicked()'), self.memBoot)
        self.Kbuttons.addWidget(self.memBootButton)

        self.bootie = QToolButton()
        self.bootie.setFixedWidth(96)
        if self.getActiveMode() == 'linux':
            self.bootie.setIcon(QIcon(':/resources/icons/buttons/nuvola_apps_usb.png'))
            self.bootie.setText('Recovery\nMode')
        elif self.getActiveMode() == 'bootie':
            self.bootie.setIcon(QIcon(':/resources/icons/buttons/restart.png'))
            self.bootie.setText('Reset')
        self.bootie.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.bootie.setIconSize(QSize(48,48))
        self.bootie.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.bootie, SIGNAL('clicked()'), self.bootieRecover)
        self.Kbuttons.addWidget(self.bootie)

        self.kernRescue = QToolButton()
        self.kernRescue.setFixedWidth(96)
        self.kernRescue.setIcon(QIcon(':/resources/icons/buttons/khelpcenter.png'))
        self.kernRescue.setText('Restore\nKernel')
        self.kernRescue.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.kernRescue.setIconSize(QSize(48,48))
        self.kernRescue.setStyleSheet("padding-bottom: 8")
        #QObject.connect(self.memBootButton, SIGNAL('clicked()'), self.memBoot)
        self.kernRescue.setEnabled(False)
        self.Kbuttons.addWidget(self.kernRescue)
        
        self.runCommandButton = QToolButton()
        self.runCommandButton.setFixedWidth(96)
        self.runCommandButton.setIcon(QIcon(':/resources/icons/buttons/application-x-executable-script.png'))
        self.runCommandButton.setText('Run\nCommand')
        self.runCommandButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.runCommandButton.setIconSize(QSize(48,48))
        self.runCommandButton.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.runCommandButton, SIGNAL('clicked()'), self.runCommand)
        self.buttons.addWidget(self.runCommandButton)
        
        self.termButton = QToolButton()
        self.termButton.setFixedWidth(96)
        self.termButton.setIcon(QIcon(':/resources/icons/buttons/utilities-terminal.png'))
        self.termButton.setText('Open\nTerminal')
        self.termButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.termButton.setIconSize(QSize(48,48))
        self.termButton.setStyleSheet("padding-bottom: 8")
        self.termButton.setEnabled(False)
        #QObject.connect(self.termButton, SIGNAL('clicked()'), self.runCommand)
        self.buttons.addWidget(self.termButton)
        
        self.FbuttonsW = QWidget()
        self.FbuttonsW.setLayout(self.Fbuttons)
        
        self.KbuttonsW = QWidget()
        self.KbuttonsW.setLayout(self.Kbuttons)
        
        self.buttonsW = QWidget()
        self.buttonsW.setLayout(self.buttons)
        
        self.basicOptions = QHBoxLayout()
        
        self.driver = QToolButton()
        self.driver.setFixedWidth(96)
        self.driver.setIcon(QIcon(':/resources/icons/buttons/system-software-update.png'))
        self.driver.setText('Novacom\nDriver')
        self.driver.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.driver.setIconSize(QSize(48,48))
        self.driver.setStyleSheet("padding-bottom: 8")
        self.basicOptions.addWidget(self.driver)
        QObject.connect(self.driver, SIGNAL('clicked()'), self.installDriver)
        
        self.preware = QToolButton()
        self.preware.setFixedWidth(96)
        self.preware.setIcon(QIcon(':/resources/icons/buttons/Icon_Preware.png'))
        self.preware.setText('Install\nPreware')
        self.preware.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.preware.setIconSize(QSize(48,48))
        self.preware.setStyleSheet("padding-bottom: 8")
        self.basicOptions.addWidget(self.preware)
        QObject.connect(self.preware, SIGNAL('clicked()'), self.installPreware)
        
        self.ipk = QToolButton()
        self.ipk.setFixedWidth(96)
        self.ipk.setIcon(QIcon(':/resources/icons/buttons/Icon_Box_Arrow.png'))
        self.ipk.setText('Install\nPackage')
        self.ipk.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ipk.setIconSize(QSize(48,48))
        self.ipk.setStyleSheet("padding-bottom: 8")
        QObject.connect(self.ipk, SIGNAL('clicked()'), self.installIPKG)
        
        self.basicOptions.addWidget(self.ipk)
        self.basics = QWidget()
        self.basics.setLayout(self.basicOptions)
        
        self.tabs.addTab(self.basics, 'Installers')
        self.tabs.addTab(self.FbuttonsW, 'File Actions')
        self.tabs.addTab(self.KbuttonsW, 'Kernel Actions')
        self.tabs.addTab(self.buttonsW, 'Terminal Actions')
        
        self.tabs.setMaximumHeight(150)
        
        self.hbox.addWidget(self.deviceBox)
        self.hbox.setStretch(0,1)
        self.hbox.addWidget(self.tabs)
                
        self.novatool.setLayout(self.hbox)
        self.setCentralWidget(self.novatool)
        self.setWindowTitle('Novatool 1.0')
        self.setUnifiedTitleAndToolBarOnMac(True)
        
        self.icon_disconneced = QPixmap(':/resources/icons/buttons/network-disconnect.png')
        self.icon_connected = QPixmap(':/resources/icons/buttons/network-connect.png')
        self.statusBar = QStatusBar()
        self.statusBar.setSizeGripEnabled(False)
        self.statusIcon = QLabel()
        self.statusMsg = QLabel()
        self.updateStatusBar(False, None)
        self.setStatusBar(self.statusBar)
                
        self.menuBar = QMenuBar()
        self.filemenu = QMenu('File')
        if self.platform == 'Darwin' or self.platform == 'Windows':
            self.driverInstallAction = QAction(self)
            self.driverInstallAction.setText('Install Novacom Driver')
            QObject.connect(self.driverInstallAction, SIGNAL('triggered()'), self.installDriver)
            self.filemenu.addAction(self.driverInstallAction)
            self.filemenu.addSeparator()
        self.quitAction = QAction(self)
        self.quitAction.setText('Quit')
        QObject.connect(self.quitAction, SIGNAL('triggered()'), self.quitApp)
        self.filemenu.addAction(self.quitAction)
        self.menuBar.addMenu(self.filemenu)
        self.aboutmenu = QMenu('Help')
        self.aboutmenu.addAction('About')
        self.menuBar.addMenu(self.aboutmenu)
        self.setMenuBar(self.menuBar)
        
        b = QLabel('<h2>No Connected Devices</h2>')
        b.setAlignment(Qt.AlignCenter)
        self.deviceButtons = [b]
        self.deviceBoxLayout.addWidget(self.deviceButtons[0])
        self.setWidgetsEnabled(False)
                        
        reactor.connectTCP('localhost', 6970, DebugFactory(self))
        
        self.show()
        
    def getActivePort(self):
        port = None
        for dev in self.devices:
            if self.activeDevice == dev[1]:
                port = dev[0]
                break
        return port

    def getActiveMode(self):
        mode = None
        for dev in self.devices:
            if self.activeDevice == dev[1]:
                mode = dev[3].split('-')[1]
                break
        return mode

    def save_config(self):
        save_config(self.config_file, self.config)
        
    def setWidgetsEnabled(self, bool):
        self.preware.setEnabled(bool)
        self.ipk.setEnabled(bool)
        self.getFileButton.setEnabled(bool)
        self.sendFileButton.setEnabled(bool)
        self.memBootButton.setEnabled(bool)
        self.runCommandButton.setEnabled(bool)
        self.bootie.setEnabled(bool)
        
    def installDriver(self):
        dl = download_novacom_installer(self.platform, jar, self.tempdir)
        if dl:
            if self.platform == 'Darwin':
                tf = tarfile.open(dl)
                tf.extractall(self.tempdir)
                tf.close() 
                subprocess.call(['open','-W',dl[:-7]])  
            else:
                subprocess.call(['msiexec','/i',dl])
        
    def quitApp(self):
        if self.debugProto:
            self.debugProto.transport.loseConnection()
        shutil.rmtree(self.tempdir)
        self.save_config()
        reactor.stop()
        QApplication.quit()
        
    def updateStatusBar(self, connected, msg):
        if connected:
            self.statusIcon.setPixmap(self.icon_connected)
        else:
            self.statusIcon.setPixmap(self.icon_disconneced)
        self.statusBar.addWidget(self.statusIcon)
        if msg:
            self.statusMsg.setText(msg)
            self.statusBar.addWidget(self.statusMsg)
        
    def getFile(self):
        port = self.getActivePort()
        if port:
            filename = FileDlg(port, self).pickFile()
            if filename:
                c = ClientCreator(reactor, NovacomGet, self)
                d = c.connectTCP('localhost', port)
                d.addCallback(cmd_getFile, str(filename))
                
    def sendFile(self):
        port = self.getActivePort()
        if port:
            infile = QFileDialog.getOpenFileName(self, caption='Send file')
            if infile[0]:
                outfile, ok = QInputDialog.getText(self, 'Send file', 'Path to file:')
                if ok:
                    f = open(str(infile[0]),'r')
                    data = f.read()
                    f.close()
                    c = ClientCreator(reactor, NovacomSend, self)
                    d = c.connectTCP('localhost', port)
                    d.addCallback(cmd_sendFile, data, str(outfile))        

    def memBoot(self):
        port = self.getActivePort()
        if port:
            infile = QFileDialog.getOpenFileName(self, caption='Mem boot kernel')
            if infile[0]:
                f = open(str(infile[0]),'r')
                data = f.read()
                f.close()
                c = ClientCreator(reactor, NovacomSend, self)
                d = c.connectTCP('localhost', port)
                d.addCallback(cmd_memBoot, data)
        
    def runCommand(self):
        port = self.getActivePort()
        mode = self.getActiveMode()
        if port and mode:
            dialog = RunDlg(port, mode, self)
            dialog.show()
            
    def bootieRecover(self):
        port = self.getActivePort()
        if port:
            if self.getActiveMode() == 'linux':
                c = ClientCreator(reactor, NovacomRun, None)
                d = c.connectTCP('localhost', port)
                d.addCallback(cmd_run, True, '/sbin/tellbootie recover')
            elif self.getActiveMode() == 'bootie':
                c = ClientCreator(reactor, NovacomRun, None)
                d = c.connectTCP('localhost', port)
                d.addCallback(cmd_bootie_run, 'reset')
        
    def installIPKG(self):
        port = self.getActivePort()
        if port:
            file = InstallDlg(port, self).pickFile()
            if file:
                c = ClientCreator(reactor, NovacomInstallIPKG, ProgressDlg(self), port)
                d = c.connectTCP('localhost', port)
                if file[:7] == 'http://':
                    d.addCallback(cmd_installIPKG_URL, file)
                else:
                    d.addCallback(cmd_installIPKG, file)
    
    def installPreware(self):
        port = self.getActivePort()
        if port:
            print 'Install preware'
            c = ClientCreator(reactor, NovacomInstallIPKG, ProgressDlg(self), port)
            d = c.connectTCP('localhost', port)
            d.addCallback(cmd_installIPKG_URL, PREWARE)
            
    def closeEvent(self, event=None):
        sys.exit(reactor.stop())
        
if __name__ == '__main__':
    
    platform = platform.system()
    tempdir = path = tempfile.mkdtemp()
    
    if platform == 'Windows':
        appdata = os.environ['APPDATA']
    else:
        _home = os.environ.get('HOME', '/')
        appdata = os.environ.get('XDG_CONFIG_HOME', os.path.join(_home, '.config'))
    novatool_config_home = os.path.join(appdata, 'novatool')    
    if not os.path.exists(novatool_config_home):
        os.makedirs(novatool_config_home)        
    config_file = os.path.join(novatool_config_home,"config")
    config = load_config(config_file)
    
    mainWin = MainWindow(config_file, config, platform, tempdir)
    sys.exit(reactor.run())
