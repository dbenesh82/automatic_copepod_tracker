# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 18:02:49 2018

@author: phosp
"""

import numpy as np
import pandas as pd
import random
import cv2
import matplotlib.pyplot as plt
from skimage.measure import compare_ssim as ssim


vid_file = 'vid/pl1_day5.mov'

def video_attributes(video):
    '''
    Takes in video, returns number of frames, video width and video height
    '''
    cap = cv2.VideoCapture(video) # open vid
    # get vid basics, like frames, width, height
    tot_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return(tot_frames, vid_width, vid_height)
    cap.release() # close vid
    


def find_drop(video):
    '''
    Takes in video, returns the frame at which plate is dropped
    '''
    cap = cv2.VideoCapture(vid_file) # open vid
    # get first frame
    ret, frame_p = cap.read()
    frame_p = cv2.cvtColor(frame_p, cv2.COLOR_BGR2GRAY)
    
    img_sim_min = 1 # for finding dissimilar pics
    f_drop = 1 # for finding frame on which plate drops
    while(cap.isOpened()):
        # get current frame
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame_c = cap.read()
        
        if ret == True: # if not at end of vid
            # convert to grayscale           
            frame_c = cv2.cvtColor(frame_c, cv2.COLOR_BGR2GRAY)
            
            # if not in middle third of frames, skip
            if frame_n < tot_frames/3 or frame_n > (2 * tot_frames/3):
                next
            else:
                # compare consecutive frames to find most dissimilar ones
                img_simx = ssim(frame_p, frame_c)
                if img_simx < img_sim_min:
                    img_sim_min = img_simx
                    f_drop = frame_n
                        
            print(round(frame_n/tot_frames * 100, 1), "%") # how far along?
            frame_p = frame_c
        else:
            break
    # return results
    if img_sim_min > 0.75:
        print("Minimum image similarity high. Drop not found?")
    return(int(f_drop))
    cap.release()


def get_random_images(video, total_frames, drop, n):
    '''
    Get n random images before and after drop. 
    Returns an image array which is used to find wells and their average position.
    '''
    # pick random images
    rands_before = random.sample(range(drop), n)
    rands_after = random.sample(range(drop, total_frames), n)
    
    # pick out those frames from the video
    rand_imgs_after = []
    rand_imgs_before = []
    for i in range(len(rands_before)):
        cap = cv2.VideoCapture(video)
        
        # random image before drop
        cap.set(cv2.CAP_PROP_POS_FRAMES, rands_before[i]) 
        ret, frame = cap.read()
        rand_imgs_before.append(frame)
        
        # random image after drop
        cap.set(cv2.CAP_PROP_POS_FRAMES, rands_after[i]) 
        ret, frame = cap.read()
        rand_imgs_after.append(frame)
        
        cap.release()
    
    return(rand_imgs_before, rand_imgs_after)



# find the wells in the frames before and after the drop
def find_wells(imgs):
    '''
    Takes in a series of frames, finds the wells, returns their mean position and radius.
    '''
    for img in imgs: # loop through frames
        # find wells
        cimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(cimg, cv2.HOUGH_GRADIENT, 1, 90,
                                   param1=50,param2=30,
                                   minRadius=48,maxRadius=68)
        
        # convert well coordinates to df and sort them by position
        circdf = pd.DataFrame(circles[0,:], columns = ['x', 'y', 'rad'])
        circdf['well_x'] = pd.cut(circdf['x'], 6, labels = ['1', '2','3', '4', '5', '6'])
        circdf['well_y'] = pd.cut(circdf['y'], 4, labels = ['A', 'B','C', 'D'])
        circdf = circdf.sort_values(by = ['well_x', 'well_y'])
    
        # warning if 24 wells were not identified
        if len(circdf) != 24:
            print("24 wells not found!")
 
        # convert back to np.array; easier to average
        circles = np.array(circdf.loc[:,'x':'rad'])

        # compile the results across images
        try:
            sum_circles
        except NameError:
            sum_circles = circles
        else:
            sum_circles = sum_circles + circles
    
    # calculate mean positions across all images
    mean_circles = sum_circles/len(imgs)
    mean_circles = np.uint16(np.around(mean_circles))
    return(mean_circles)




def find_copepod(frame):
    '''
    Take in binary image, returns whether the cop was moving and thus identified.
    Helper in the track_copepod function
    '''
    # setup blob detector parameters.
    params = cv2.SimpleBlobDetector_Params()
    # threshold from black to white
    params.minThreshold = 0;
    params.maxThreshold = 255;
    # only blobs bigger than 7 pixels area
    params.filterByArea = True
    params.minArea = 7
    # create a detector with the parameters
    ver = (cv2.__version__).split('.')
    if int(ver[0]) < 3 :
        detector = cv2.SimpleBlobDetector(params)
    else :
        detector = cv2.SimpleBlobDetector_create(params)
    
    # use detector
    keypoints = detector.detect(frame)
    blobs = len(keypoints)
    cop_found = blobs > 0
    
    # if cop found, extract data
    if cop_found:
        (x,y), cop_qual = keypoints[0].pt, keypoints[0].size
    else:
        x,y,cop_qual = None,None,None
    return(cop_found, x, y, cop_qual, blobs)




def track_copepod(well, video):
    # create before and after masks for the well
    x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))
    xc, yc, rad = wells_before[well]
    d2 = (x - xc)**2 + (y - yc)**2
    mask_before = d2 > rad**2
    xc, yc, rad = wells_after[well]
    d2 = (x - xc)**2 + (y - yc)**2
    mask_after = d2 > rad**2
    
    # open video
    cap = cv2.VideoCapture('vid/pl1_day5.mov')
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 

    # initialize frame and data output
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[maskx] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray)
    
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        print(frame_n)
        ret, frame = cap.read()
        
        if ret==True:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if frame_n == drop: # at drop, reset background subtractor, record no data
                fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False)
                frame[mask_before] = 0
                next
            else:
                # apply masks to frame depending on before or after drop
                # remove background and invert (needed to detect blobs)
                if frame_n < drop:
                    gray[mask_before] = 0
                    frame[mask_before] = 0
                    gray = fgbg.apply(gray)
                    gray = cv2.bitwise_not(gray)
                else:
                    gray[mask_after] = 0
                    frame[mask_after] = 0
                    gray = fgbg.apply(gray)
                    gray = cv2.bitwise_not(gray)
            
                # find a copepod
                cop_found, xc, yc, cop_qual, blobs = find_copepod(gray)
                                
                if cop_found:
                    # make a row of data
                    out_row = np.array([frame_n, xc, yc, blobs, cop_qual])
                    # draw circle around cop
                    cv2.circle(frame,(int(xc),int(yc)),4,(0,0,255), 2)
                    # only reassign cop coord if moving
                    xp, yp = xc, yc
                else:
                    # if cop not found, use results
                    out_row = np.array([frame_n, xp, yp, blobs, cop_qual])
                    if xp is not None:
                        cv2.circle(frame,(int(xp),int(yp)),4,(255,0,0), 2)
            

                # create output array for each frame
                try:
                    out_array
                except NameError:
                    out_array = [out_row]
                else:
                    out_array = np.append(out_array, [out_row], axis = 0)

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))



tot_frames, vid_width, vid_height = video_attributes(vid_file)
drop = find_drop(vid_file)
rand_imgs_before, rand_imgs_after = get_random_images(vid_file, tot_frames, drop, 50)
wells_before = find_wells(rand_imgs_before) # get average well position before
wells_after = find_wells(rand_imgs_after) # get average well position after




well_id = ['1A', '1B', '1C', '1D',
           '2A', '2B', '2C', '2D',
           '3A', '3B', '3C', '3D',
           '4A', '4B', '4C', '4D',
           '5A', '5B', '5C', '5D',
           '6A', '6B', '6C', '6D']


outx = track_copepod(6, vid_file)    




















        
 
    







# pick just one well
x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))   
xc, yc, rad = wells_before[1]
d2 = (x - xc)**2 + (y - yc)**2
maskx = d2 > rad**2

cap = cv2.VideoCapture('vid/pl1_day5.mov')
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 

# initialize frame
ret, old_frame = cap.read()
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
old_gray[maskx] = 0

# look for cop; get initial values for tracking
old_cop_found, xp, yp, old_cop_qual = find_copepod(old_gray)

while(cap.isOpened()):
    frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
    ret, frame = cap.read()
    print(frame_n)
    if ret==True:
        # once frame number goes past drop, stop
        if frame_n >= f_drop:
            break
        else:
            # convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # make area outside wells black
            gray[maskx] = 0
            frame[maskx] = 0
            # remove blackground
            gray = fgbg.apply(gray)
            
            # find copepod in current frame
            cop_found, xc, yc, cop_qual = find_copepod(gray)
                
            if cop_found:
                # output its position and draw a circle around it
                out_row = np.array([frame_n, xc, yc, cop_qual])
                cv2.circle(frame,(xc,yc),4,(0,0,255), 2)
            # if no copepod found, use x, y coord from previous frame
            else:
                out_row = np.array([frame_n, xp, yp, cop_qual])
                if xp is not None:
                    cv2.circle(frame,(xp,yp),4,(255,0,0), 2)
            
            # create output array
            try:
                out_array
            except NameError:
                out_array = [out_row]
            else:
                out_array = np.append(out_array, [out_row], axis = 0)
                
            # assign current frame values to previous frame values
            old_cop_found, xp, yp, old_cop_qual = cop_found, xc, yc, cop_qual
 

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    else:
        break
cap.release()
cv2.destroyAllWindows()




