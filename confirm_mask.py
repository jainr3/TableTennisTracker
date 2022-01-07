import cv2

img = cv2.imread("img/calibrate.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv,(0, 94, 108), (25, 255, 197))
cv2.imshow("orange", mask);cv2.waitKey();cv2.destroyAllWindows()