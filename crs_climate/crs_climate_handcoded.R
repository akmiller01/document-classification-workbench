list.of.packages <- c("data.table","dotenv", "httr", "dplyr", "reshape2", "ggplot2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
lapply(list.of.packages, require, character.only=T)
rm(list.of.packages,new.packages)

setwd("~/git/document-classification-workbench/")

dat = fread("crs_climate/train_set.csv")

if(dir.exists("textdata/crs_climate_handcoded")){
  unlink("textdata/crs_climate_handcoded", recursive=T)
  dir.create("textdata/crs_climate_handcoded")
}

dat$id = 1:nrow(dat)
pb = txtProgressBar(max=nrow(dat), style=3)
for(i in 1:nrow(dat)){
  setTxtProgressBar(pb, i)
  activity = dat[i,]
  activity_text = activity$text
  activity_id = activity$id
  filename = paste0("./textdata/crs_climate_handcoded/", activity_id, ".txt")
  writeLines(activity_text, filename)
}
close(pb)

dat_meta = dat[,c("id", "relevance", "label")]
fwrite(dat_meta, "./metadata/crs_climate.csv")
