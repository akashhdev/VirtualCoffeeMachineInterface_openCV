import os
from cvzone.HandTrackingModule import HandDetector
import cv2
import mysql.connector
import uuid
from datetime import datetime
from fpdf import FPDF

################ MYSQL SETUP ###############

mydb, mycursor = None, None

def connectToDB():

    global mydb, mycursor

    #mydb = mysql.connector.connect(host="localhost",user="localhost",passwd="1234")
    mydb = mysql.connector.connect(host="localhost",user="root",passwd="9500")
    mycursor = mydb.cursor()
    mycursor.execute("use productDemo;")

connectToDB()

############################################

################ VIDEO INPUT  ##############

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

###############################################

############### ASSETS ####################

imgBackground = cv2.imread("Resources/Background2.png")

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
modePosition = [(1136,196),(1000,384),(1136,581),(1136,196)]
checkoutCirclePosition = (1067,315)
selectionList = [-1,-1,-1]
itemNameDict = {
             "order_name":{0:"latte",1:"black_coffee",2:"green_tea"},
             "order_config":{0:"regular_sugar",1:"medium_sugar",2:"large_sugar"},
             "order_size":{0:"regular_size",1:"medium_size",2:"large_size"}
            }

itemPriceDict = {
             "order_name":{"latte":50,"black_coffee":40,"green_tea":30},
             "order_config":{"regular_sugar":0,"medium_sugar":5,"large_sugar":10},
             "order_size":{"regular_size":0,"medium_size":15,"large_size":30}
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
orderPlacedScreenCounter = 0
detector = HandDetector(detectionCon=0.8,maxHands=1)
k1,k2,k3,k4 = 1,1,1,1

##############################################

#### MYSQL BACKEND ########

def pushToBackend():

    global orderDict
    global mydb, mycursor

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

    connectToDB()

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

        job = ""

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
            job+="\n\n"
            job+="COFFEMART"
            job+="\nRECIEPT OF PURCHASE"
            job+="\n"+dt_string
            job+="\nOrderId: "
            job+="\n"+order_id
            job+="\n--------------------------------"
            job+=f"\n{order_name}              {str(itemPriceDict['order_name'][order_name])} INR"
            job+=f"\n  {order_config}        {'+'+str(itemPriceDict['order_config'][order_config])} INR"
            job+=f"\n  {order_size}          {'+'+str(itemPriceDict['order_size'][order_size])} INR"
                    
        
        job+="\n--------------------------------"
        job+=f"\nTotal: {order_amount} INR"
        job+=f"\nPayment Status: {payment_status}"
        job+=f"\nOrder Status: {order_status}"
        job+="\n\n\n"
    else:
        print("\n\nNO DATA FOUND - printReceipt()")

    # Close the cursor and connection
    mycursor.close()

    # output reciept to print 
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Courier", size = 12)

    for line in job.split("\n"):
        pdf.cell(200,10, txt = line, ln = 1, align = 'C')

    pdf.output("recieptreciept_"+order_id+".pdf")

    # print output on console 
    print(job)
    
    return

### CLEAR PREVIOUS ORDER RECORD ######

def clearPreviousOrders():

    # clears previous orders from python memory
    # orders are archieved in mysql

    global orderDict

    orderDict = {
            "orderId": "",
            "orderName":[],
            "orderConfig":[],
            "orderSize":[],
            "orderValue":0,
            "paymentStatus": "PENDING",
            "orderStatus": "PENDING"
            }

    return
    
### RESTARTS THE MAIN LOOP #####

def restart():

    global modeType 
    global counterPause 
    global orderPlacedScreenCounter 
    global k1,k2,k3,k4
    global selectionList
    global imgBackground

    modeType = 0
    counterPause = 0
    orderPlacedScreenCounter = 0
    selectionList = [-1,-1,-1]
    k1,k2,k3,k4 = 1,1,1,1
    imgBackground = cv2.imread("Resources/Background.png")

    print("\nrestarting loop - restart()\n")

    virtualCoffee()

    return

### MAIN PROGRAM LOOP #######

def virtualCoffee():

    global modeType
    global orderPlacedScreenCounter
    global selectionSpeed

    global itemNameDict
    global itemPriceDict
    global orderDict

    global selection
    global modePosition
    global selectionList

    global counterPause
    global counter
    global orderPlacedScreenCounter
    global detector
    global k1,k2,k3,k4


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

            elif fingers1 == [1,1,1,1,1]:
                if selection != 3:
                    counter = 1
                selection = 3

            else:

                # if no finger is up, reset counter
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

        # OrderPlaced Screen - 4th reset state  
        if not hands and modeType == 3 and orderPlacedScreenCounter < 360:

            # 1. disable hand detection
            hands = None

            # 2. make a circle around the checkmark
            orderPlacedScreenCounter += 0.5
            
            cv2.ellipse(imgBackground, checkoutCirclePosition,(98,98),0,0,
                            orderPlacedScreenCounter*selectionSpeed,(0,255,0),20)
            

            # 3. after loading is done go back to initial screen
            if orderPlacedScreenCounter*selectionSpeed == 360:

                # 4. restart for next order
                break


        # pause after selection
        if counterPause > 0:
            counterPause += 1
            if counterPause > 30:
                counterPause = 0


        # adding selection icon at bottom
        if selectionList[0] != -1:
            imgBackground[636:636 + 65, 133:133 + 65] = listImgIcons[selectionList[0]]

            if k1:
                selection = selectionList[0]
                orderName = itemNameDict["order_name"][selection]

                orderDict["orderName"].append(orderName)
                orderDict["orderValue"] += itemPriceDict["order_name"][orderName]
                k1 = 0

        if selectionList[1] != -1:
            imgBackground[636:636 + 65, 340:340 + 65] = listImgIcons[3 + selectionList[1]]

            if k2:
                selection = selectionList[1]
                orderConfig = itemNameDict["order_config"][selection]

                # ensures we only add one item every iteration

                orderDict["orderConfig"].append(orderConfig)
                orderDict["orderValue"] += itemPriceDict["order_config"][orderConfig]
                k2 = 0

        if selectionList[2] != -1:
            imgBackground[636:636 + 65, 542:542 + 65] = listImgIcons[6 + selectionList[2]]

            if k3:
                selection = selectionList[2]
                orderSize = itemNameDict["order_size"][selection]

                # ensures we only add one item every iteration

                orderDict["orderSize"].append(orderSize)
                orderDict["orderValue"] += itemPriceDict["order_size"][orderSize]

                k3 = 0

        #push data tp backend
        if orderDict["orderSize"]:
            if k4:
                # 1. add order id
                orderDict["orderId"] = str(uuid.uuid4())

                # 2. confirm order
                orderDict['orderStatus'] = "ACCEPTED"

                # 3. push data to backend
                pushToBackend()

                k4 = 0

        #displaying
        cv2.imshow("Background",imgBackground)
        cv2.waitKey(1)

    restart()

    return

### EXECUTE THE PROGRAM ######

virtualCoffee()




