import os
from cvzone.HandTrackingModule import HandDetector
import cv2
import mysql.connector
import uuid
from datetime import datetime


################ MYSQL SETUP ###############
#mydb = mysql.connector.connect(host="localhost",user="localhost",passwd="1234")
mydb = mysql.connector.connect(host="localhost",user="root",passwd="9500")
mycursor = mydb.cursor()
mycursor.execute("use productDemo;")


############################################

################ VIDEO INPUT  ##############

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

###############################################

############### ASSETS ####################

imgBackground = cv2.imread("Resources/Background.png")

# importing mode images
folderPathModes = "Resources/Modes"
listImgModesPath = os.listdir(folderPathModes)
listImgModes = []
for imgModePath in listImgModesPath:
    listImgModes.append(cv2.imread(os.path.join(folderPathModes, imgModePath)))


# importing icon images
folderPathIcons = "Resources/Icons"
listImgIconsPath = os.listdir(folderPathIcons)
listImgIcons = []
for imgIconsPath in listImgIconsPath:
    listImgIcons.append(cv2.imread(os.path.join(folderPathIcons, imgIconsPath)))
#########################################


################ VARIABLES ###################
modeType = 0
selection = []
selectionSpeed = 9
modePosition = [(1136,196),(1000,384),(1136,581)]
selectionList = [-1,-1,-1]
itemDict = {
             0:[('latte',50),('black',40),('tea',30)],
             1:[('sugar_one',0),('sugar_two',5),('sugar_three',10)],
             2:[('size_one',0),('size_two',15),('size_three',30)]
            }

itemPriceDict = {
             "order_name":{"latte":50,"black":40,"tea":30},
             "order_config":{"sugar_one":0,"sugar_two":5,"sugar_three":10},
             "order_size":{"size_one":0,"size_two":15,"size_three":30}
            }

orderDict = {
            "orderId": "",
            "orderName":[],
            "orderConfig":[],
            "orderSize":[],
            "orderValue":0,
            "paymentStatus": "PENDING",
            "orderStatus": "PENDING"
            }
counterPause = 0

detector = HandDetector(detectionCon=0.8,maxHands=1)
k1,k2,k3,k4 = 1,1,1,1

##############################################

#### MYSQL BACKEND ########

def pushToBackend(orderDict):

    ORDER_ID = orderDict["orderId"]
    ORDER_NAME = orderDict["orderName"][0]
    ORDER_CONFIG = orderDict["orderConfig"][0]
    ORDER_SIZE = orderDict["orderSize"][0]
    PAYMENT_STATUS = orderDict["paymentStatus"]
    ORDER_STATUS = orderDict["orderStatus"]
    ORDER_AMOUNT = str(orderDict["orderValue"])

    sql = "INSERT INTO order_info VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (ORDER_ID,
           ORDER_NAME,
            ORDER_CONFIG,
            ORDER_SIZE,
            ORDER_AMOUNT,
            PAYMENT_STATUS,
            ORDER_STATUS
           )

    mycursor.execute(sql, val)
    mydb.commit()
    #print(mycursor.execute('INSERT INTO order_info VALUES ("7945cfb4-44bb-4000-b316-ec8c76e0083a", "latte", "latte", "latte", "PENDING", "PENDING", "150");'))
    
    # 2. print reciept for last order
    printReciept(ORDER_ID)

    # 3. clear previous order 
    clearPreviousOrders()

    return

### PRINT RECIEPT #########

def printReciept(orderID):
    
    if orderID == '':
        print("NO orderID given - printReciept")
        return
    
    # Execute a SELECT statement to extract the data
    query = 'SELECT order_id, order_name, order_config, order_size, order_status, payment_status, order_amount FROM order_info WHERE order_id = "{}"'.format(orderID)
    print(query)
    mycursor.execute(query)

    # Fetch all the data from the SELECT statement
    data = mycursor.fetchall()

    # Iterate over the data and print each row
    if data:
        for row in data:
            order_id = row[0]
            order_name = row[1]
            order_config = row[2]
            order_size = row[3]
            order_status = row[4]
            payment_status = row[5]
            order_amount = row[6]

            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            print("Receipt    "+dt_string)
            print("--------------------------------")
            print(f"{order_name}              {str(itemPriceDict['order_name'][order_name])}")
            print(f"  {order_config}        {'+'+str(itemPriceDict['order_config'][order_config])}")
            print(f"  {order_size}          {'+'+str(itemPriceDict['order_size'][order_size])}")
                    
        
        print("--------------------------------")
        print(f"Total: {order_amount}")
        print(f"Payment Status: {payment_status}")
        print(f"Order Status: {order_status}")
    else:
        print("\n\nNO DATA FOUND - printReceipt()")

    # Close the cursor and connection
    mycursor.close()
    
    return


def clearPreviousOrders():

    # clears previous orders from python memory
    # orders are archieved in mysql

    global orderDict

    orderDict = {
            "orderName":[],
            "orderConfig":[],
            "orderSize":[],
            "orderValue":0,
    }

    return
    


### MAIN PROGRAM LOOP #######

while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)
    imgBackground[139:139+480,50:50+640] = img
    #print(len(listImgModes))
    imgBackground[0:720,850:1280] = listImgModes[modeType]

    if hands and counterPause == 0 and modeType < 3:
        hand1 = hands[0]
        fingers1 = detector.fingersUp(hand1)

        if fingers1 == [0,1,0,0,0]:
            if selection != 0:
                counter = 1
            selection = 0


        elif fingers1 == [0,1,1,0,0]:
            if selection != 1:
                counter = 1
            selection = 1


        elif fingers1 == [0,1,1,1,0]:
            if selection != 2:
                counter = 1
            selection = 2

        else:
            selection = -1
            counter = 0


        if counter > 0:
            counter += 1

            #print(counter)
            cv2.ellipse(imgBackground, modePosition[selection],(103,103),0,0,
                        counter*selectionSpeed,(0,255,0),20)

            if counter*selectionSpeed > 360:
                selectionList[modeType] = selection
                modeType += 1
                counter = 0
                selection = -1
                counterPause = 1


    # pause after selection
    if counterPause > 0:
        counterPause += 1
        if counterPause > 60:
            counterPause = 0


    # adding selection icon at bottom
    if selectionList[0] != -1:
        imgBackground[636:636 + 65, 133:133 + 65] = listImgIcons[selectionList[0]]

        if k1:
            selection = selectionList[0]
            # ensures we only add one item every iteration
            orderDict["orderName"].append(itemDict[selection][selection][0])
            orderDict["orderValue"] += itemDict[selection][selection][1]
            k1 = 0


    if selectionList[1] != -1:
        imgBackground[636:636 + 65, 340:340 + 65] = listImgIcons[3 + selectionList[1]]

        if k2:
            selection = selectionList[1]
            # ensures we only add one item every iteration
            orderDict["orderConfig"].append(itemDict[selection][selection][0])
            orderDict["orderValue"] += itemDict[selection][selection][1]
            k2 = 0


    if selectionList[2] != -1:
        imgBackground[636:636 + 65, 542:542 + 65] = listImgIcons[6 + selectionList[2]]

        if k3:
            selection = selectionList[2]
            # ensures we only add one item every iteration
            orderDict["orderSize"].append(itemDict[selection][selection][0])
            orderDict["orderValue"] += itemDict[selection][selection][1]
            k3 = 0

    #push data tp backend
    if orderDict["orderSize"]:
        if k4:
            # 1. add order id
            orderDict["orderId"] = str(uuid.uuid4())

            # 2. confirm order
            orderDict['orderStatus'] = "ACCEPTED"

            # 3. push data to backend
            pushToBackend(orderDict)

            k4 = 0

    #displaying
    cv2.imshow("Background",imgBackground)
    cv2.waitKey(1)






