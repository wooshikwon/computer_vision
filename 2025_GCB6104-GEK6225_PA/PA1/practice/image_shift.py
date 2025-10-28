import cv2
import numpy as np

img = cv2.imread('images/tsukuba_left.png', cv2.IMREAD_GRAYSCALE)

d = 30

cv2.imshow('original', img)
h, w = img.shape
shifted = np.zeros_like(img)
shifted[:, d:] = img[:, :w-d]
cv2.imshow('shifted', shifted)

cv2.waitKey(0)
cv2.destroyAllWindows()
