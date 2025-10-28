import cv2

coloredImg = cv2.imread('images/tsukuba_left.png')
grayImg = cv2.imread('images/tsukuba_left.png', cv2.IMREAD_GRAYSCALE)

cv2.imshow('original', coloredImg)
cv2.imshow('gray', grayImg)

cv2.waitKey(0)
cv2.destroyAllWindows()

