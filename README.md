# Description
quizz scanner is a simple opencv application that can generate unique(random) bubble quizz tests and evaluate them based on a qrcode holding the order of the questions making cheating a little bit harder for students(better than nothing , i suppose).

# Installation
Use the package manager pip to install the dependencies

'''bash
pip install numpy opencv-contrib-python openpyxl pyzbar imutils PyQt5 qimage2ndarray
'''
pyzbar requires  [Visual C++ Redistributable Packages for Visual Studio 2013](https://www.microsoft.com/en-US/download/details.aspx?id=40784) to work

start the app py typing python qcm.py

# Usage
fill quizz.xlsx with the question , the answers(4) and the number of the right one.
use quizz.docx for the responses.
after launching the app , show the qrcode to initialize the evaluation (qrcode contains the sequence matching with the questions in the excel file needed after the shuffle).

now , show the bubble sheet and the work is done !!!




