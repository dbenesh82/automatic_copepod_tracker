# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 18:02:49 2018

@author: phosp

Here I have written several functions that track copepod movement through a video.
They rely on data from a video table previously created (02find_drop_all_videos.py).
The script loops through the video recordings, and tracks a subset of copepods 
in each recording. The tracking data is outputted to csv files identified as 
"plate_well_day.csv".
"""

import numpy as np
import pandas as pd
import random
import cv2
from pathlib import Path



### FUNCTIONS TO DEFINE PLATE CHARACTERISTICS USED IN TRACKING, LIKE THE POSITION OF THE WELLS 

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





### FUNCTIONS FOR TRACKING COPEPODS

def find_copepod(binary_frame, xp, yp):
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
    # only blobs bigger than 7 pixels area, does not avoid all noise
    params.filterByArea = True
    params.minArea = 7
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
        # if multiple blobs found, find blob closest to current position
        if len(keypoints) > 1 and xp is not None: 
            dist_min = 120
            for i in range(len(keypoints)):
                (x,y), cop_qual = keypoints[i].pt, keypoints[i].size
                dist = ( ((x - xp)**2 + (y - yp)**2) )**0.5
                if dist < dist_min:
                    i_min = i
                    dist_min = dist
            (x,y), cop_qual = keypoints[i_min].pt, keypoints[i_min].size
    # if no blob found, return previous coordinates
    else:
        x,y,cop_qual = xp, yp, None
    return(cop_found, x, y, cop_qual, blobs)




def track_copepod_before(well, video, wells_vec, drop, vid_width, vid_height):
    # create masks to isolate the well
    x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))
    xc, yc, rad = wells_vec[well]
    d2 = (x - xc)**2 + (y - yc)**2
    mask_before = d2 > rad**2
    
    # open video
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
    
    # run through video once to 'train' background model
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
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray, None, None)
    out_array = np.array([[0, xp, yp, blobs, cop_qual]])
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame = cap.read()
        
        if frame_n < drop:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray[mask_before] = 0
            frame[mask_before] = 0
            gray = fgbg.apply(gray)
            gray = cv2.bitwise_not(gray)
            
            # find a copepod
            cop_found, xc, yc, cop_qual, blobs = find_copepod(gray, xp, yp)
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
            
            #cv2.imshow('frame', frame)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs', 'blob_size']))



def track_copepod_after(well, video, wells_vec, drop, vid_width, vid_height):
    # create masks to isolate the well
    x, y = np.meshgrid(np.arange(vid_width), np.arange(vid_height))
    xc, yc, rad = wells_vec[well]
    d2 = (x - xc)**2 + (y - yc)**2
    mask_after = d2 > rad**2
    
    # open video
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
    
    # run through video once to 'train' background model
    cap.set(cv2.CAP_PROP_POS_FRAMES, drop)
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame = cap.read()
        if ret == True: 
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame[mask_after] = 0
            frame = fgbg.apply(frame)
        else:
            break
    
    # reset at initial 'drop' frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, drop)
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_after] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    # output initial data
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray, None, None)
    out_array = np.array([[drop, xp, yp, blobs, cop_qual]])
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        ret, frame = cap.read()
        
        if ret==True:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray[mask_after] = 0
            frame[mask_after] = 0
            gray = fgbg.apply(gray)
            gray = cv2.bitwise_not(gray)
            # find a copepod
            cop_found, xc, yc, cop_qual, blobs = find_copepod(gray, xp, yp)
         
            if cop_found:
                # make a row of data
                out_row = np.array([frame_n, xc, yc, blobs, cop_qual])
                # draw circle around cop
                cv2.circle(gray,(int(xc),int(yc)),4,(0,0,255), 2)
                # reassign cop coord if it was found (moving)
                xp, yp = xc, yc
            else:
                # if cop not found, use x-y coord from previous frame
                out_row = np.array([frame_n, xp, yp, blobs, cop_qual])
                if xp is not None:
                    cv2.circle(gray,(int(xp),int(yp)),4,(255,0,0), 2)
            
            # create output array, frame-by-frame
            out_array = np.append(out_array, [out_row], axis = 0)
            
            #cv2.imshow('frame', gray)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))




### FUNCTIONS TO WRANGLE THE OUTPUTTED TRACKING DATA

def fill_missing_xy(df):
    '''
    Takes combined data frame from track_copepod, before and after.
    Fills cases where copepod was not moving.
    '''
    # if all are missing, i.e. tracker did not detect movement, then
    # fill with arbitrary coordinate to be able to calculate zero distances
    if len(df) == df['x'].isnull().sum():
        df['x'] = 1
        df['y'] = 1
    # if last value is missing, no movement was detected after the drop
    # fill with previous position detected (forward fill)
    if df.iloc[len(df)-1]['x'] is None:
        i = len(df)-1
        x, y = df.iloc[i]['x'], df.iloc[i]['y']
        while x is None:
            i = i-1
            x, y = df.iloc[i]['x'], df.iloc[i]['y']
        df.loc[i:len(df)-1,'x'] = x
        df.loc[i:len(df)-1,'y'] = y
    # if still missing coordinates, such as at beginning, before movement detected
    # fill with next position detected (backward fill)
    if df['x'].isnull().sum() > 0:
        i = 0
        x = None
        for i in range(len(df)):
            x, y = df.iloc[i]['x'], df.iloc[i]['y']
            if x is None:
                j = i # row where empty cells start
                while x is None and i < len(df):
                    i += 1
                    x, y = df.iloc[i]['x'], df.iloc[i]['y']
                df.loc[j:i-1,'x'] = x
                df.loc[j:i-1,'y'] = y
            else:
                next
    return(df)

    

def add_sec_to_df(df, half):
    '''
    Add seconds to data frame. Assigns drop as happening at t = 60s.
    '''
    # create vectors of seconds
    l = len(df)
    if half == 'before':
        sec = np.arange(60 - (l * 1/8), 60, 1/8)
    elif half == 'after':
        sec = np.arange(60, 60 + (l * 1/8), 1/8)
    else:
        print("Non-valid entry for plate 'half'")
    # check if they are correct length and then assign them
    if l != len(sec):
        print("Wrong length of time vector!")
    df['sec'] = sec
    return(df)


def calculate_distance_dot_product(df):
    '''
    Takes in a combined data frame (before and after drop) and calculates
    the distance moved each frame and the dot product of vectors betweeen frames.
    '''
    out_df = df
    # calculate distance
    out_df['x_1'] = out_df['x'].shift(1)
    out_df['y_1'] = out_df['y'].shift(1)
    out_df['distance'] = ( ((out_df['x'] - out_df['x_1'])**2 + (out_df['y'] - out_df['y_1'])**2) )**0.5
    
    # calculate dot product
    out_df['x_2'] = out_df['x'].shift(2)
    out_df['y_2'] = out_df['y'].shift(2)
    out_df['dot_product'] = ((out_df['x_2'] - out_df['x_1']) * (out_df['x_1'] - out_df['x']) + 
          (out_df['y_2'] - out_df['y_1']) * (out_df['y_1'] - out_df['y']))
    
    # remove unneeded coordinates after calculating new vars
    out_df = out_df.drop(['x_2','y_2','x_1','y_1'], axis = 1)
    
    return(out_df)








### PUTTING IT ALL TOGETHER TO TRACK MULTIPLE COPEPODS ON A PLATE AND OUTPUT DATA TO CSV

def track_whole_plate(video):
    '''
    Takes in a video, writes csvs with the tracking data for each copepod
    '''
    # get info about the video from video table
    fname = Path(video).name # file name
    r_vid_tbl = video_tbl[video_tbl.file_name == fname] # match file name in vid table
    plate = r_vid_tbl.iloc[0]['plate']
    day = r_vid_tbl.iloc[0]['day']
    tot_frames = r_vid_tbl.iloc[0]['frames']
    vid_width = r_vid_tbl.iloc[0]['width']
    vid_height = r_vid_tbl.iloc[0]['height']
    drop = int(r_vid_tbl.iloc[0]['drop'])
    tracked = r_vid_tbl.iloc[0]['tracked']
    
    # track plate if not previously done so
    if tracked == 'Yes':
        print(fname + ' processed previously')
    else:    
        # find well outlines
        rand_imgs_before, rand_imgs_after = get_random_images(video, tot_frames, drop, 50)
        wells_before = find_wells(rand_imgs_before) 
        wells_after = find_wells(rand_imgs_after)    
        
        # list of well ids
        well_ids = ['1A', '1B', '1C', '1D',
               '2A', '2B', '2C', '2D',
               '3A', '3B', '3C', '3D',
               '4A', '4B', '4C', '4D',
               '5A', '5B', '5C', '5D',
               '6A', '6B', '6C', '6D']
        
        # which wells should be tracked
        wells_to_track_on_rec = wells_to_track[wells_to_track.plate == int(plate)]
        wells_to_track_on_rec = wells_to_track_on_rec[wells_to_track_on_rec.day == int(day)]
        wells_to_track_on_rec = wells_to_track_on_rec['well'].tolist()
        
        # convert plate and day to strings for naming outputted files
        if plate < 10:
            plate = "0" + str(plate)
        else:
            plate = str(plate)
        if day < 10:
            day = "0" + str(day)
        else:
            day = str(day)
        
        # loop through wells, tracking cop in each
        for w in range(len(well_ids)):
            well_id = well_ids[w]
            # check if well should be tracked
            if well_id not in wells_to_track_on_rec:
                next
            else: 
                # track cop
                print(fname + ": tracking " + well_id + " before drop")
                out_bef = track_copepod_before(w, video, wells_before, drop, vid_width, vid_height)
                print(fname + ": tracking " + well_id + " after drop")
                out_aft = track_copepod_after(w, video, wells_after, drop, vid_width, vid_height)
                # wrangle data
                out_bef = add_sec_to_df(out_bef, 'before')
                out_aft = add_sec_to_df(out_aft, 'after')
                out_df = pd.concat([out_bef, out_aft], ignore_index = True)
                out_df = fill_missing_xy(out_df)        
                out_df = calculate_distance_dot_product(out_df)
                # output data frame to file
                out_fname = plate + "_" + well_id + "_" + day + ".csv"
                out_df.to_csv('track_data/' + out_fname)
                print('Finished tracking ' + well_id)
        # after loop, update video table, noting it was tracked, write to file
        video_tbl.loc[r_vid_tbl.index, 'tracked'] = 'Yes'
        video_tbl.to_csv("video_tbl/video_table_drop.csv")
        print('Finished ' + fname)






### LOOP THROUGH VIDEO FILES, TRACK SUBSET OF COPEPODS

# get video info
video_tbl = pd.read_csv("video_tbl/video_table_drop.csv")
# get wells to track for each plate
wells_to_track = pd.read_csv("wells_to_track.csv")
# get list of all mov files
cwd = Path.cwd()
vid_folder = cwd.parent/"GxG_videos"
dirs = [x for x in vid_folder.iterdir() if x.is_dir()] # get all the directories in folder
vids_paths = []
for d in dirs:
    f1 = list(d.glob("*.mov"))        # list mov files in folder
    vids_paths = vids_paths + f1


# track a random sample to compare with manual tracker
rvid = random.sample(range(len(vids_paths)), 100)
for r in rvid:
    vid = str(vids_paths[r])
    track_whole_plate(vid)

# loop through videos, track copepods in each
#for vid in vids_paths:
 #  track_whole_plate(str(vid))

