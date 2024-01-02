import numpy as np
import mss
import cv2
from pynput.keyboard import Controller, Listener
import time
import threading, sys

BAR_TOP_COLOUR = np.array([0, 193, 73, 255])
BAR_BOTTOM_COLOUR = np.array([1, 101, 33, 255])
BAR_COLUMN = 20
FISH_COLOUR = np.array([151, 96, 2, 255])
FISH_COLUMN = 20
EXC_COLOUR1 = np.array([0, 186, 247, 255])
EXC_COLOUR2 = np.array([0, 249, 251, 255])

def holdC(holdTime):
    keyboard.press('c')
    time.sleep(holdTime)
    keyboard.release('c')
    return

def findTopBar(screen):
    topBarY = -1
    for row in range(0,600):
        if screen[row][BAR_COLUMN].tolist() == BAR_TOP_COLOUR.tolist():
            topBarY = row
            break

    return topBarY

def findBottomBar(screen):
    bottomBarY = -1
    for row in range(599,0,-1):
        if screen[row][BAR_COLUMN].tolist() == BAR_BOTTOM_COLOUR.tolist():
            bottomBarY = row
            break

    return bottomBarY

def findFish(screen):
    fishY = -1
    for row in range(0,600):
        if screen[row][FISH_COLUMN].tolist() == FISH_COLOUR.tolist():
            fishY = row
            break

    return fishY

def findVelocity(presentV, pastV, time_interval):
    return (presentV - pastV) / time_interval

def hook():
    keyboard.press('c')
    time.sleep(0.3)
    keyboard.release('c')
    time.sleep(0.3)
    keyboard.press('c')
    time.sleep(1.9)
    keyboard.release('c')
    return
    
def fishing():
    global stop, t
    startDelay = 5
    for i in range(startDelay, 0, -1):
        print(f"[A] Wait for {i}...")
        time.sleep(1)
    print("[A] Program started.")

    fishingTop = cv2.imread('Images\\fishingTop.png',0)
    barTop = cv2.imread('Images\\topBarNew2.png',0)

    with mss.mss() as sct:

        # The screen part to capture
        monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        smallRegion = {}
        
        while True:
            
            foundUI = False

            while foundUI == False:
                if(stop):
                    if(t):
                        t.join()
                    print("[A] Program Terminated")
                    return

                # Grab the data
                screen = np.array(sct.grab(monitor))
                newScreen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)

                #Detect when fishing
                res = cv2.matchTemplate(newScreen,fishingTop,cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if(max_val > 0.95 and stop == False):
                    print("[A] Started!")
                    print("[A] Press 'z' to terminate program.")
                    foundUI = True
                    smallRegion = {"top": monitor['top'] + max_loc[1], "left": monitor['left'] + max_loc[0], "width": 60, "height": 600}
                    
            barY, fishY, prevdy, prevFishY = 0, 0, 0, 0
            prevBarY = 550

            fishing = True

            screen = np.array(sct.grab(smallRegion))

            #바 찾기
            topBarY = findTopBar(screen)
            bottomBarY = findBottomBar(screen)

            centrePerc = 0.50

            barLength = bottomBarY - topBarY
            barAddition = int(centrePerc*barLength)

            startT, endT = 0, 0 #딜레이 기록용

            a = 0.5/100
            b = 1.5/100
            c = 0.9/100
            g = 9.8
            
            while fishing == True:
                #화면 선택
                screen = np.array(sct.grab(smallRegion))

                topBarY = findTopBar(screen)
                bottomBarY = findBottomBar(screen)
                if(topBarY == -1 and bottomBarY != -1):
                    topBarY = bottomBarY - barLength
                if(topBarY == -1): #둘다 불가능할 경우
                    newScreen = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
                    res = cv2.matchTemplate(newScreen,barTop,cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    if(max_val > 0.80):
                        topBarY = max_loc[1]

                if(bottomBarY == -1):
                    bottomBarY = topBarY + barLength

                #물고기 탐색
                fishY = findFish(screen)
                if fishY == -1:
                    if(t):
                        t.join()
                    print("[A] Restarting...")
                    print("[A] Press 'z' to terminate program.\n\n")
                    fishing = False
                    #hook()
                    
                barY = topBarY + barAddition
                time_interval = 1 / 30  # 프레임값
                dy = barY - fishY

                fish_velocity = findVelocity(fishY, prevFishY, time_interval)
                bar_velocity = findVelocity(barY, prevBarY, time_interval)
                d_velocity = findVelocity(dy, prevdy, time_interval)
                velocity_0 = (bar_velocity - (a / 30))
                
                prevdy, prevBarY, prevFishY = dy, barY, fishY

                if(fishY < barY):
                    tem = a * ((velocity_0**2) * g + (a - g) * (fishY - bottomBarY) * g + (fish_velocity**2))
                    tem = max(tem,0)
                    temp1, temp2, temp3 = tem ** 0.5, velocity_0 * a, -490
                    holdTime1 = -((temp1 + temp2) / temp3 * 2)
                    holdTime2 = (a*dy) + (b*d_velocity) + (c*bar_velocity)
                    if(holdTime2 > 0):
                        holdTime2 = (holdTime2 ** 0.5)
                    else:
                        holdTime2 = -1 * ((-1 * holdTime2) ** 0.5)
                    holdTime = round(holdTime1 * 0.9 + holdTime2 * 0.1, 4)
                    if(holdTime1 > 1):
                        holdTime = 0
                    else:
                        #endT = time.time()
                        #delay = endT - startT
                        #sys.stdout.write(f"Hold1 = {holdTime1:>7.4f}, Hold2 = {holdTime2:>7.4f}, WHold = {holdTime:>7.4f}, Delay = {delay:.4f}\n")
                        pass
                elif(fishY > topBarY and bottomBarY < 450): #하강시
                    holdTime = 0.003
                elif(bottomBarY < 500): #바닥 근처 도달시 튀어오름 방지
                    holdTime = 0.005
                else:
                    holdTime = 0

                if(holdTime > 0.05): #0.05, 0.05
                    holdTime = 0.05

                if(holdTime > 0):
                    #startT = time.time()
                    t = threading.Thread(target=holdC, args=(holdTime,))
                    t.start()

                if cv2.waitKey(25) & 0xFF == ord("q"):
                    cv2.destroyAllWindows()
                    if(t):
                        t.join()
                    break

def on_press(key):
    global stop
    try:
        if(key.char == 'z'):
            stop = True
    except:
        pass

def main():
    global stop
    listener = Listener(on_press = on_press)
    listener.start()
    fishing()

    listener.stop()
    listener.join()

if __name__ == "__main__":
    keyboard = Controller()
    stop = False
    t = None #스레드
    main()
