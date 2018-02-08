# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 13:55:38 2018

@author: phosp
"""

import numpy as np
import pandas as pd
import random
import cv2
import matplotlib.pyplot as plt
from skimage.measure import compare_ssim as ssim



# find drop - fast enough that no reduction in frames needed
cap = cv2.VideoCapture('day5/pl1_day5.mov') # open vid

# get vid basics, like frames, width, height
tot_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# read first frame
ret, frame_p = cap.read()
frame_p = cv2.cvtColor(frame_p, cv2.COLOR_BGR2GRAY)

# open vid and go through frame by frame
f_num = 1
img_sim_min = 1
f_drop = 1
while(cap.isOpened()):
    if ret==True:
        ret, frame_c = cap.read()
        # convert frame to grayscale
        frame_c = cv2.cvtColor(frame_c, cv2.COLOR_BGR2GRAY)
        
        # if not in middle third of frames, skip
        if f_num < tot_frames/3 or f_num > (2 * tot_frames/3):
            next
        else:
            # compare consecutive frames to find most dissimilar ones
            img_simx = ssim(frame_p, frame_c)
            if img_simx < img_sim_min:
                img_sim_min = img_simx
                f_drop = f_num
        
        print(round(f_num/tot_frames * 100, 1), "%") # how far along?
        f_num += 1
        frame_p = frame_c
    else:
        break
cap.release()




# pick random 50 frames before and after drop 
rands_before = random.sample(range(f_drop), 50)
rands_after = random.sample(range(f_drop, tot_frames), 50)

# pick out those frames from the video
rand_imgs_after = []
rand_imgs_before = []
for i in range(len(rands_before)):
    cap = cv2.VideoCapture('day5/pl1_day5.mov')
    
    # random image before drop
    cap.set(cv2.CAP_PROP_POS_FRAMES, rands_before[i]) 
    ret, frame = cap.read()
    rand_imgs_before.append(frame)
    
    # random image after drop
    cap.set(cv2.CAP_PROP_POS_FRAMES, rands_after[i]) 
    ret, frame = cap.read()
    rand_imgs_after.append(frame)
    
    cap.release()


# find the wells in the frames before and after the drop
def find_wells(imgs):
    '''
    Takes in a series of frames, finds the wells, returns their mean position
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



wells_before = find_wells(rand_imgs_before) # get average well position before
wells_after = find_wells(rand_imgs_after) # get average well position after


# exclude the area outside of wells as uninteresting
def exclude_outside_wells(wells, H, W):
    '''
    Takes in the coordinates of wells, video height, and video width.
    Returns logical 'mask' of coordinates to black out
    '''
    # x and y coordinates per every pixel of the image
    x, y = np.meshgrid(np.arange(W), np.arange(H))   
    for well in wells:
        # location of well
        xc, yc, rad = well
        # x and y coordinates per every pixel of the image
        #x, y = np.meshgrid(np.arange(W), np.arange(H))
        # squared distance from the center of well
        d2 = (x - xc)**2 + (y - yc)**2
        # mask is True outside of the circle; for excluding
        maskx = d2 > rad**2
        try:
            mask
        except NameError:
            mask = maskx # if no mask yet, create it
        else:
            mask = np.logical_and(mask, maskx) # overlap between new and existing mask
    return(mask)

# identifies areas to exclude
mask_before = exclude_outside_wells(wells_before, vid_height, vid_width)
mask_after = exclude_outside_wells(wells_after, vid_height, vid_width)






# here's the after drop video
cap = cv2.VideoCapture('day5/pl1_day5.mov')
cap.set(cv2.CAP_PROP_POS_FRAMES, f_drop + 1) # set starting frame as just after drop
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500, detectShadows = False) 

while(cap.isOpened()):
    frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
    ret, frame = cap.read()
         
    if ret==True:
        # convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # make area outside wells black
        gray[mask_after] = 0
        # remove background
        gray = fgbg.apply(gray)
        
        # draw the circles around the wells
        for i in wells_after:
            # draw the outer circle
            cv2.circle(gray,(i[0],i[1]),i[2],(211,211,211), 2)
            # draw the center of the circle
            #cv2.circle(gray,(i[0],i[1]),2,(0,0,0),3)
        
        cv2.imshow('frame', gray)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break
cap.release()
cv2.destroyAllWindows()




# here's the before drop video
cap = cv2.VideoCapture('day5/pl1_day5.mov')
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 

while(cap.isOpened()):
    frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
    ret, frame = cap.read()
    
    if ret==True:
        # once frame number goes past drop, stop
        if frame_n >= f_drop:
            break
        else:
            # convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # make area outside wells black
            gray[mask_before] = 0
            frame[mask_before] = 0
            # remove background
            gray = fgbg.apply(gray)
            
            # draw the circles around the wells
            for i in wells_before:
                # draw the outer circle
                cv2.circle(gray,(i[0],i[1]),i[2],(211,211,211), 2)
                # draw the center of the circle
                #cv2.circle(gray,(i[0],i[1]),2,(0,0,0),3)
        
            cv2.imshow('frame', gray)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    else:
        break
cap.release()
cv2.destroyAllWindows()





# reasonable at finding cops; some false positives 
# here's the before drop video
cap = cv2.VideoCapture('day5/pl1_day5.mov')
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 

while(cap.isOpened()):
    frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
    ret, frame = cap.read()
    
    if ret==True:
        # once frame number goes past drop, stop
        if frame_n >= f_drop:
            break
        else:
            # convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # make area outside wells black
            gray[mask_before] = 0
            frame[mask_before] = 0
            # remove background
            gray = fgbg.apply(gray)
            
            # find copepods
            cops = cv2.goodFeaturesToTrack(gray,
                                           maxCorners=24,
                                           qualityLevel=0.5,
                                           minDistance = 10,
                                           blockSize = 4)
            
            # draw the circles around the wells
            for i in wells_before:
                # draw the outer circle
                cv2.circle(gray,(i[0],i[1]),i[2],(211,211,211), 2)
                # draw the center of the circle
                #cv2.circle(gray,(i[0],i[1]),2,(0,0,0),3)
            
            # draw circles around the cops
            try:
                cops.any()
            except AttributeError:
                next
            else:
                cops = np.uint16(np.around(cops))
                for i in cops:                    
                    # draw the outer circle
                    cv2.circle(frame,(i[0][0],i[0][1]),3,(0,0,255), 2)
                
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    else:
        break
cap.release()
cv2.destroyAllWindows()







# pick just one well
x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))   
xc, yc, rad = wells_before[1]
d2 = (x - xc)**2 + (y - yc)**2
maskx = d2 > rad**2

# see how well cop is detected
# bounces around when not moving because it fades into bckgd
# without bckg subtraction, though, not even recognized...
cap = cv2.VideoCapture('vid/pl1_day5.mov')
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
x, y = None, None
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
            # remove b1ackground
            gray = fgbg.apply(gray)
            
            # find a copepod
            corners = cv2.cornerMinEigenVal(gray, blockSize = 5)
            cop_qual = corners.max()
            
            # value suggestive of moving cop
            if cop_qual != None and cop_qual > 0.1:
                # if find copepod, extract x, y coordinates
                cops = cv2.goodFeaturesToTrack(gray, maxCorners=1,
                                               qualityLevel=0.75,
                                               minDistance = 10,
                                               blockSize = 5)
                cops = np.uint16(np.around(cops))
                x, y = cops[0][0][0], cops[0][0][1]
                out_row = np.array([frame_n, x, y, cop_qual])
                
                # draw circles around the cop
                cv2.circle(frame,(x,y),4,(0,0,255), 2)
            else:
                # if no copepod found, use x, y coord from previous frame
                out_row = np.array([frame_n, x, y, cop_qual])
            
            # create output array
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
cap.release()
cv2.destroyAllWindows()


# distribution of quality values
#n, bins, patches = plt.hist(cop_qual_out, 30, facecolor='green', alpha=0.75)


q_df = pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'detection'])
q_df.to_csv("out_test4.csv")

q_df['x2'] = q_df['x'].shift(-1)
q_df['y2'] = q_df['y'].shift(-1)
#q_df['distance'] = np.sqrt( (q_df['x2'] - q_df['x'])^2 + (q_df['y2'] - q_df['y'])^2 )
# TO DO WITH DF
# shorten to standard length before and after drop (1 min)
sec = np.arange(0, 60.01, 1/8)
# deal with non-moving starts NONE
# calculate variables - distance moved each frame
# quality control - similar to manual?
sec = np.arange(0, 60.01, 1/8)






# test blob detect
cap = cv2.VideoCapture('vid/pl1_day5.mov')
# model for background subtraction
fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 

# Setup SimpleBlobDetector parameters.
params = cv2.SimpleBlobDetector_Params()
 
# Change thresholds
params.minThreshold = 0;
params.maxThreshold = 255;
 
# Filter by Area.
params.filterByArea = True
params.minArea = 8
 
# Create a detector with the parameters
ver = (cv2.__version__).split('.')
if int(ver[0]) < 3 :
    detector = cv2.SimpleBlobDetector(params)
else :
    detector = cv2.SimpleBlobDetector_create(params)

while(cap.isOpened()):
    frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
    ret, frame = cap.read()
    
    if frame_n == drop: # at drop, reset background subtractor, record no dat
        fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False)
    if ret==True:
        # once frame number goes past drop, stop
        # convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray[maskx] = 0
        frame[maskx] = 0
        # remove blackground
        gray = fgbg.apply(gray)
        gray = cv2.bitwise_not(gray)
        
        
        keypoints = detector.detect(gray)
        if len(keypoints) > 0:
            # Draw detected blobs as red circles.
            # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
            gray = cv2.drawKeypoints(gray, keypoints, np.array([]), (0,0,255),
                                     cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            blobs = len(keypoints)
            (x,y), size = keypoints[0].pt, keypoints[0].size
        else:
            next
        
        cv2.imshow('frame', gray)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    else:
        break
cap.release()
cv2.destroyAllWindows()













#TRY TO OUTPUT VID
## WOULD LIKE TO WRITE FILES, BUT I LACK THE CODECS APPARENTLY
