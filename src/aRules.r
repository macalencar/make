#!/usr/bin/Rscript
#parameters:argv[] = [TRANSACTIONS_FILEPATH, MIN_SUPPORT, MIN_LIFT, MIN_CONFIDENCE, OUTPUTFILE]
library("arules")
options(max.print=5000,digits=5)
args<-commandArgs(TRUE)

min_supp <- as.double(args[2])
min_lift <- as.double(args[3])
min_conf <- as.double(args[4])

dbfile <- read.transactions(args[1], sep=",", rm.duplicates=FALSE)
rulesList <- apriori(dbfile, parameter=list(minlen=2, maxlen=2, conf=min_conf, sup=min_supp))
rulesSubset <- subset(rulesList, subset = lift >= min_lift) #dont need filter min_conf or min_supp, apriori do automaticaly
sortedRules <- sort(rulesSubset, by=c("support","lift","confidence"))
write(sortedRules, file=args[5],sep=",", row.names=FALSE, quote=FALSE)

