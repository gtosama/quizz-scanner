from imutils import contours , grab_contours , perspective 
from imutils.perspective import four_point_transform
import numpy as np
from pyzbar import pyzbar
import openpyxl

def shadow_remover(cv2 ,img):
    grayscale_plane = cv2.split(img)[0]
    dilated_img = cv2.dilate(grayscale_plane, np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(grayscale_plane, bg_img)
    normalized_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    return normalized_img

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

def preprocess(cv2 , image , gray , ANSWER_KEY , nb_questions):
    questionCnts = []  
         
    font = cv2.FONT_HERSHEY_SIMPLEX     
   
    thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,67,10)
    kernel = np.ones((1,1),np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.dilate(thresh,kernel,iterations = 5)
    #beta test
    
    #beta test end
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = grab_contours(cnts)
   
   
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        #define size of detected bubbles here
        if w >= 3 and h >= 3 and ar >= 0.9 and ar <= 1.1:
            questionCnts.append(c)  
    if len(questionCnts)  == nb_questions * 4 :
        correct = 0 
        questionCnts = contours.sort_contours(questionCnts,method="top-to-bottom")[0]        
        #cv2.imshow('thresh' , thresh)
        print(len(questionCnts))
        try:
                        
            for (q, i) in enumerate(np.arange(0, len(questionCnts), 4)):
                cnts = contours.sort_contours(questionCnts[i:i + 4 ])[0]
                bubbled = []
            
                for (j, c) in enumerate(cnts):                
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [c], -1, 255, -1)
                    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                    total = cv2.countNonZero(mask) 
                    print(total)               
                    if total > 600:                      
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

def detect_roi2(cv2 , org , edged , gray) :
    f = org.copy()
    cnts = cv2.findContours(edged, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = grab_contours(cnts)
    docCnt = None
            
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # if our approximated contour has four points,
        # then we can assume we have found the paper
        if len(approx) == 4 and cv2.contourArea(c) >= 450 :
            docCnt = approx
            break

    if len(docCnt) > 0 :
        x , y , w , h = cv2.boundingRect(docCnt)       
        cv2.rectangle(f,(x,y),(x+w,y+h),(0,255,0),2)
        warped = four_point_transform(f, docCnt.reshape(4, 2))
        roi_gray = four_point_transform(gray, docCnt.reshape(4, 2))
    
    return f , warped , roi_gray

