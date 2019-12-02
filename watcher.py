import sys
sys.path.append("../jetson_tools/")
import misctools

import cv2 # made with cv 3.2.0-dev
import numpy as np
import select
import time
import sys
import v4l2capture  # can be found here : https://github.com/gebart/python-v4l2capture/blob/master/capture_picture.py

def list_video_device( bPrintHighestResolution=True ):
    import os
    import v4l2capture
    file_names = [x for x in os.listdir("/dev") if x.startswith("video")]
    file_names.sort()
    for file_name in file_names:
        path = "/dev/" + file_name
        print( "path: %s" % path )
        try:
            video = v4l2capture.Video_device(path)
            driver, card, bus_info, capabilities = video.get_info()
            print ("    driver:       %s\n    card:         %s" \
                "\n    bus info:     %s\n    capabilities  : %s" % (
                    driver, card, bus_info, ", ".join(capabilities)) )
                    
            if bPrintHighestResolution:
                w,h = video.set_format(100000,100000)
                print( "    highest format: %dx%d" % (w,h) );
                    
            video.close()
        except IOError as e:
            print("    " + str(e) )
            

def get_video_devices():
    import os
    device_path = "/dev"
    file_names = [os.path.join(device_path, x) for x in os.listdir(device_path) if x.startswith("video")]
    return file_names


class WebCam():
    """
    Access webcam(s) using video4linux (v4l2)
    eg:
        webcam = WebCam();
        im = webcam.getImage();
        cv2.imwrite( "/tmp/test.jpg", im )
    """
    def __init__( self, strDeviceName = "/dev/video0", nWidth = 640, nHeight = 480, nNbrBuffer = 1 ):
        """
        - nNbrBuffer: put a small number to have short latency a big one to prevent missing frames
        """
        print( "INF: WebCam: opening: '%s'" % strDeviceName );
        self.video = v4l2capture.Video_device(strDeviceName)
        # Suggest an image size to the device. The device may choose and
        # return another size if it doesn't support the suggested one.
        self.size_x, self.size_y = self.video.set_format(nWidth, nHeight)
        print( "format is: %dx%d" % (self.size_x, self.size_y) );

        # not working on the webcam device.
        #framerate = self.video.set_fps(30); # can't succeed in changing that on my cheap webcam, but work on my computer
        #print( "framerate is: %d" % (framerate) );
        
        # Create a buffer to store image data in. This must be done before
        # calling 'start' if v4l2capture is compiled with libv4l2. Otherwise
        # raises IOError.
        self.video.create_buffers(nNbrBuffer) # would be better to play with fps, but it's not working on mine...
        # Send the buffer to the device. Some devices require this to be done
        # before calling 'start'.
        self.video.queue_all_buffers()
        # Start the device. This lights the LED if it's a camera that has one.
        self.video.start()
        print( "INF: WebCam: opening: '%s' - done" % strDeviceName );
        
    def __del__( self ):
        self.video.close()
    
    def getImage(self, bVerbose =  True ):
        """
        return an image, None on error
        """
        if bVerbose: print("INF: WebCam.getImage: Reading image...")
        # Wait for the device to fill the buffer.
        rStartAcquistion = time.time()
        aRet = select.select((self.video,), (), ()) # Wait for the device to fill the buffer.
        if bVerbose: print( "DBG: WebCam.getImage: select return: %s" % str(aRet) );
        try:
            image_data = self.video.read_and_queue()
        except BaseException as err:
            print( "WRN: skipping image: %s" % str(err) )
            time.sleep( 0.2 )
            return None
            
        rEndAquisition = time.time()
        rImageAquisitionDuration =  rEndAquisition - rStartAcquistion

        #image = Image.fromstring("RGB", (size_x, size_y), image_data)
        #image.save(strFilename)
        
        
        if bVerbose: print( "image_data len: %s" % len(image_data) )
        if len(image_data) == self.size_x * self.size_y * 3:
            # color image
            nparr = np.fromstring(image_data, np.uint8).reshape( self.size_y,self.size_x,3)
            nparr = cv2.cvtColor(nparr, cv2.COLOR_BGR2RGB);
        else:
            # grey on 16 bits (depth on 16 bits)
            nparr = np.fromstring(image_data, np.uint16).reshape( self.size_y,self.size_x,1)
            minv = np.amin(nparr)
            maxv = np.amax(nparr)
            print( "min: %s, max: %s" % (minv, maxv) )            
            nparr /= 64
            #nparr = cv2.cvtColor(nparr, cv2.COLOR_BGR2RGB);            
        return nparr
# class WebCam - end


        
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
            
    list_video_device()
    webcam = WebCam(strDeviceName = "/dev/video%d" % nNumCamera );
    im = webcam.getImage();
    im = webcam.getImage();

    strWindowName = "camera %d" % nNumCamera
    
    nCptFrame = 0
    begin = time.time()
    
    aLastName = [] 

    strPrevName = ""
    imPrev = im[:]
    im[:]=(0,0,0) # first one refresh at first!
    timeLastOutputtedHtml = time.time()
    strCurrentImageInHtml = ""
    strPrevImageInHtml = ""
    bPreviousWasDifferent = False # you need to update once more, as the image in the html is always the previews one (for refresh blinking avoidance)
    while( 1 ):
        im = webcam.getImage(bVerbose=False);
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
                rDiff = misctools.mse(im,imPrev)
                imPrev = im
                #~ print("DBG: rDiff: %5.2f" % rDiff )
                livedataFilename = "/var/www/html/data/liveData"
                #~ livedataFilename = "/var/www/html/data/notify.asp"
                bRewriteHtml = False
                
                if rDiff > 750: # in daylight, it's around 700
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
                    time.sleep(0.1)
                    if time.time() - timeLastOutputtedHtml > 30.:
                        bRewriteHtml = True
                    
                if bRewriteHtml or bPreviousWasDifferent:
                    print("DBG: generating webpage...")
                    #~ generateHtml(aLastName, bReverse)
                    file = open(livedataFilename, "wt")
                    #file.write("<IMG SRC=./data/%s></IMG>" % strImageName )
                    file.write("<IMG SRC=./data/%s width=1024></IMG><br>%s<br>" % (strPrevImageInHtml, strCurrentTime ) )
                    file.write("<IMG SRC=./data/%s width=10></IMG><br>" % strCurrentImageInHtml )
                    file.write("<font size=-10>last computed: %s</font>" % misctools.getTimeStamp() )
                    file.write("<!--end-->" )
                    file.close()
                    timeLastOutputtedHtml = time.time()
                    
                
    
    cv2.imwrite( "/tmp/last.jpg", im )
