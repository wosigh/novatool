from PySide.QtCore import *
from PySide.QtGui import *
import resources

DEVICE_ICONS = {
                'castle-linux':':/resources/icons/devices/Icon_Device_Pre1_128.png',
                'roadrunner-linux':':/resources/icons/devices/Icon_Device_Pre2_128.png',
                'pixie-linux':':/resources/icons/devices/Icon_Device_Pixi1_128.png',
                }

class deviceEvent(QObject):
    
    def __init__(self, parent):
        super(deviceEvent, self).__init__(parent)
        self.gui = parent
        
    def eventFilter(self, object, event):
        
        if event.type() == QEvent.MouseButtonPress:
            for i in range(0, len(self.gui.deviceButtons)):
                if self.gui.deviceButtons[i] == object:
                    self.gui.deviceButtons[i].setActive(True)
                    self.gui.activeDevice = self.gui.devices[i][1]
                else:
                    self.gui.deviceButtons[i].setActive(False)
            return True
        return False

class deviceLabelEvent(QObject):
    
    def __init__(self, parent):
        super(deviceLabelEvent, self).__init__(parent)
    
    def eventFilter(self, object, event):

        if event.type() == QEvent.MouseButtonPress:
            object.setReadOnly(False)
            return True
        return False

class DeviceButton(QFrame):
    
    def __init__(self, gui, device):
        super(DeviceButton, self).__init__()
        
        self.gui = gui
        self.device = device
        
        self.installEventFilter(deviceEvent(self.gui))
        
        self.isActive = False
        
        self.setLineWidth(4)
        self.setFixedSize(196,196)
        
        self.layout = QVBoxLayout()
        
        self.icon = QPixmap(DEVICE_ICONS[self.device[3]])
        self.iconLabel = QLabel()
        self.iconLabel.setPixmap(self.icon)
        self.iconLabel.setAlignment(Qt.AlignCenter)
        
        self.nameLabel = QLineEdit()
        self.nameLabel.installEventFilter(deviceLabelEvent(self.gui))
        self.nameLabel.setReadOnly(True)
        self.nameLabel.setStyleSheet('background: transparent;')
        self.nameLabel.setFrame(False)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        if self.gui.config['device_aliases'].has_key(self.device[1]):
            self.nameLabel.setText(self.gui.config['device_aliases'][self.device[1]])
        else:
            self.nameLabel.setText(self.device[3])        
        QObject.connect(self.nameLabel, SIGNAL('returnPressed()'), self.nameLabelChanged)
                    
        self.layout.addWidget(self.iconLabel)
        self.layout.addWidget(self.nameLabel)
        
        self.setLayout(self.layout)
        
    def setActive(self, bool):
        self.isActive = bool
        if bool:
            self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        else:
            self.setFrameStyle(QFrame.Panel | QFrame.Raised)
            
    def nameLabelChanged(self):
        self.nameLabel.setReadOnly(True)
        if self.nameLabel.text() == self.device[3]:
            if self.gui.config['device_aliases'][self.device[1]]:
                del self.gui.config['device_aliases'][self.device[1]]
        else:
            self.gui.config['device_aliases'][self.device[1]] = self.nameLabel.text()
        self.gui.save_config()