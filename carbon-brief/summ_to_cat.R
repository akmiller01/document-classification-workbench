list.of.packages <- c("data.table", "httr", "dotenv", "dplyr", "jsonlite")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
lapply(list.of.packages, require, character.only=T)
rm(list.of.packages,new.packages)

setwd("~/git/document-classification-workbench/")

load_dot_env()
api_key = Sys.getenv("GOOGLE_API_KEY")
authentication = add_headers(`Ocp-Apim-Subscription-Key` = api_key)

cb_json = fromJSON(
  paste0(
    "https://sheets.googleapis.com/v4/spreadsheets/1uu-zaC6iYsMfhSfS1r3VZoTVrstRGechs0fJJSzDsZo/values/Total!A1:G?alt=json&key=",
    api_key,
    "&_=1705502124367"
  )
)
dat = data.frame(cb_json$values)
names(dat) = dat[1,]
dat = dat[2:nrow(dat),]

dat$Category[which(dat$Category=="OIl & gas")] = "Oil & gas"

dat$id = c(1:nrow(dat))
for(i in 1:nrow(dat)){
  row = dat[i,]
  summary_text = row$Summary
  filename = paste0("./textdata/carbon-brief/", i, ".txt")
  writeLines(summary_text, filename)
}
dat = dat[,c("id", "URL", "Category")]
fwrite(dat, "./metadata/carbon-brief.csv")