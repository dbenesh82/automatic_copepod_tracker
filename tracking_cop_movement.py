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
from pathlib import Path


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
    Get n random images before and after drop. Returns image arrays.
    Used to get average position of wells across a random set of frames.
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
    Takes in a series of frames, finds the circles (wells).
    Returns their mean x-y position and radius.
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




def find_copepod(binary_frame):
    '''
    Take in binary image, returns the identified blobs.
    Parameters set to find moving cop, i.e. when it is in foreground not background.
    Returns whether cop was found, x-y coordinates, cop size, and number of blobs identified.
    Helper in the track_copepod function.
    '''
    # setup blob detector parameters.
    params = cv2.SimpleBlobDetector_Params()
    # threshold from black to white
    params.minThreshold = 0;
    params.maxThreshold = 255;
    # only blobs bigger than 7 pixels area, avoids noise, finds cop
    params.filterByArea = True
    params.minArea = 8
    # create a detector with the parameters
    ver = (cv2.__version__).split('.')
    if int(ver[0]) < 3 :
        detector = cv2.SimpleBlobDetector(params)
    else :
        detector = cv2.SimpleBlobDetector_create(params)
    
    # use detector
    keypoints = detector.detect(binary_frame)
    blobs = len(keypoints)
    cop_found = blobs > 0
    
    # if cop found, extract data
    if cop_found:
        (x,y), cop_qual = keypoints[0].pt, keypoints[0].size
    else:
        x,y,cop_qual = None,None,None
    return(cop_found, x, y, cop_qual, blobs)




def track_copepod(well, video):
    # create masks to isolate the well, one for before and one for after drop
    tot_frames, vid_width, vid_height = video_attributes(video)
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
    # initialize frame and output data
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_before] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        print(frame_n)
        ret, frame = cap.read()
        
        if ret==True:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if frame_n == drop: # if at drop, reset background subtractor, record no data
                fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False)
                frame[mask_after] = 0
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
                    # reassign cop coord if it was found (moving)
                    xp, yp = xc, yc
                else:
                    # if cop not found, use x-y coord from previous frame
                    out_row = np.array([frame_n, xp, yp, blobs, cop_qual])
                    if xp is not None:
                        cv2.circle(frame,(int(xp),int(yp)),4,(255,0,0), 2)
            

                # create output array, frame-by-frame
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


def extract_plate_day_from_vid_file_name(vid_file):
    fname = Path(vid_file).stem
    plate, day = fname.split("_")
    plate = [s for s in plate if s.isdigit()]
    
    if len(plate) > 1:
        plate = ''.join(plate)
    else:
        plate = '0' + plate[0]

    day = [s for s in day if s.isdigit()]
    day = ''.join(day)
    
    return(plate, day)



vid_file = 'vid/pl1_day5.mov'
plate, day = extract_plate_day_from_vid_file_name(vid_file)
tot_frames, vid_width, vid_height = video_attributes(vid_file)
drop = find_drop(vid_file)
rand_imgs_before, rand_imgs_after = get_random_images(vid_file, tot_frames, drop, 50)
wells_before = find_wells(rand_imgs_before) # get average well position before
wells_after = find_wells(rand_imgs_after) # get average well position after




# need to wrangle output data


def wrangle_cop_data(df):
    '''
    Takes data frame from track_copepod. Standardizes it.
    '''
    # cut too many frames before and after drop
    before_drop = df.iloc[drop-1-(8*60):drop-1]
    after_drop = df.iloc[drop-1:drop + 8*60]
    out_df = pd.concat([before_drop, after_drop])
    if len(out_df) == 961: # number of frames corresponding to two minutes
        out_df['sec'] = np.arange(0, 961/8, 1/8) # add seconds
    else:
        out_df['sec'] = np.arange(0, len(out_df)/8, 1/8)
        # WORKS FOR STD CASE, NEED TO ADJUST FOR VIDS WITH TOO FEW FRAMES

    # fill in missing coordinates at beginning; assumes small first move
    for i in range(len(out_df['x'])):    
        if out_df.iloc[i]['x'] is not None:
            x,y = out_df.iloc[i]['x'], out_df.iloc[i]['y']
            out_df.loc[0:i-1,'x'] = x
            out_df.loc[0:i-1,'y'] = y
            break

    # calculate distance, remove x,y
    out_df['x2'] = out_df['x'].shift(-1)
    out_df['y2'] = out_df['y'].shift(-1)
    out_df['distance'] = ( ((out_df['x2'] - out_df['x'])**2 + (out_df['y2'] - out_df['y'])**2) )**0.5
    
    # calculate dot product too
    
    # remove coordinates after calculating needed info
    out_df = out_df.drop(['x2','y2'], axis = 1)
    
    return(out_df)




# run on whole plate
def track_whole_plate(video):
    # list of well ids
    well_ids = ['1A', '1B', '1C', '1D',
           '2A', '2B', '2C', '2D',
           '3A', '3B', '3C', '3D',
           '4A', '4B', '4C', '4D',
           '5A', '5B', '5C', '5D',
           '6A', '6B', '6C', '6D']
    
    plate, day = extract_plate_day_from_vid_file_name(video)

    for w in range(len(well_ids)):
        out_df = wrangle_cop_data(track_copepod(w, video))
        well_id = well_ids[w]
        out_fname = plate + "_" + well_id + "_" + day + ".csv"
        out_df.to_csv('track_data/' + out_fname)
        


track_whole_plate(vid_file)


