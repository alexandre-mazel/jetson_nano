import argparse
import logging
import time

import cv2
import os
import numpy as np

from tf_pose.estimator import TfPoseEstimator
from tf_pose.networks import get_graph_path, model_wh

from tf_pose import common

logger = logging.getLogger('TfPoseEstimator-WebCam')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

fps_time = 0

def skeletonsToExpr(humans):
    strOut = "["
    for human in humans:
        strOut += "{"
        for i in range(common.CocoPart.Background.value):
            if i not in human.body_parts.keys():
                continue
            strOut += "%d:[%5.3f,%5.3f,%5.3f]" % (i,human.body_parts[i].x, human.body_parts[i].y, human.body_parts[i].score)
            strOut += ","
        strOut += "},"
    strOut += "]"
    return strOut
    
    
def analyseSkeletonsPose(humans):
    """
    """
    image_h, image_w = 640,480
    centers = {}
    #~ print( "humans.dir: %s" % dir(humans) )
    for human in humans:
        #~ print( "human.dir: %s" % dir(human) )
        #~ print( "human.body_parts: %s" % human.body_parts )
        #~ print( "common.CocoPart.Background.value: %s" % common.CocoPart.Background.value )
        for i in range(common.CocoPart.Background.value):
            if i not in human.body_parts.keys():
                continue

            body_part = human.body_parts[i]
            #~ print( "body_part: %s" % str(body_part) )
            center = (int(body_part.x * image_w + 0.5), int(body_part.y * image_h + 0.5))
            centers[i] = center
            #~ print( "center: %s" % str(center) )

        # draw line
        for pair_order, pair in enumerate(common.CocoPairsRender):
            if pair[0] not in human.body_parts.keys() or pair[1] not in human.body_parts.keys():
                continue

            # npimg = cv2.line(npimg, centers[pair[0]], centers[pair[1]], common.CocoColors[pair_order], 3)
            #~ cv2.line(npimg, centers[pair[0]], centers[pair[1]], common.CocoColors[pair_order], 3)
            pass
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='tf-pose-estimation realtime webcam')
    parser.add_argument('--camera', type=int, default=0)

    parser.add_argument('--resize', type=str, default='0x0',
                        help='if provided, resize images before they are processed. default=0x0, Recommends : 432x368 or 656x368 or 1312x736 ')
    parser.add_argument('--resize-out-ratio', type=float, default=4.0,
                        help='if provided, resize heatmaps before they are post-processed. default=1.0')

    parser.add_argument('--model', type=str, default='mobilenet_thin', help='cmu / mobilenet_thin / mobilenet_v2_large / mobilenet_v2_small')
    parser.add_argument('--show-process', type=bool, default=False,
                        help='for debug purpose, if enabled, speed for inference is dropped.')
    args = parser.parse_args()

    logger.debug('initialization %s : %s' % (args.model, get_graph_path(args.model)))
    w, h = model_wh(args.resize)
    if w > 0 and h > 0:
        e = TfPoseEstimator(get_graph_path(args.model), target_size=(w, h))
    else:
        e = TfPoseEstimator(get_graph_path(args.model), target_size=(432, 368)) # 216/184 # but must be a 16 multiple
    logger.debug('cam read+')
    cam = cv2.VideoCapture(args.camera)
    ret_val, image = cam.read()
    ret_val, image = cam.read()
    ret_val, image = cam.read()
    logger.info('cam image=%dx%d' % (image.shape[1], image.shape[0]))
    if image.shape[1] >= 640:
        cam.set(cv2.CAP_PROP_FRAME_WIDTH,int(640))
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT,int(480))
        ret_val, image = cam.read()
        logger.info('changing resolution => cam image=%dx%d' % (int(image.shape[1]), int(image.shape[0])))

    strFolderOut = "./recording/"
    try:
        os.makedirs ( strFolderOut )
    except: pass
    
    nCpt = 0
    while True:
        ret_val, image = cam.read()
        # if image larger than 640x480, reduce it, and reduce network ???
        if image.shape[1] >= 640 and 0:
            #~ nScaleFactor = 2
            image = cv2.resize(image, (320,240)) # , fx=1./nScaleFactor, fy=1./nScaleFactor
            print( "image resized to 320x240")

        #~ logger.debug('image process+')
        humans = e.inference(image, resize_to_default=(w > 0 and h > 0), upsample_size=args.resize_out_ratio)    
        
        if len(humans) > 0:
            
            analyseSkeletonsPose( humans )   
            
            #~ print( "humans: %s" % str(humans) )
            strAnalyseRes = skeletonsToExpr(humans)
            print( "strAnalyseRes: %s" % strAnalyseRes )

            strStamp = str(time.time())
            cv2.imwrite( strFolderOut + strStamp + ".png", image )
            
            #~ logger.debug('postprocess+')
            image = TfPoseEstimator.draw_humans(image, humans, imgcopy=False)
            cv2.imwrite( strFolderOut + strStamp + "_skeleton.png", image )
            file = open( strFolderOut + strStamp + ".dat", "wt" )
            file.write( strAnalyseRes )
            file.close()

            

        #~ logger.debug('show+')
        strTxt = "FPS: %f" % (1.0 / (time.time() - fps_time)) 
        print( strTxt )
        cv2.putText(image,
                    strTxt,
                    (10, 10),  cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 2)
        if (nCpt & 7) == 7:
            cv2.imshow('tf-pose-estimation result', image)
        fps_time = time.time()
        if cv2.waitKey(1) == 27:
            break
        #~ logger.debug('finished+')
        nCpt += 1

    cv2.destroyAllWindows()
