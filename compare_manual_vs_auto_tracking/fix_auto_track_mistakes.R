library(dplyr)
library(ggplot2)
setwd("C:/Users/phosp/OneDrive/Documents/Benesh/Research/G by G/04_5automatic_tracking/compare_manual_vs_auto_tracking")


# HERE IS STRATEGY FOR 'FIXING' TRACKER MISTAKES
# 1. Import tracking file
# 2. Make 'drop' variable
# 3. Remove zeros between jumps (when tracker did not detect anything), recalculate distance, dot product and angle between consecutive points
# 4. Suspicious points are those with huge dot product - set row with huge dot_product to the x y of current row
# 5. Repeat as large values could be created through re-assignments
# 6. Once no more suspicious jumps (outside of drop), re-integrate non-movements
# 7. Save file
# 8. Wrap 1-7 in function and loop over all the files exported from vids


fix_tracking_mistakes <- function(file_name){
  print(paste("Fixing file", file_name))
  
  # IMPORT FILE
  d <- file_name
  
  fil <- paste0("../../04_5automatic_tracking/track_data/", d)
  dx <- read.csv(file = fil, header = TRUE)
  fname <- substring(d, first = 1, last = nchar(d)-4)
  cop_name <- substring(d, first = 1, last = 5)
  plate <- substring(d, first = 1, last = 2)
  dx$fname <- fname
  dx$cop_name <- cop_name
  dx$plate <- plate
  
  
  # IDENTIFY DROP
  dx <- mutate(dx, drop = if_else((sec > 59.5 & sec < 60.51), 1, 0))
  
  
  # REMOVE NON-MOVEMENTS, RECALCULATE DOT PRODUCT
  dx2 <- filter(dx, distance !=0 | is.na(distance))%>%
    mutate(x0 = lag(x), x2 = lead(x), y0 = lag(y), y2 = lead(y))%>%
    mutate(dist1 = sqrt((x0 - x)^2 + (y0 - y)^2) )%>%
    mutate(dist2 = sqrt((x - x2)^2 + (y - y2)^2) )%>%
    mutate(dot_product = ((x2 - x) * (x - x0) + (y2 - y) * (y - y0)))%>%
    mutate(angle = acos(dot_product/(dist1 * dist2)) * 180/pi)%>%
    select(fname, cop_name, plate, frame, x, y, blobs, blob_size, sec,
           dist1, dist2, dot_product, angle, drop)
  
  
  # # compare where big dot products are (i.e. the bad points)
  # ggplot(dx, aes(x = x, y = y)) +
  #   geom_path() + 
  #   geom_point( aes(size = abs(dot_product), color = as.factor(drop)))
  # 
  # ggplot(dx2, aes(x = x, y = y)) +
  #   geom_path() + 
  #   geom_point( aes(size = abs(dot_product), color = as.factor(drop)))
  # 
  
  
  
  # SET SUSPICIOUS POINTS/TRACKER JUMPS TO PREVIOUS POSITION
  min_dp <- min(filter(dx2, drop != 1)$dot_product, na.rm = T)
  max_dp <- max(filter(dx2, drop != 1)$dot_product, na.rm = T)
  
  # which dot products are unusual? 
  # after plotting, decided to use cut off of bottom 2 and top 0.5 percentile, given skew of dot product distribution
  
  while(min_dp < -35 | max_dp > 200){
    for(i in seq_along(dx2$fname)){
      dp <- dx2$dot_product[i]
      
      if(dx2$drop[i] == 1) { # skip if part of 'drop'
        next
      } else if(is.na(dp) | (dp > -35 & dp < 200)) { # skip if no or reasonable dot product
        next
      } else { # otherwise reset coordinates
        dx2$x[i] <- dx2$x[i - 1]
        dx2$y[i] <- dx2$y[i - 1]
      }
    }
    # then recalculate dot products
    dx2 <- mutate(dx2, x0 = lag(x), x2 = lead(x), y0 = lag(y), y2 = lead(y))%>%
      mutate(dist1 = sqrt((x0 - x)^2 + (y0 - y)^2) )%>%
      mutate(dist2 = sqrt((x - x2)^2 + (y - y2)^2) )%>%
      mutate(dot_product = ((x2 - x) * (x - x0) + (y2 - y) * (y - y0)))%>%
      mutate(angle = acos(dot_product/(dist1 * dist2)) * 180/pi)%>%
      select(fname, cop_name, plate, frame, x, y, blobs, blob_size, sec, dist1, dist2, dot_product, angle, drop)
    
    min_dp <- min(filter(dx2, drop != 1)$dot_product, na.rm = T)
    max_dp <- max(filter(dx2, drop != 1)$dot_product, na.rm = T)
    
  }
  
  # # replot after changes
  # ggplot(dx2, aes(x = x, y = y)) +
  #   geom_path() + 
  #   geom_point( aes(size = abs(dot_product), color = as.factor(drop)))
  
  
  # REINTEGRATE NON-MOVEMENTS
  names(dx)
  dxx <- select(dx, fname, cop_name, plate, drop, frame, sec, blobs, blob_size) # not sure if blobs should be included
  dxx <- left_join(dxx, dx2)
  
  
  # LOOP THROUGH TO REASSIGN COORDINATES OF NON-MOVING POINTS
  for(i in seq_along(dxx$fname)){
    if(is.na(dxx$x[i])){
      dxx$x[i] <- dxx$x[i - 1]
      dxx$y[i] <- dxx$y[i - 1]
    }
  }
  
  # RECALCULATE DIST, DP
  dxx <- mutate(dxx, x0 = lag(x), x2 = lead(x), y0 = lag(y), y2 = lead(y))%>%
    mutate(dist1 = sqrt((x0 - x)^2 + (y0 - y)^2) )%>%
    mutate(dist2 = sqrt((x - x2)^2 + (y - y2)^2) )%>%
    mutate(dot_product = ((x2 - x) * (x - x0) + (y2 - y) * (y - y0)))%>%
    mutate(angle = acos(dot_product/(dist1 * dist2)) * 180/pi)%>%
    select(fname, cop_name, plate, frame, sec, drop, blobs, blob_size, x, y, distance = dist1, dot_product)
  
  
  # # COMPARE ORIGINAL WITH FIXED FILE
  # nrow(dx) == nrow(dxx)
  # summary(select(dx, distance, dot_product, blobs, blob_size))
  # summary(select(dxx, distance, dot_product, blobs, blob_size))
  # 
  # sum(dx$distance, na.rm=T)
  # sum(dxx$distance, na.rm=T)
  # 
  # dx_c <- left_join( select(dx, fname, frame, drop, dist_old = distance, dp_old = dot_product),
  #                    select(dxx, fname, frame, dist_new = distance, dp_new = dot_product))
  # ggplot(dx_c, aes(x = dist_old, y = dist_new, color = factor(drop))) + geom_point()
  # ggplot(dx_c, aes(x = dp_old, y = dp_new, color = factor(drop))) + geom_point()
  # 
  # OUTPUT FILE
  fil_out <- paste0("Fixed_tracker_outputs/", fname, "r.csv")
  write.csv(dxx, file = fil_out, row.names = FALSE)
}


# run all files
dfiles <- list.files(path = "../track_data/")
for(fil in dfiles){
  fix_tracking_mistakes(fil)
}






# # quality checks - no extreme dps, lower distances summed across recording, correlated across recordings
# # make pooled data table for original files
# if(exists('orig')) {rm(orig)}
# for(d in dfiles){
#   fil <- paste0("../../04_5automatic_tracking/track_data/", d)
#   dx <- read.csv(file = fil, header = TRUE)
#   fname <- substring(d, first = 1, last = nchar(d)-4)
#   cop_name <- substring(d, first = 1, last = 5)
#   plate <- substring(d, first = 1, last = 2)
#   dx$fname <- fname
#   dx$cop_name <- cop_name
#   dx$plate <- plate
#   if(exists('orig')){
#     orig <- rbind(orig, dx)
#   } else{
#     orig <- dx
#   }
# }
# 
# # make pooled data table for revised files
# rfiles <- list.files(path = "Fixed_tracker_outputs/")
# if(exists('revised')) {rm(revised)}
# for(d in rfiles){
#   fil <- paste0("Fixed_tracker_outputs/", d)
#   dx <- read.csv(file = fil, header = TRUE)
#   fname <- substring(d, first = 1, last = nchar(d)-5)
#   cop_name <- substring(d, first = 1, last = 5)
#   plate <- substring(d, first = 1, last = 2)
#   dx$fname <- fname
#   dx$cop_name <- cop_name
#   dx$plate <- plate
#   if(exists('revised')){
#     revised <- rbind(revised, dx)
#   } else{
#     revised <- dx
#   }
# }
# 
# orig <- mutate(dx, drop = if_else((sec > 59.5 & sec < 60.51), 1, 0))
# 
# # check a few x, ys (update index)
# f<-unique(orig$fname)[50]
# 
# ggplot(filter(orig, fname == f),
#               aes(x=x, y=y)) +
#   geom_path() +
#   geom_point(aes(color = factor(drop), size = abs(dot_product)), alpha = 0.3)
# 
# 
# ggplot(filter(revised, fname == f),
#        aes(x=x, y=y)) +
#   geom_path() +
#   geom_point(aes(color = factor(drop), size = abs(dot_product)), alpha = 0.3)
# 
# 
# 
# # sum across recordings (similar whether or not drop is removed)
# orig_pooled <- group_by(orig, fname)%>%
#   summarize(tot_dist_old = sum(distance, na.rm=T))
# 
# rev_pooled <- group_by(revised, fname)%>%
#   summarize(tot_dist_rev = sum(distance, na.rm=T))
# 
# pooled <- left_join(orig_pooled, rev_pooled)
# ggplot(pooled, aes(x = tot_dist_old, y = tot_dist_rev)) + geom_point()
# 
# # distance moved decreased by 40% on average after revisions
# pooled <- mutate(pooled, prop_reduction = 1-tot_dist_rev/tot_dist_old)
# summary(pooled)
