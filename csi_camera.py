# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
import time

# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen


## encode jpg:
#gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! 'video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12' ! nvjpegenc ! filesink location=test.jpg
## encode h264
#FILE=filename.mp4
#gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM), width=1920, height=1080,format=NV12, framerate=30/1' ! omxh264enc ! qtmux ! filesink location=$FILE -e 
def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=60,
    flip_method=0,
):
    print("pipeline: %dx%d => %dx%d @ %dfps" % (capture_width,capture_height,display_width,display_height,framerate) )
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


def show_camera():
    # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
    print(gstreamer_pipeline(flip_method=0))
    # 3280x2464: fish eye!
    cw = 3280
    ch = 2464
    
    cw,ch = (1920,1080)
    cw,ch = (1280,720)

    
    rw = 640
    rh = (rw*ch)/cw

    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0,capture_width=cw, capture_height=ch,framerate=60,display_width=cw,display_height=ch), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        window_handle = cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)
        # Window
        timeBegin = time.time()
        nCptFrame = 0
        while cv2.getWindowProperty("CSI Camera", 0) >= 0:
            if 0:
                # skip always some frame, it's better than running late on buffer then receiving a jump every 2sec...
                for i in range(4):
                    cap.grab()
                
            ret_val, img = cap.read() 
            img_reduced = cv2.resize(img, (rw,rh) )
            #~ print(img_reduced.shape)
            #~ cv2.imshow("CSI Camera", img_reduced)
            # This also acts as
            keyCode = cv2.waitKey(1) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
            nCptFrame += 1
            if nCptFrame > 30:
                fps = nCptFrame / (time.time()-timeBegin)
                print("INF: fps: %5.2f" % fps ) # without rendering & waitKey == 1 => 58fps in 720p
                nCptFrame = 0
                timeBegin = time.time()
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Unable to open camera")


if __name__ == "__main__":
    show_camera()