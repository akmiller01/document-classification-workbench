library(XML)
library(data.table)

setwd("~/git/document-classification-workbench/gdc")

fods = xmlParse('gdc.fods')
links = getNodeSet(fods, '//text:a')
hrefs = sapply(links, xmlGetAttr, name="xlink:href")
titles = sapply(links, xmlValue)
dat = data.table(id=1:length(links), url=hrefs, title=titles )
fwrite(dat, "../metadata/gdc.csv")
