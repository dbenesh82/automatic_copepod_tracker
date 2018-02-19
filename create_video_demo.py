# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 14:17:07 2018

@author: phosp
"""


import numpy as np
import pandas as pd
import random
import cv2
from pathlib import Path
from tracking_cop_movement import get_random_images, find_wells



# get video info
video_tbl = pd.read_csv("video_tbl/video_table_drop.csv")
# get wells to track for each plate
wells_to_track = pd.read_csv("wells_to_track.csv")
# get list of all mov files
cwd = Path.cwd()
vid_path = cwd.parent/"GxG_videos/day5/pl1_day5.mov"
vid = str(vid_path)

fname = Path(vid_path).name # file name
r_vid_tbl = video_tbl[video_tbl.file_name == fname] # match file name in vid table
plate = r_vid_tbl.iloc[0]['plate']
day = r_vid_tbl.iloc[0]['day']
tot_frames = r_vid_tbl.iloc[0]['frames']
vid_width = r_vid_tbl.iloc[0]['width']
vid_height = r_vid_tbl.iloc[0]['height']
drop = int(r_vid_tbl.iloc[0]['drop'])
tracked = r_vid_tbl.iloc[0]['tracked']


rand_imgs_before, rand_imgs_after = get_random_images(vid, tot_frames, drop, 50)
wells_before = find_wells(rand_imgs_before)



def find_copepod(binary_frame):
    '''
    Take in binary image, returns the identified blobs.
    Parameters set to find moving cop, i.e. when it is in foreground not background.
    Returns whether cop was found, x-y coordinates, cop size, and number of blobs identified.
    Helper in the track_copepod functions.
    '''
    # setup blob detector parameters.
    params = cv2.SimpleBlobDetector_Params()
    # threshold from black to white
    params.minThreshold = 0;
    params.maxThreshold = 255;
    # only blobs bigger than 10 pixels area, does not avoid all noise
    params.filterByArea = True
    params.minArea = 10
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
        x,y = round(x, 2), round(y,2)
    else:
        x,y,cop_qual = None,None,None
    return(cop_found, x, y, cop_qual, blobs)


def track_copepod_before(well, video, wells_vec, drop, vid_width, vid_height):
    # create masks to isolate the well
    x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))
    xc, yc, rad = wells_vec[well]
    d2 = (x - xc)**2 + (y - yc)**2
    mask_before = d2 > rad**2
    
    # open video
    cap = cv2.VideoCapture(video)
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('vids/demo.mp4',fourcc, 32, (vid_width, vid_height))
    
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
    
    
    # run through video once to 'train' background model
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame[mask_before] = 0
        frame = fgbg.apply(frame)
        if frame_n >= drop:
                break
    
    # reset at initial frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_before] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    # output initial data
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    out_array = np.array([[0, xp, yp, blobs, cop_qual]])
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame = cap.read()
        
        if frame_n < 150:
            out.write(frame)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        elif frame_n < drop:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray[mask_before] = 0
            frame[mask_before] = 0
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
            out_array = np.append(out_array, [out_row], axis = 0)
            
            out.write(frame)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs', 'blob_size']))




track_copepod_before(13,vid,wells_before,drop,vid_width,vid_height)
