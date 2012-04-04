# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'linedetection.ui'
#
# Created: Tue Apr  3 22:40:48 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.graphicsMain = QtGui.QGraphicsView(self.centralwidget)
        self.graphicsMain.setObjectName(_fromUtf8("graphicsMain"))
        self.horizontalLayout_2.addWidget(self.graphicsMain)
        self.graphicsThreshed = QtGui.QGraphicsView(self.centralwidget)
        self.graphicsThreshed.setObjectName(_fromUtf8("graphicsThreshed"))
        self.horizontalLayout_2.addWidget(self.graphicsThreshed)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.lineFile = QtGui.QLineEdit(self.centralwidget)
        self.lineFile.setReadOnly(False)
        self.lineFile.setObjectName(_fromUtf8("lineFile"))
        self.gridLayout_2.addWidget(self.lineFile, 0, 0, 1, 2)
        self.buttonLoad = QtGui.QPushButton(self.centralwidget)
        self.buttonLoad.setObjectName(_fromUtf8("buttonLoad"))
        self.gridLayout_2.addWidget(self.buttonLoad, 1, 0, 1, 1)
        self.buttonChoose = QtGui.QPushButton(self.centralwidget)
        self.buttonChoose.setMinimumSize(QtCore.QSize(699, 0))
        self.buttonChoose.setObjectName(_fromUtf8("buttonChoose"))
        self.gridLayout_2.addWidget(self.buttonChoose, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.lineRho = QtGui.QLineEdit(self.centralwidget)
        self.lineRho.setObjectName(_fromUtf8("lineRho"))
        self.gridLayout.addWidget(self.lineRho, 0, 1, 1, 1)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.lineTheta = QtGui.QLineEdit(self.centralwidget)
        self.lineTheta.setObjectName(_fromUtf8("lineTheta"))
        self.gridLayout.addWidget(self.lineTheta, 1, 1, 1, 1)
        self.lineThreshold = QtGui.QLineEdit(self.centralwidget)
        self.lineThreshold.setObjectName(_fromUtf8("lineThreshold"))
        self.gridLayout.addWidget(self.lineThreshold, 2, 1, 1, 1)
        self.checkCanny = QtGui.QCheckBox(self.centralwidget)
        self.checkCanny.setObjectName(_fromUtf8("checkCanny"))
        self.gridLayout.addWidget(self.checkCanny, 3, 0, 1, 1)
        self.checkSmoothing = QtGui.QCheckBox(self.centralwidget)
        self.checkSmoothing.setObjectName(_fromUtf8("checkSmoothing"))
        self.gridLayout.addWidget(self.checkSmoothing, 4, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonHough = QtGui.QPushButton(self.centralwidget)
        self.buttonHough.setObjectName(_fromUtf8("buttonHough"))
        self.verticalLayout.addWidget(self.buttonHough)
        self.buttonReload = QtGui.QPushButton(self.centralwidget)
        self.buttonReload.setObjectName(_fromUtf8("buttonReload"))
        self.verticalLayout.addWidget(self.buttonReload)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 20))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonLoad.setText(QtGui.QApplication.translate("MainWindow", "Load", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonChoose.setText(QtGui.QApplication.translate("MainWindow", "Choose", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "threshold", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "drho", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "dtheta", None, QtGui.QApplication.UnicodeUTF8))
        self.checkCanny.setText(QtGui.QApplication.translate("MainWindow", "Use canny", None, QtGui.QApplication.UnicodeUTF8))
        self.checkSmoothing.setText(QtGui.QApplication.translate("MainWindow", "Use smoothing", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonHough.setText(QtGui.QApplication.translate("MainWindow", "Hough it", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonReload.setText(QtGui.QApplication.translate("MainWindow", "Reload module", None, QtGui.QApplication.UnicodeUTF8))

