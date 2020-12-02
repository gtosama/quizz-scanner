import sys
import os 


from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import cv2 
import qimage2ndarray # for a memory leak,see gist

from OMRutils import shadow_remover , load_answers , read_qrcode , get_ordered_answers , preprocess , detect_roi , detect_roi2 
from make_quizz import make_quizz_doc

import pandas as pd
from excelTableModel import CustomTableModel



nb_questions = 10
nbt = 30
order_code = None
code = None
score=0

quizzpath = str(Path().absolute())

answers = load_answers(quizzpath)
print(quizzpath)



class DFThread(QThread):
    changePixmap = pyqtSignal(QImage)
    showmarked = pyqtSignal(QImage)
    def run(self):            
            try:                
                self.cap = cv2.VideoCapture(0)                          
            except Exception as E:                
                print(E)
            
            while self.cap.isOpened():
                global code , order_code , score
                
                ret, f = self.cap.read()  
                f = cv2.resize(f,(800,600) , interpolation=cv2.INTER_AREA)
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                gray = shadow_remover(cv2 , gray)                
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edged = cv2.Canny(blurred, 65,150)
                f , order_code = read_qrcode(cv2  , f)        
               
                roi = None
                try:  
                    f , roi , roi_gray = detect_roi2(cv2,f,edged ,gray)    
                    roi = cv2.resize(roi, (260 , 615) , interpolation=cv2.INTER_AREA) 
                    roi_gray = cv2.resize(roi_gray, (260 , 615) , interpolation=cv2.INTER_AREA) 
                    if order_code != None and code != order_code :
                        code = order_code
                        

                    cv2.putText(f , "sequence = {}".format(code) , (10,20) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , (255 , 255 ,0))   
                    #the helping visual rectangle
                    cv2.putText(f,'aligner les rectangles',(305 ,140),cv2.FONT_HERSHEY_SIMPLEX,0.5, (0, 0, 255), 2)
                    cv2.rectangle(f,(315,155),(315+137,155+318),(255,0,0),2)
                    
                    if code != None:               
                             
                            score , _ = preprocess(cv2 , roi , roi_gray , get_ordered_answers(code , answers , nb_questions) , nb_questions )   
                            cv2.putText(f , "score = {}".format(score) , (10,35) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , (255 , 255 ,0))
                            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                            roi = cv2.resize(roi , (150 , 354) , interpolation=cv2.INTER_AREA) 
                            self.showmarked.emit(qimage2ndarray.array2qimage(roi))
                            
                except Exception as E:  
                    #print(E)      
                    pass  

                f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)      
                self.changePixmap.emit(qimage2ndarray.array2qimage(f))

class quizzthread(QThread):
    done = pyqtSignal(int)
    def run(self):        
                  
            make_quizz_doc(nb_questions , nbt , quizzpath)            
            self.done.emit(0)
        

class saveexcelthread(QThread):
    done = pyqtSignal(int)    
    def run(self):        
        try:
            window.excel_data.to_excel(quizzpath+'/quizz.xlsx' , index=False)
            self.done.emit(0)
        except Exception as e:
            print(e)
            pass

class OptionWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('opwin.ui' , self)

class EditQPWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('exceledit.ui' , self)


class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("qcm.ui", self)

    def setupUi(self,MainWindow):
        _translate = QtCore.QCoreApplication.translate

        MainWindow.setWindowTitle(_translate("window", "quizz scanner 1.0"))
        MainWindow.setFixedSize(980,720)
        #labels
        self.cam = MainWindow.findChild(QtWidgets.QLabel ,'cam')
        self.cam.setText("\t\t initialisation du périphérique video en cours ...")
        self.qrcode = MainWindow.findChild(QtWidgets.QLabel ,'qrcode')
        self.score = MainWindow.findChild(QtWidgets.QLabel ,'score')

        #textboxs -- buttons -- statusbar -- lcd
        self.ipsource = MainWindow.findChild(QtWidgets.QLineEdit ,'ipsource')
        self.setipcam = MainWindow.findChild(QtWidgets.QPushButton ,'setipcam')
        self.setipcam.clicked.connect(self.set_ip_cam)
        self.statusbar = MainWindow.findChild(QtWidgets.QStatusBar ,'statusbar')
        self.lcdscore = MainWindow.findChild(QtWidgets.QLCDNumber , 'lcdscore')


        #menus -- actions
        self.quitter = MainWindow.findChild(QtWidgets.QAction ,'actionquitter')
        self.quitter.triggered.connect(self.quit)        
        self.quitter.setShortcut(_translate("window", "Esc")) 

        self.excel = MainWindow.findChild(QtWidgets.QAction ,'actionexcel')
        self.excel.triggered.connect(self.openfileaction)

        self.qcm = MainWindow.findChild(QtWidgets.QAction ,'actionqcm')
        self.qcm.triggered.connect(self.quizz_gen)
        self.qcm.setShortcut(_translate("window","Ctrl+G"))

        self.config = MainWindow.findChild(QtWidgets.QAction ,'actionconfigurer')
        self.config.triggered.connect(self.configaction)
        self.config.setShortcut(_translate("window",'Ctrl+O')) 

        self.editqp = MainWindow.findChild(QtWidgets.QAction ,'actioneditqp')
        self.editqp.triggered.connect(self.editqpaction)
        self.editqp.setShortcut(_translate("window",'Ctrl+Q')) 
        
        

        self.feedthread = DFThread(window)
        self.feedthread.changePixmap.connect(lambda p: self.setimage(p))
        self.feedthread.showmarked.connect(lambda p: self.showmarked(p))
        self.feedthread.start()

    def change_source(self,source):    
        self.feedthread.cap = cv2.VideoCapture(source)
        self.feedthread.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.feedthread.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    def set_ip_cam(self):        
        self.change_source(self.ipsource.text())
        self.statusbar.showMessage("source video : {}".format(self.ipsource.text()))

    @pyqtSlot(QImage)
    def setimage(self , f ):       
        #the process result is the image to show
        window.cam.setPixmap(QPixmap.fromImage(f))  
        window.qrcode.setText(code)
        window.qrcode.update()    

    @pyqtSlot(QImage)
    def showmarked(self , f ):       
        #the process result is the image to show
        window.score.setGeometry(QtCore.QRect(830, 150, f.width(),f.height()))
        window.score.setPixmap(QPixmap.fromImage(f)) 
        window.lcdscore.display(score)


    def openfileaction(self):
        global quizzpath 
        home_dir = str(Path().absolute())
        fil = "xlsx(*.xlsx)"
        fname = QtWidgets.QFileDialog.getOpenFileName(self.centralwidget, 'Open file', home_dir,fil) 
        quizzpath = os.path.dirname(fname[0])  
        print(quizzpath)    

    def quit(self):   
        self.feedthread.cap.release()
        self.feedthread.exit() 
        sys.exit(app.exec_())  
    
    def quizz_gen(self):
        try:  
            buttonReply = QtWidgets.QMessageBox.question(self.centralwidget,'Générer ', "Générer "+str(nbt)+" tests avec "+ str(nb_questions) +" questions?(changer les valeurs dans le menu options)", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)                    
            if buttonReply == QtWidgets.QMessageBox.Yes:
                Qmaker = quizzthread(window)
                Qmaker.done.connect(lambda p: self.quizzdone(p))
                Qmaker.start()
                
                self.statusbar.showMessage("Génération en cours ...")
            
            
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

    def editqpaction(self):
        self.qpwin = EditQPWindow()
        self.tableview = self.qpwin.findChild(QtWidgets.QTableView ,'tableView')
        self.qpwin.setWindowTitle("Quick Excel Edit")
        self.tableview.setWordWrap(True)
        self.tableview.setTextElideMode(Qt.ElideMiddle)
        self.tableview.resizeRowsToContents()
        df = pd.read_excel(quizzpath + "/quizz.xlsx")
        df.set_index('questions')
        self.excel_data = df
        model = CustomTableModel(df)       
        self.tableview.setModel(model)

        self.saveexcel = self.qpwin.findChild(QtWidgets.QPushButton , 'save')
        self.saveexcel.clicked.connect(self.saveaction)
        self.qpwin.show()

    def saveaction(self): 
        try:  
            buttonReply = QtWidgets.QMessageBox.question(self.centralwidget,'excel quizz  ', "êtes vous sure?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)                    
            if buttonReply == QtWidgets.QMessageBox.Yes:
                Qsaver = saveexcelthread(window)
                Qsaver.done.connect(lambda p: self.savedone(p))
                Qsaver.start()
                self.statusbar.showMessage("modification du fichier excel en cours ...")
                self.qpwin.close()
                
            else:
                pass
            
        except Exception as e:
            print(e)
            self.statusbar.showMessage(str(e))
    
    @pyqtSlot(int)
    def savedone(self , x):
        self.statusbar.showMessage("fichier excel modifié ")

    
    
        

    
if __name__ == "__main__": 
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    #buttonReply = QtWidgets.QMessageBox.question(window.centralwidget,'menu camera', "avez vous une camera?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)                    
    #if buttonReply == QtWidgets.QMessageBox.Yes:
        
    window.setupUi(window)
    window.show()
    app.exec_()