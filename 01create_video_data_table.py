# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 07:43:39 2018

@author: phosp

Here I loop through the video files and extract basic information from them,
such as width, height, frame rate, etc. This information is exported to a
csv. It is then amended with additional information in the 
'02find_drop_all_videos.py' and XXX.py files.
"""

import pandas as pd
import cv2
from pathlib import Path

### FUNCTIONS TO EXTRACT BASIC RECORDING INFORMATION
def extract_plate_day_from_vid_file_name(video):
    '''
    Extract plate number and day of recording from video file name
    '''
    fname = Path(video).stem
    plate, day = fname.split("_")
    plate = [s for s in plate if s.isdigit()]
    
    if len(plate) > 1:
        plate = ''.join(plate)
    else:
        plate = '0' + plate[0]

    day = [s for s in day if s.isdigit()]
    day = ''.join(day)
    
    return(plate, day)


def video_attributes(video):
    '''
    Takes in video, returns number of frames, video width and video height
    '''
    cap = cv2.VideoCapture(video) # open vid
    # get vid basics, like frames, width, height
    tot_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_rate = round(cap.get(cv2.CAP_PROP_FPS), 3)
    return(tot_frames, vid_width, vid_height, frame_rate)
    cap.release() # close vid
    



# get list of all mov files
cwd = Path.cwd()
vid_folder = cwd.parent/"GxG_videos"
dirs = [x for x in vid_folder.iterdir() if x.is_dir()] # get all the directories in folder
vids_paths = []
for d in dirs:
    f1 = list(d.glob("*.mov"))        # list mov files in folder
    vids_paths = vids_paths + f1



# Create table with video attributes
for v in vids_paths:
    fname = Path(v).name
    print(fname)
    plate, day = extract_plate_day_from_vid_file_name(str(v))
    tot_frames, vid_width, vid_height, frame_rate = video_attributes(str(v))
    
    out_entry = pd.DataFrame({"file_name": fname,
                              "plate": plate,
                              "day": day,
                              "width": vid_width,
                              "height": vid_height,
                              "frames": tot_frames,
                              "fps": frame_rate,
                              "drop": None,
                              "tracked": "No",
                              "drop_img_sim": None}, index = [0])
    try:
        out_df
    except NameError:
        out_df = out_entry
    else:
        out_df = pd.concat([out_df, out_entry], ignore_index=True)

# export the table to file
out_df.to_csv("video_tbl/video_table.csv", index_label = "index")




    
    