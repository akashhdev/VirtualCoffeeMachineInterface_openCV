import os
from cvzone.HandTrackingModule import HandDetector
import cv2

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

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

modeType = 0
selection = []
selectionSpeed = 7
modePosition = [(1136,196),(1000,384),(1136,581)]
selectionList = [-1,-1,-1]
counterPause = 0
detector = HandDetector(detectionCon=0.8,maxHands=1)

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

    print(selectionList)

    # adding selection icon at bottom
    if selectionList[0] != -1:
        imgBackground[636:636+65, 133:133+65] = listImgIcons[selectionList[0]]
    if selectionList[1] != -1:
        imgBackground[636:636 + 65, 340:340 + 65] = listImgIcons[3+selectionList[1]]
    if selectionList[2] != -1:
        imgBackground[636:636 + 65, 542:542+ 65] = listImgIcons[6+selectionList[2]]

    #displaying
    cv2.imshow("Background",imgBackground)
    cv2.waitKey(1)