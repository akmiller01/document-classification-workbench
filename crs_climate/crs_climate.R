list.of.packages <- c("data.table","dotenv", "httr", "dplyr", "reshape2", "ggplot2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
lapply(list.of.packages, require, character.only=T)
rm(list.of.packages,new.packages)

setwd("~/git/document-classification-workbench/")

if(dir.exists("textdata/crs_climate")){
  unlink("textdata/crs_climate", recursive=T)
  dir.create("textdata/crs_climate")
}

load("~/git/fao-food-security/large_input/crs.RData")
keep = c("CRS ID", "Year", "Donor Name",
            "Project Title", "Short Description", "Long Description",
         "Climate Mitigation","Climate Adaptation")
crs = crs[,keep,with=F]
gc()

donors = c(
  "Germany"
  ,"United States"
  ,"EU Institutions"
  # ,"Canada"
  # ,"Japan"
  # ,"United Kingdom"
  # ,"Switzerland"
  # ,"Australia"
  # ,"Spain"
  # ,"Sweden"
)

crs = subset(crs, Year >= 1998
             # & `Donor Name` %in% donors
)
gc()

crs$climate = (
  crs$`Climate Mitigation` %in% c(1, 2)
) | (
  crs$`Climate Adaptation` %in% c(1, 2)
)

climate_count_by_year = crs[,.(count=.N),by=.(Year, climate)]
ggplot(climate_count_by_year, aes(x=Year, y=count, group=climate, fill=climate)) +
  geom_area()

crs$text = paste(
  crs$`Project Title`,
  crs$`Short Description`,
  crs$`Long Description`
)

drop = c("Project Title", "Short Description", "Long Description",
         "Climate Mitigation","Climate Adaptation")
crs[,drop] = NULL
gc()
crs$text_dup = duplicated(crs$text)
crs = subset(crs, !text_dup)
crs$text_dup = NULL

crs$id = c(1:nrow(crs))

no_climate = subset(crs, climate == F)
climate = subset(crs, climate == T)
rm(crs)
gc()

set.seed(1337)
no_climate = no_climate %>% slice_sample(n=nrow(climate))
crs_balanced = rbind(no_climate, climate)

pb = txtProgressBar(max=nrow(crs_balanced), style=3)
for(i in 1:nrow(crs_balanced)){
  setTxtProgressBar(pb, i)
  activity = crs_balanced[i,]
  activity_text = activity$text
  activity_id = activity$id
  filename = paste0("./textdata/crs_climate/", activity_id, ".txt")
  writeLines(activity_text, filename)
}
close(pb)
crs_balanced$climate_label = "No adaptation or mitigation as a principle or significant objective"
crs_balanced$climate_label[which(crs_balanced$climate == 1)] = "Adaptation or mitigation as a principle or significant objective"

crs_balanced = crs_balanced[,c("id", "CRS ID", "climate_label", "Year", "Donor Name"), with=F]
fwrite(crs_balanced, "./metadata/crs_climate.csv")
