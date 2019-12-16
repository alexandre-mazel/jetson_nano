import sys
sys.path.append("../jetson_tools/")
import misctools
import webcam

import cv2 # made with cv 3.2.0-dev
import numpy as np
import select
import time
import sys
import v4l2capture  # can be found here : https://github.com/gebart/python-v4l2capture/blob/master/capture_picture.py



        
if __name__ == "__main__":
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE,SIG_DFL)     
    nNumCamera = 0
    if len(sys.argv) > 1:
        if sys.argv[1][0] == '-':
            print( "syntax: %s <camera_num (default: %s)>" % (sys.argv[0] ),nNumCamera)
            exit(-1)
        else:
            nNumCamera = int(sys.argv[1])
            
    webcam.list_video_device()
    wcam = webcam.WebCam(strDeviceName = "/dev/video%d" % nNumCamera );
    im = wcam.getImage();
    im = wcam.getImage();

    strWindowName = "camera %d" % nNumCamera
    
    nCptFrame = 0
    begin = time.time()
    
    aLastName = [] 

    strPrevName = ""
    imPrev = im[:]
    im[:]=(255,255,255) # first one => refresh at first!
    timeLastOutputtedHtml = time.time()
    strCurrentImageInHtml = ""
    strPrevImageInHtml = ""
    bPreviousWasDifferent = False # you need to update once more, as the image in the html is always the previews one (for refresh blinking avoidance)
    # center of image
    xc1 = int(im.shape[1]*1/4)
    xc2 = int(im.shape[1]*3/4)
    yc1 = int(im.shape[0]*1/4)
    yc2 = int(im.shape[0]*3/4)
    while( 1 ):
        im = wcam.getImage(bVerbose=False);
        if not im is None:
            if 0:
                cv2.imshow(strWindowName,im)
                key = cv2.waitKey(1)
                #~ print key
                if key == 27: break
            nCptFrame += 1
            if nCptFrame > 100:
                duration = time.time() - begin
                print( "fps: %5.3f" % (float(nCptFrame)/duration) )
                nCptFrame = 0
                begin = time.time()
            if 1:
                rDiff = misctools.mse(im,imPrev, bDenoise=True)
                rDiffCenter = misctools.mse(im[yc1:yc2,xc1:xc2],imPrev[yc1:yc2,xc1:xc2], bDenoise=True)
                rAvgColor = im.mean()
                imPrev = im
                print("DBG: rDiff: %5.2f, rDiffCenter: %5.2f, color: %5.2f" % (rDiff,rDiffCenter, rAvgColor) )
                livedataFilename = "/var/www/html/data/liveData"
                #~ livedataFilename = "/var/www/html/data/notify.asp"
                bRewriteHtml = False
                
                # 4 types de lumiere, regit la couleur: 
                # - nuit avec juste tele: 4
                # - juste sam: 14
                # - sombre avec juste salon: 35
                # - en journee: ??
                
                # avec bDenoise=True
                # rDiff: 70/ 60/ 130/ 700
                # rDiffCenter: 70/ 105/ 130/ 700
                
                if      (rAvgColor < 40 and (rDiff > 250 or rDiffCenter > 150) ) \
                    or  (rAvgColor > 40 and (rDiff > 300 or rDiffCenter > 200) ) \
                    : 
                    bPreviousWasDifferent = True
                    print("DBG: writing image...")
                    # write image and update liveData for html server
                    strImageName = "%s.jpg" % misctools.getFilenameFromTime() #time.time()
                    strTotalImageName = "/var/www/html/data/" + strImageName
                    cv2.imwrite( strTotalImageName, im,[int(cv2.IMWRITE_JPEG_QUALITY), 80] )
                    aLastName.append(strImageName)
                    aLastName = aLastName[:-5]
                    
                    if strPrevName == "":
                        strPrevName = strImageName
                    strCurrentImageInHtml = strImageName
                    strPrevImageInHtml = strPrevName
                    strCurrentTime = misctools.getTimeStamp()
                    
                    bRewriteHtml = True
                    strPrevName = strImageName
                    time.sleep(1.2) # don't refresh too often !
                else:
                    bPreviousWasDifferent = False
                    time.sleep(0.2)
                    if time.time() - timeLastOutputtedHtml > 120.:
                        bRewriteHtml = True
                    
                if bRewriteHtml or bPreviousWasDifferent:
                    print("DBG: generating webpage...")
                    #~ generateHtml(aLastName, bReverse)
                    file = open(livedataFilename, "wt")
                    #file.write("<IMG SRC=./data/%s></IMG>" % strImageName )
                    file.write("<IMG SRC=./data/%s width=1024></IMG><br>%s<br>" % (strPrevImageInHtml, strCurrentTime ) )
                    file.write("<IMG SRC=./data/%s width=1024></IMG><br>" % strCurrentImageInHtml )
                    file.write("<font size=-10>last computed: %s</font>" % misctools.getTimeStamp() )
                    file.write("<!--end-->" )
                    file.close()
                    timeLastOutputtedHtml = time.time()
                    
                
    
    cv2.imwrite( "/tmp/last.jpg", im )
