library(ggplot2)
library(dplyr)
library(tidyr)

# read data
bd <- read.csv(file = "behav_combined_after_qc2.csv", header = TRUE)
infd <- read.csv(file = "GxG_inf.csv", header = TRUE, fileEncoding = "UTF-8-BOM") #excel attached BOM to csv
# change col names for behav data
bd <- select(bd, fname, cop_name, day, 
             slice = Slice.n., dist = Distance, pixel = Pixel.Value, 
             ok_col_names, ok_col_num, ok_row_num)%>%
  arrange(day, cop_name, slice)



# reduce data to needed var
infd <- mutate(infd, plate = substr(cop_name, 1, 2),
               well = substr(cop_name, 4, 5))%>%
  select(cop_name, plate, well, exposed, infected, dead, days_surv, cop_fam, parasite_fam)

# remove those where infection unknown
infd <- filter(infd, !is.na(infected))
# remove those that did not survive to have at least two recordings
infd <- filter(infd, days_surv > 8)

# loop through each cop, create table of days to observe each cop
for(i in seq_along(infd$cop_name)){
  cop = infd[i,]
  if(cop$dead == 0) {
    days = c(5,7,9,11,13,15,17,19,21)
  } else {
    days = seq(5, cop$days_surv - 2, by = 2)
  }
  rec_df = data.frame(cop_name = cop$cop_name, day = days)
  
  if(!exists('out_df')) {
    out_df = rec_df
  } else {
    out_df = rbind(out_df, rec_df)
  }
}
rm(rec_df, i, days, cop)

# re-add plate and well to df of wells to record
out_df <- left_join(out_df, select(infd, cop_name, plate, well))

# check distibution of infection for selected cops
table(infd$infected)
# do not need to record 3 times as many uninfecteds as infecteds
# especially given they are only in 5 groups (cop family), not 25 like infecteds (cop x parasite family)

# 120 per cop family seems like a good goal, about double the amount from just manual tracking
# take all those that were manually tracked
man_tracked <- unique(bd$cop_name)
tn <- table(infd$infected, infd$cop_fam)
# restrict to those not yet tracked for each cop family, sample random ones to bring up sample size to 120
infx <- filter(infd, !(cop_name %in% man_tracked), cop_fam == "I")
n <- tn[1,1] - length(infx$cop_name)
to_track1 <- sample(infx$cop_name, 120 - n)

infx <- filter(infd, !(cop_name %in% man_tracked), cop_fam == "II")
n <- tn[1,2] - length(infx$cop_name)
to_track2 <- sample(infx$cop_name, 120 - n)

infx <- filter(infd, !(cop_name %in% man_tracked), cop_fam == "III")
n <- tn[1,3] - length(infx$cop_name)
to_track3 <- sample(infx$cop_name, 120 - n)

infx <- filter(infd, !(cop_name %in% man_tracked), cop_fam == "IV")
n <- tn[1,4] - length(infx$cop_name)
to_track4 <- sample(infx$cop_name, 120 - n)

infx <- filter(infd, !(cop_name %in% man_tracked), cop_fam == "V")
n <- tn[1,5] - length(infx$cop_name)
to_track5 <- sample(infx$cop_name, 120 - n)

to_track <- c(man_tracked, to_track1, to_track2, to_track3, to_track4, to_track5)

# examine distribution of samples
infx <- filter(infd, cop_name %in% to_track)
table(infx$infected)
table(infx$infected, infx$cop_fam)
# looks better

# restrict recording data frame to just these cops; reduces by about a third
out_df <- filter(out_df, cop_name %in% to_track)

# output table
out_df <- select(out_df, cop_name, plate, well, day)

write.csv(out_df, file = "wells_to_track.csv", row.names = FALSE)
