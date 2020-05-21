# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qcm.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets , uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import cv2 
from cv2 import aruco
import qimage2ndarray # for a memory leak,see gist
import sys
import os 
from pathlib import Path


import time

from OMRutils import load_answers , read_qrcode , get_ordered_answers , preprocess , detect_roi 
from make_quizz import make_quizz_doc

try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
except Exception as E:
    pass

nb_questions = 10
nbt = 30
order_code = None
code = None
score=None
aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_250)
parameters =  aruco.DetectorParameters_create()
answers = load_answers()
quizzpath = 'quizz.xlsx'
class quizzthread(QThread):
    done = pyqtSignal(int)
    def run(self):        
        make_quizz_doc(nb_questions , nbt , quizzpath)
        self.done.emit(0)

class OptionWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('opwin.ui' , self)
       
class DFThread(QThread):
    changePixmap = pyqtSignal(QImage)
    showmarked = pyqtSignal(QImage)
    def run(self):
            while cap.isOpened():
                global code , order_code , score
                
                ret, f = cap.read()  
                org = f.copy()
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)    
                
                f , order_code = read_qrcode(cv2  , f)  

                
                try:        
                    if order_code != None and code != order_code :
                        code = order_code

                    cv2.putText(f , "sequence = {}".format(code) , (10,20) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , (255 , 255 ,0))   
                
                    if code != None: 
                        if len(corners) == 4:        
                            f , roi = detect_roi(cv2, org , f , corners , ids)           
                            score , marked = preprocess(cv2 , roi , get_ordered_answers(code , answers , nb_questions) , nb_questions )   
                            cv2.putText(f , "score = {}".format(score) , (10,35) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , (255 , 255 ,0))
                            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB) 
                            self.showmarked.emit(qimage2ndarray.array2qimage(roi))
                            
                except Exception as E:        
                    pass  

                f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)      
                self.changePixmap.emit(qimage2ndarray.array2qimage(f))


def change_source(source):
    global cap
    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

  
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 720)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.cam = QtWidgets.QLabel(self.centralwidget)
        self.cam.setGeometry(QtCore.QRect(10, 30, 800, 600))
        self.cam.setObjectName("cam")
        self.source_lab = QtWidgets.QLabel(self.centralwidget)
        self.source_lab.setGeometry(QtCore.QRect(10, 650, 47, 16))
        self.source_lab.setObjectName("source_lab")
        self.ipsource = QtWidgets.QLineEdit(self.centralwidget)
        self.ipsource.setGeometry(QtCore.QRect(70, 650, 451, 20))
        self.ipsource.setObjectName("ipsource")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(830, 20, 131, 16))
        self.label.setObjectName("label")
        self.qrcode = QtWidgets.QLabel(self.centralwidget)
        self.qrcode.setGeometry(QtCore.QRect(830, 40, 281, 16))
        self.qrcode.setObjectName("qrcode")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(830, 80, 47, 13))
        self.label_2.setObjectName("label_2")
        self.score = QtWidgets.QLabel(self.centralwidget)
        self.score.setGeometry(QtCore.QRect(830, 80, 320, 280))
        self.score.setObjectName("score")
        self.setipcam = QtWidgets.QPushButton(self.centralwidget)
        self.setipcam.setGeometry(QtCore.QRect(540, 650, 161, 23))
        self.setipcam.setObjectName("setipcam")
        self.setipcam.clicked.connect(self.set_ip_cam)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1112, 21))
        self.menubar.setObjectName("menubar")       
        #menu fichier
        self.menuFichier = QtWidgets.QMenu(self.menubar)
        self.menuFichier.setObjectName("menuFichier")
        self.quitter = QtWidgets.QAction(MainWindow)
        self.quitter.setObjectName("quitter")
        self.excel = QtWidgets.QAction(MainWindow)
        self.excel.setObjectName("excel")
        self.menuFichier.addAction(self.excel)
        self.menuFichier.addAction(self.quitter)        
        self.excel.triggered.connect(self.openfileaction)
        self.quitter.triggered.connect(self.quit)
        #menu configuration
        self.menuconfig = QtWidgets.QMenu(self.menubar)
        self.menuconfig.setObjectName("menuconfig")
        self.configurer = QtWidgets.QAction(MainWindow)
        self.configurer.setObjectName("configurer")
        self.menuconfig.addAction(self.configurer)
        self.configurer.triggered.connect(self.configaction)
        #menu générer
        self.menuG_n_rer = QtWidgets.QMenu(self.menubar)
        self.menuG_n_rer.setObjectName("menuG_n_rer")
        MainWindow.setMenuBar(self.menubar)
        #menu about
        self.menuabout = QtWidgets.QMenu(self.menubar)
        self.menuabout.setObjectName("menuabout")
        MainWindow.setMenuBar(self.menubar)
        self.help = QtWidgets.QAction(MainWindow)
        self.help.setObjectName("help")
        self.menuabout.addAction(self.help)
        self.menuabout.triggered.connect(self.msghelp)


        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionfichier_qcm = QtWidgets.QAction(MainWindow)
        self.actionfichier_qcm.setObjectName("actionfichier_qcm")
        self.menuG_n_rer.addAction(self.actionfichier_qcm)
        self.menuG_n_rer.triggered.connect(self.quizz_gen)
        #add menus here
        self.menubar.addAction(self.menuFichier.menuAction())
        self.menubar.addAction(self.menuG_n_rer.menuAction())
        self.menubar.addAction(self.menuconfig.menuAction())
        self.menubar.addAction(self.menuabout.menuAction())
        #lcd score display
        self.lcd = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcd.setObjectName("lcd")
        self.lcd.setGeometry(QtCore.QRect(830, 580, 200, 80))
        self.retranslateUi(MainWindow)

        #add visual widgets before this line
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        #set the cam feed
        feedthread = DFThread(MainWindow)
        feedthread.changePixmap.connect(lambda p: self.setimage(p))
        feedthread.showmarked.connect(lambda p: self.showmarked(p))
        feedthread.start()


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "quizz scanner 0.7"))
        self.cam.setText(_translate("MainWindow", "TextLabel"))
        self.source_lab.setText(_translate("MainWindow", "Source"))
        self.label.setText(_translate("MainWindow", "sequence"))
        self.qrcode.setText(_translate("MainWindow", "TextLabel"))
        self.label_2.setText(_translate("MainWindow", "score"))
        self.score.setText(_translate("MainWindow", ""))
        self.setipcam.setText(_translate("MainWindow", "ouvrir ip cam"))
        self.menuFichier.setTitle(_translate("MainWindow", "Fichier"))
        self.menuG_n_rer.setTitle(_translate("MainWindow", "Générer"))
        self.menuconfig.setTitle(_translate("MainWindow", "options"))
        self.menuabout.setTitle(_translate("MainWindow", "about"))
        self.actionfichier_qcm.setText(_translate("MainWindow", "fichier qcm"))
        self.quitter.setText(_translate("MainWindow", "Quitter"))        
        self.excel.setText(_translate("MainWindow", "ouvrir le fichier excel"))
        self.quitter.setShortcut(_translate("MainWindow", "Esc"))        
        self.configurer.setText(_translate("MainWindow", "configurer"))
        self.configurer.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.help.setText(_translate("MainWindow", "help"))
        self.lcd.display(0)
    def set_ip_cam(self):        
        change_source(self.ipsource.text())
        self.statusbar.showMessage("source video : {}".format(self.ipsource.text()))
    
    def openfileaction(self):
        global quizzpath 
        home_dir = str(Path.home())
        fil = "xlsx(*.xlsx)"
        fname = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget, 'Open file', home_dir,fil) 
        quizzpath = os.path.dirname(fname[0])        
        
    
    def msghelp(self):
        print(QThreadPool.globalInstance().maxThreadCount())
        QtWidgets.QMessageBox.about(self.centralwidget,"About quizz scanner","version 0.7 \ncontact: boujrida.mohamedoussama@gmail.com\n")
    
    
    def quizz_gen(self):
        try:  
            buttonReply = QtWidgets.QMessageBox.question(self.centralwidget,'Générer ', "Générer "+str(nbt)+" tests avec "+ str(nb_questions) +" questions?(changer les valeurs dans le menu options)", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)                    
            if buttonReply == QtWidgets.QMessageBox.Yes:
                Qmaker = quizzthread(MainWindow)
                Qmaker.done.connect(lambda p: self.quizzdone(p))
                Qmaker.start()
                self.statusbar.showMessage("Génération en cours ...")
            else:
                pass
            
        except Exception as e:
            print(e)
            self.statusbar.showMessage(str(e))


    @pyqtSlot(int)
    def quizzdone(self , x):
        self.statusbar.showMessage("fichier quizz.docx prêt ")

    def configaction(self):
        global nb_questions
        self.opWin = OptionWindow()
        self.opWin.setWindowTitle("options de configuration")
        self.confbtn = self.opWin.findChild(QtWidgets.QPushButton ,'setnbq')
        self.opWin.findChild(QtWidgets.QLineEdit , 'nbq').setText(str(nb_questions))        
        self.opWin.findChild(QtWidgets.QLineEdit , 'nbt').setText(str(nbt))        
        self.confbtn.clicked.connect(self.set_op)
        self.opWin.show()

    def set_op(self):
        global nb_questions , nbt        
        nbt = int(self.opWin.findChild(QtWidgets.QLineEdit , 'nbt').text()) 
        nb_questions = int(self.opWin.findChild(QtWidgets.QLineEdit , 'nbq').text()) 
        self.opWin.close() 
    
    @pyqtSlot(QImage)
    def setimage(self , f ):       
        #the process result is the image to show
        ui.cam.setPixmap(QPixmap.fromImage(f))
        ui.qrcode.setText(code)
        ui.qrcode.update()
        

    @pyqtSlot(QImage)
    def showmarked(self , f ):       
        #the process result is the image to show
        ui.score.setGeometry(QtCore.QRect(830, 150, f.width(),f.height()))
        ui.score.setPixmap(QPixmap.fromImage(f)) 
        ui.lcd.display(score)

    def quit(self):
        sys.exit(app.exec_())  
        

if __name__ == "__main__":        
   
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()    
    ui.setupUi(MainWindow)
    MainWindow.setFixedSize(1150,720)  
    MainWindow.show()   
    sys.exit(app.exec_())