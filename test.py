import cv2

img = cv2.imread("1.jpg")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv,(10, 100, 200), (25, 255, 255) )
cv2.imshow("orange", mask);cv2.waitKey();cv2.destroyAllWindows()