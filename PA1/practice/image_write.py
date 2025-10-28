import cv2

grayImg = cv2.imread('images/tsukuba_left.png', cv2.IMREAD_GRAYSCALE)
cv2.imwrite('output/gray.jpg', grayImg)