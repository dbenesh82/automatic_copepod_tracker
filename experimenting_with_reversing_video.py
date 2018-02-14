# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 08:47:52 2018

@author: phosp
"""


# reverse video
vid_file = 'vid/pl1_day5.mov'
# open video
cap = cv2.VideoCapture(vid_file)





# reverse video
vid_file = 'vid/pl1_day5.mov'
# open video
cap = cv2.VideoCapture(vid_file)
frame_n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
frame_n = int(frame_n)

while(cap.isOpened):
    #cap.set(cv2.CAP_PROP_POS_FRAMES, frame_n-1)
    ret, frame = cap.read()
    #frame_n = frame_n - 1
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if not ret:
        break
cap.release()
cv2.destroyAllWindows()







def track_copepod_reverse(well, video):
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
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
        
    # initialize from last frame and initialize output data
    cap.set(cv2.CAP_PROP_POS_FRAMES, tot_frames-1)
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_before] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    frame_n = tot_frames
    while(cap.isOpened()):
        print(frame_n)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_n-1)
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

            frame_n = frame_n - 1
            if frame_n < 0:
                break
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))



def track_copepod_forward(well, video):
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
    cap = cv2.VideoCapture(video)
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


outr = track_copepod_reverse(15, vid_file)
outf = track_copepod_forward(15, vid_file)








def track_copepod_reverse_before(well, video):
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
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
        
    # initialize from last frame and initialize output data
    cap.set(cv2.CAP_PROP_POS_FRAMES, drop-1)
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_before] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    frame_n = drop
    while(cap.isOpened()):
        print(frame_n)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_n-1)
        ret, frame = cap.read()
        
        if ret==True:
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
            try:
                out_array
            except NameError:
                out_array = [out_row]
            else:
                out_array = np.append(out_array, [out_row], axis = 0)

            frame_n = frame_n - 1
            if frame_n < 0:
                break
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))



def track_copepod_forward_before(well, video):
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
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
    
    while(cap.isOpened()):
        frame_n = cap.get(cv2.CAP_PROP_POS_FRAMES)
        print(frame_n)
        ret, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame[mask_before] = 0
        frame = fgbg.apply(frame)
        if frame_n == 150:
                cv2.imshow('test_frame', frame)
        if frame_n >= drop:
                break
        if ret != True:
            break
    
    # initialize frame and output data
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
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
                cv2.circle(gray,(int(xc),int(yc)),4,(0,0,255), 2)
                # reassign cop coord if it was found (moving)
                xp, yp = xc, yc
            else:
                # if cop not found, use x-y coord from previous frame
                out_row = np.array([frame_n, xp, yp, blobs, cop_qual])
                if xp is not None:
                    cv2.circle(gray,(int(xp),int(yp)),4,(255,0,0), 2)
            
            # create output array, frame-by-frame
            try:
                out_array
            except NameError:
                out_array = [out_row]
            else:
                out_array = np.append(out_array, [out_row], axis = 0)
            
            if frame_n >= drop:
                break
            cv2.imshow('frame', gray)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))



outr = track_copepod_reverse_before(15, vid_file)
outf = track_copepod_forward_before(10, vid_file)

outr.to_csv("outr.csv")
outf.to_csv("outf.csv")





def track_copepod_reverse_after(well, video):
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
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
        
    # initialize from last frame and initialize output data
    cap.set(cv2.CAP_PROP_POS_FRAMES, tot_frames-1)
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    old_gray[mask_before] = 0
    old_gray = fgbg.apply(old_gray)
    old_gray = cv2.bitwise_not(old_gray) # makes binary
    cop_found, xp, yp, cop_qual, blobs = find_copepod(old_gray)
    frame_n = tot_frames
    while(cap.isOpened()):
        print(frame_n)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_n-1)
        ret, frame = cap.read()
        
        if ret==True:
            # convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

            frame_n = frame_n - 1
            if frame_n < drop:
                break
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    # close video, return dataframe
    cap.release()
    cv2.destroyAllWindows()
    return(pd.DataFrame(out_array, columns = ['frame', 'x', 'y', 'blobs','blob_size']))



def track_copepod_forward_after(well, video):
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
    cap = cv2.VideoCapture(video)
    # model for background subtraction
    fgbg = cv2.createBackgroundSubtractorMOG2(history = 500,detectShadows = False) 
    # initialize frame and output data
    cap.set(cv2.CAP_PROP_POS_FRAMES, drop)
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


outr = track_copepod_reverse_after(15, vid_file)
outf = track_copepod_forward_after(15, vid_file)
