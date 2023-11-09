list.of.packages <- c("data.table", "tm", "SnowballC", "wordcloud", "RColorBrewer", "wordcloud2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)
lapply(list.of.packages, require, character.only=T)

setwd("~/git/document-classification-workbench/gdc")

text = readLines("all_text.txt")

# Function to identify and remove spaces
identify_and_remove_spaces <- function(string) {
  # Split the text into individual characters
  characters <- unlist(strsplit(string, " "))
  
  # Every other character is a space
  if(length(characters) >= nchar(string) / 2){
    clean_string = gsub(" ", "", string)
    return(clean_string)
  }
  return(string)
}

# Apply the function to the text_vector
cleaned_vector <- unname(sapply(text, identify_and_remove_spaces))
cleaned_vector = gsub("•|●","",cleaned_vector)

docs <- Corpus(VectorSource(cleaned_vector))
inspect(docs)

toSpace <- content_transformer(function (x , pattern ) gsub(pattern, " ", x))
docs <- tm_map(docs, toSpace, "/")
docs <- tm_map(docs, toSpace, "@")
docs <- tm_map(docs, toSpace, "\\|")

# Convert the text to lower case
docs <- tm_map(docs, content_transformer(tolower))
# Remove numbers
docs <- tm_map(docs, removeNumbers)
# Remove english common stopwords
docs <- tm_map(docs, removeWords, stopwords("english"))
# Remove your own stop word
# Remove punctuations
docs <- tm_map(docs, removePunctuation)
# Eliminate extra white spaces
docs <- tm_map(docs, stripWhitespace)
# docs <- tm_map(docs, stemDocument)

dtm <- TermDocumentMatrix(docs) 
dtm = removeSparseTerms(dtm, 0.999)
m <- as.matrix(dtm)
v <- sort(rowSums(m),decreasing=TRUE)
d <- data.frame(word = names(v),freq=v)
head(d, 10)

set.seed(1234)
wordcloud(words = d$word,
          freq = d$freq,
          # scale=c(max(d$freq),min(d$freq)),
          max.words=200, 
          random.order=FALSE,
          rot.per=0.35, 
          colors=brewer.pal(8, "Dark2"))

wordcloud2(data=d, size=1.6, color='random-dark')
