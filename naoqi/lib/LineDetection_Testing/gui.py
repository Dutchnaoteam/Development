import sys, cv
from PyQt4 import QtCore, QtGui
from linedetection import Ui_MainWindow
import linedetector as l

class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.scene = QtGui.QGraphicsScene()
        self.scene2 = QtGui.QGraphicsScene()

        QtCore.QObject.connect(self.ui.buttonLoad, QtCore.SIGNAL("clicked()"),
                self.onLoad)
        QtCore.QObject.connect(self.ui.buttonChoose, QtCore.SIGNAL("clicked()"),
                self.onDisplay)
        QtCore.QObject.connect(self.ui.buttonHough, QtCore.SIGNAL("clicked()"),
                self.onHough)
        QtCore.QObject.connect(self.ui.lineRho, QtCore.SIGNAL("returnPressed()"),
                self.onHough)
        QtCore.QObject.connect(self.ui.lineTheta, QtCore.SIGNAL("returnPressed()"),
                self.onHough)
        QtCore.QObject.connect(self.ui.lineThreshold,
                QtCore.SIGNAL("returnPressed()"), self.onHough)
        QtCore.QObject.connect(self.ui.buttonReload, QtCore.SIGNAL("clicked()"),
                self.onReload)

    def onLoad(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, caption="Open File",
                directory=".")
        self.ui.lineFile.setText(filename)

    def onDisplay(self):
        self.scene.addPixmap(QtGui.QPixmap(self.ui.lineFile.text()))
        self.ui.graphicsMain.setScene(self.scene)

    def onReload(self):
        reload(l)
        print "Reloaded modules"

    def onHough(self):
        imgFile = str(self.ui.lineFile.text())
        drho = float(self.ui.lineRho.text())
        dtheta = float(self.ui.lineTheta.text())
        threshold = int(self.ui.lineThreshold.text())

        lineImg, threshed = l.find_lines(imgFile, drho, dtheta, threshold,
                self.ui.checkCanny.isChecked(),
                self.ui.checkSmoothing.isChecked())
        cv.SaveImage('main.png', lineImg)
        cv.SaveImage('threshed.png', threshed)

        self.scene.addPixmap(QtGui.QPixmap('main.png'))
        self.ui.graphicsMain.setScene(self.scene)
        self.scene2.addPixmap(QtGui.QPixmap('threshed.png'))
        self.ui.graphicsThreshed.setScene(self.scene2)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())
