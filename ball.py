from collections import deque
from picamera2 import Picamera2
import numpy as np
import argparse
import cv2
import imutils
import time

BUFF_SIZE = 64

# Config colors
blue_lower = (90, 50, 70)
blue_upper = (128, 255, 255)

# Deque of points in buffer
points = deque(maxlen=BUFF_SIZE)

# Init camera
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(raw={"size":(1640,1232)}, main={"format":"RGB888", "size": (640,480)})    
)
picam2.start()
time.sleep(2.0)

# Main loop
while True:
    img = picam2.capture_array()
    
    # Get current frame
    frame = img
    
    if frame is None:
        break

    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # construct a mask for the color blue, then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    # 
    mask = cv2.inRange(hsv, blue_lower, blue_upper)
    mask = cv2.erode(mask, None, iterations=2)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    center = None
    mask = cv2.dilate(mask, None, iterations=2)

    # only proceed if at least one contour was found
    if len(contours) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        try:
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            # only proceed if the radius meets a minimum size
            if radius > 10:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
        except:
            pass

    points.appendleft(center)
    
    # loop over the set of tracked points
    for i in range(1, len(points)):
        # if either of the tracked points are None, ignore them
        if points[i - 1] is None or points[i] is None:
            continue
        # otherwise, compute the thickness of the line and
        # draw the connecting lines
        thickness = int(np.sqrt(BUFF_SIZE / float(i + 1)) * 2.5)
        cv2.line(frame, points[i - 1], points[i], (0, 0, 255), thickness)

    # show the frame to our screen
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

picam2.stop()
picam2.close()
cv2.destroyAllWindows()
