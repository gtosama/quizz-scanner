from imutils import contours , grab_contours , perspective
import numpy as np
from pyzbar import pyzbar
import openpyxl


def load_answers():
    book = openpyxl.load_workbook('quizz.xlsx')
    sheet = book.active
    ANSWERS={x-2:sheet.cell(row=x,column=6).value for x in range(2,12)}     
    return ANSWERS

def get_ordered_answers(code,right_answers,nb_questions):
    order = code.split(' ')
    order = [int(x)-1 for x in order]
    ordered_answers = {}
    for x in range(0,nb_questions):
        ordered_answers[x] = right_answers[order[x]]
    return ordered_answers

def read_qrcode(cv2, image):
    barcodes = pyzbar.decode(image)   
    code = None
    if len(barcodes) >=0:
            for barcode in barcodes:                
                (x, y, w, h) = barcode.rect
                code = barcode.data.decode("utf-8")                            
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(image, code, (x-200, y + 95), cv2.FONT_HERSHEY_SIMPLEX,0.5, (0, 0, 255), 2)
    return image , code

def preprocess(cv2 , image , ANSWER_KEY , nb_questions):
    questionCnts = []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    font = cv2.FONT_HERSHEY_SIMPLEX  
    
    blurred = cv2.GaussianBlur(gray, (1, 1), 0)
    edged = cv2.Canny(blurred, 75, 200)
    thresh = cv2.threshold(gray, 0, 255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = grab_contours(cnts)
   
   
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        #define size of detected bubbles here
        if w >= 18 and h >= 18 and ar >= 0.95 and ar <= 1.09:
            questionCnts.append(c)  
    if len(questionCnts)  == nb_questions * 4 :
        questionCnts = contours.sort_contours(questionCnts,method="top-to-bottom")[0]        
        #cv2.imshow('thresh' , thresh)
        try:
            correct = 0                
            for (q, i) in enumerate(np.arange(0, len(questionCnts), 4)):
                cnts = contours.sort_contours(questionCnts[i:i + 4 ])[0]
                bubbled = []
            
                for (j, c) in enumerate(cnts):                
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [c], -1, 255, -1)
                    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                    total = cv2.countNonZero(mask)                
                    if total > 400:                      
                        bubbled.append((total , j))
                color = (0, 0, 255)
                #print(bubbled)        
                k = ANSWER_KEY[q]
                if (bubbled !=None):
                    #if only one bubble is chosen
                    if len(bubbled) == 1:                
                        if k == bubbled[0][1]:
                            color = (0, 255, 0)
                            correct += 1
                        cv2.drawContours(image, [cnts[k]], -1, color, 3)        
                    else:
                        for y in range(len(cnts)):
                            cv2.drawContours(image, [cnts[y]], -1, color, 3) 
            #cv2.imshow("marked" , image)
            
        except  Exception as E :
            print(E)

    return correct , image


def detect_roi(cv2 , org , f , corners , ids):
    result = []
    roi = None
    for i in range(0, len(ids)):
        try:
            marker = np.squeeze(corners[i])                
            x1,y1 = marker[0]
            x2,y2 = marker[2]
            x = int((x1 + x2)/2)
            y = int((y1 + y2)/2)            
            result.append((x, y))
        except Exception as E:
            #print(E)
            pass      
     
        try:          
            edges = np.array(result) 
            roi = perspective.four_point_transform(f,edges)     
            for point in result:
                x , y = point
                cv2.circle(f , (x,y) , 10 , (0,255,0),-1)
                   
            ct = np.array(result).reshape((-1,1,2)).astype(np.int32)
            rect  = cv2.minAreaRect(ct)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(f , [box] , 0 , (255,0,0) , 2 )
                
        except Exception as E:
            print(E)
            pass
    return f , roi

