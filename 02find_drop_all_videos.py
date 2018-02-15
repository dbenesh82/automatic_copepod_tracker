# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 08:32:03 2018

@author: phosp

Here I extract the frame, in each video, where the plate is dropped. This
info is then added to the video_table, which is then in turn used in the 
tracking script (XXX.py).
"""

import pandas as pd
import cv2
from pathlib import Path
from skimage.measure import compare_ssim as ssim


### FUNCTION TO FIND THE DROP IN EACH PLATE

def find_drop(video, tot_frames):
    '''
    Takes in video, returns the frame at which plate is dropped
    '''
    fname = Path(v).name
    cap = cv2.VideoCapture(video) # open vid
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
            
            # if not in middle fifth of frames, skip
            if frame_n < tot_frames*0.4 or frame_n > tot_frames*0.6:
                next
            else:
                # compare consecutive frames to find most dissimilar ones
                img_simx = ssim(frame_p, frame_c)
                if img_simx < img_sim_min:
                    img_sim_min = img_simx
                    f_drop = frame_n
                        
            print("Finding drop", fname, round(frame_n/tot_frames * 100, 1), "%") # how far along?
            frame_p = frame_c
        else:
            break
    # return results
    if img_sim_min > 0.8:
        print("Minimum image similarity high. Drop not found?")
    return(int(f_drop), img_sim_min)
    cap.release()






# get list of all mov files
cwd = Path.cwd()
vid_folder = cwd.parent/"GxG_videos"
dirs = [x for x in vid_folder.iterdir() if x.is_dir()] # get all the directories in folder
vids_paths = []
for d in dirs:
    f1 = list(d.glob("*.mov"))        # list mov files in folder
    vids_paths = vids_paths + f1



# import video table
# if table with drop data has been created, import it, else table from '01create_video_data_table.py'
v_tbl_path = Path(cwd/"video_tbl/video_table_drop.csv")
if v_tbl_path.exists():
    out_df = pd.read_csv("video_tbl/video_table_drop.csv", index_col = 'index')
else:
    out_df = pd.read_csv("video_tbl/video_table.csv", index_col = 'index')



# Go through and find the drop in every video
for v in vids_paths:
    fname = Path(v).name # file name
    r_vid_tbl = out_df[out_df.file_name == fname] # match file name in vid table
    # if multiple matches, break loop
    if len(r_vid_tbl) != 1:
        print("Multiple files matched!")
        break
    # if drop value is not null, skip this video (already run)
    elif pd.notnull(r_vid_tbl.iloc[0]['drop']):
        print(fname + " has been processed")
        next
    # find the drop in the remaining cases
    else:
        drop, img_sim = find_drop(str(v), int(r_vid_tbl['frames']))
        out_df.loc[r_vid_tbl.index, 'drop'] = drop
        out_df.loc[r_vid_tbl.index, 'drop_img_sim'] = img_sim
        print(fname + " has been processed")
    # export the table to file after each iteration
    out_df.to_csv("video_tbl/video_table_drop.csv")


