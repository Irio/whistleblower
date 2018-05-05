import sys

import cv2
import numpy

TEXT_MIN_WIDTH = 35
TEXT_MIN_HEIGHT = 10

DEFAULT_WIDTH  = 850
DEFAULT_HEIGHT = 1100

KERNEL_WIDTH  = 25
KERNEL_HEIGHT = 15


def remove_borders(image, threshold, max_width, max_height):
    height, width = image.shape[:2]

    for i in range(max_width):
        total = image[:, i].sum() / 255
        if total > threshold:
            image[:, i] = numpy.ones(height) * 255

        total = image[:, width - i - 1].sum() / 255
        if total > threshold:
            image[:, i - 1] = numpy.ones(height) * 255

    for i in range(max_height):
        total = image[i, :].sum() / 255
        if total > threshold:
            image[i, :] = numpy.ones(width) * 255

        total = image[height - i - 1, :].sum()
        if total > threshold:
            image[height - i - 1, :] = numpy.ones(width) * 255

    return image


def crop(numpy_array, filename):
    image = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    gray = remove_borders(gray, 0.8, 15, 15)

    adjusted_width  = image.shape[1] / DEFAULT_WIDTH
    adjusted_height = image.shape[0] / DEFAULT_HEIGHT

    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (KERNEL_WIDTH, KERNEL_HEIGHT))
    eroded = cv2.erode(gray, kernel)

    _, bw = cv2.threshold(eroded, 127, 255, cv2.THRESH_BINARY_INV)

    total, markers = cv2.connectedComponents(bw)

    images = [numpy.uint8(markers==i) * 255 for i in range(total) if numpy.uint8(markers==i).sum() > 10]

    rectangles = []

    for label in images:
        countours = cv2.findContours(label, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        (x,y,w,h) = cv2.boundingRect(countours[0])

        rectangles.append((x, y, w, h, label.sum() / 255.0))

    rectangles = sorted(rectangles, key=lambda x:x[4], reverse=True)

    rectangles = rectangles[1:]

    expanded = [sys.maxsize, sys.maxsize, -sys.maxsize, -sys.maxsize]

    for rect in rectangles:

        x0, y0, w0, h0 = expanded
        x1, y1, w1, h1, _ = rect

        if w1 <= (TEXT_MIN_WIDTH * adjusted_width):
            continue

        if h1 <= (TEXT_MIN_HEIGHT * adjusted_height):
            continue

        x = min(x0, x1)
        y = min(y0, y1)

        w = max(x0 + w0, x1 + w1) - x
        h = max(y0 + h0, y1 + h1) - y

        expanded = [x, y, w, h]

    cv2.imwrite(filename, image[y:y+h, x:x+w])
