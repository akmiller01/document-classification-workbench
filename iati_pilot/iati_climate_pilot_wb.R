list.of.packages <- c("data.table","dotenv", "httr", "dplyr", "jsonlite")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
lapply(list.of.packages, require, character.only=T)
rm(list.of.packages,new.packages)

setwd("~/git/document-classification-workbench/")

load_dot_env()
api_key = Sys.getenv("API_KEY")
authentication = add_headers(`Ocp-Apim-Subscription-Key` = api_key)

sector_cl = fread("extra/Sector.csv")[,c("code","name")]
sector_map = sector_cl$name
names(sector_map) = sector_cl$code
decode_sector = function(sector_code_column){
  res = list()
  for(i in 1:length(sector_code_column)){
    sector_codes = sector_code_column[[i]]
    if(!is.null(sector_codes)){
      res[[i]] = paste(unique(unname(sector_map[sector_codes])), collapse=" ")
    }else{
      res[[i]] = NA
    }
  }
  return(res)
}

is_null_vectorized <- function(x) {
  return(sapply(x, function(elem) identical(elem, NULL)))
}

concatenate_narratives <- function(narrative_df) {
  
  # Concatenate the columns row-wise
  concatenated_narratives_str <- apply(narrative_df, 1, function(row) {
    null_values = is_null_vectorized(row)
    non_empty_values <- row[!null_values]
    unique_non_empty = sapply(non_empty_values, unique)
    concat_non_empty = sapply(unique_non_empty, paste, collapse=" ")
    if (length(concat_non_empty) > 0) {
      paste(concat_non_empty, collapse = " ")
    } else {
      NA
    }
  })
  
  return(concatenated_narratives_str)
}


data_list = list()
data_index = 1

org_ref = "44000"
rows = 1000
len_result = 1
page_count = 0
next_cursor_mark = "*"
while(len_result > 0){
  page_count = page_count + 1
  message(page_count)
  activity_path <- paste0("https://api.iatistandard.org/datastore/activity/select?",
                          "q=(reporting_org_ref:(\"",
                          org_ref,
                          "\"))",
                          "&fl=iati_identifier,policy_marker_code,policy_marker_significance,*_narrative,sector_code,sector_percentage,transaction_sector_code&",
                          "wt=json&",
                          "sort=id asc&",
                          "rows=",rows,"&",
                          "cursorMark=", next_cursor_mark
  )
  
  activity_request <- GET(url = activity_path, authentication)
  stopifnot(activity_request$status_code==200)
  activity_response <- content(activity_request, encoding = "UTF-8", as = "text")
  activity_json = fromJSON(activity_response)
  next_cursor_mark = activity_json$nextCursorMark
  len_result = length(activity_json$response$docs)
  if(len_result > 0){
    docs = activity_json$response$docs
    docs$climate = NA
    for(i in 1:nrow(docs)){
      doc = docs[i,]
      climate_significant = 0
      cumulative_climate_percentage = 0
      if("sector_code" %in% names(docs)){
        if("sector_percentage" %in% names(docs)){
          if("000081" %in% doc$sector_code[[1]]){
            sector_index = which(doc$sector_code[[1]] == "000081")
            cumulative_climate_percentage = cumulative_climate_percentage + doc$sector_percentage[[1]][sector_index]
          }
          if("000811" %in% doc$sector_code[[1]]){
            sector_index = which(doc$sector_code[[1]] == "000811")
            cumulative_climate_percentage = cumulative_climate_percentage + doc$sector_percentage[[1]][sector_index]
            
          }
          if("000812" %in% doc$sector_code[[1]]){
            sector_index = which(doc$sector_code[[1]] == "000812")
            cumulative_climate_percentage = cumulative_climate_percentage + doc$sector_percentage[[1]][sector_index]
          }
        }
      }
      if(cumulative_climate_percentage >= 50){
        climate_significant = 1
      }
      if("transaction_sector_code" %in% names(docs)){
        if("000081" %in% doc$transaction_sector_code[[1]]){
          climate_significant = 1
        }
        if("000811" %in% doc$transaction_sector_code[[1]]){
          climate_significant = 1
        }
        if("000812" %in% doc$transaction_sector_code[[1]]){
          climate_significant = 1
        }
      }
      docs[i, "climate"] = climate_significant
    }
    if("sector_code" %in% names(docs)){
      docs$sector_code =
        decode_sector(
          docs$sector_code
        )
    }
    if("transaction_sector_code" %in% names(docs)){
      docs$transaction_sector_code = 
        decode_sector(
          docs$transaction_sector_code
        )
    }
    narrative_cols = names(docs)[which(endsWith(names(docs), "_narrative"))]
    narrative_cols = narrative_cols[which(!startsWith(narrative_cols, "sector"))]
    narrative_cols = narrative_cols[which(!startsWith(narrative_cols, "transaction_sector"))]
    narrative_df = docs[,narrative_cols]
    docs[,narrative_cols] = NULL
    docs$iati_text = concatenate_narratives(narrative_df)
    data_list[[data_index]] = docs
    data_index = data_index + 1
  }
  Sys.sleep(2)
}

activities = rbindlist(data_list, use.names=T)
activities$id = c(1:nrow(activities))
for(i in 1:nrow(activities)){
  activity = activities[i,]
  activity_text = paste(
    activity$iati_text,
    activity$sector_code,
    activity$transaction_sector_code
  )
  filename = paste0("./textdata/iati_climate_pilot_wb/", i, ".txt")
  writeLines(activity_text, filename)
}
activities$climate_label = "No adaptation or mitigation as a principle or significant objective"
activities$climate_label[which(activities$climate == 1)] = "Adaptation or mitigation as a principle or significant objective"

activities = activities[,c("id", "iati_identifier", "climate_label"), with=F]
fwrite(activities, "./metadata/iati_climate_pilot_wb.csv")

no_climate = subset(activities, climate_label == "No adaptation or mitigation as a principle or significant objective")
climate = subset(activities, climate_label != "No adaptation or mitigation as a principle or significant objective")

set.seed(1337)
no_climate = no_climate %>% slice_sample(n=nrow(climate))
activities_balanced = rbind(no_climate, climate)
fwrite(activities_balanced, "./metadata/iati_climate_pilot_wb_balanced.csv")
for(id in activities_balanced$id){
  file.copy(
    from=paste0("./textdata/iati_climate_pilot_wb/", id, ".txt"),
    to=paste0("./textdata/iati_climate_pilot_wb_balanced/", id, ".txt")
  )
}
