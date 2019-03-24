#!/usr/bin/python3 
import sys
import os
import datetime
import operator
import random
from collections import OrderedDict 
from math import *
from numpy  import *
from subprocess import *

OUTPUTDIR='./output'
firstDay=-1
devList=OrderedDict() #{}  #[device] = [all values possible]
dataSet=OrderedDict() #{}
mrules=OrderedDict() #{}   #model rules = [n] =(antecedent, consequent, support, lift, confidence)
nSlots=-1
#calculates slot based on time(hh:mm:ss) and slot_interval(min)
def getSlot(strtime,slot_interval):
    hours=int(strtime[:2])
    minutes=int(strtime[3:5])
    slot=(((hours*60) + (minutes))//slot_interval)
    return slot

#calculates day of week based on date(datetime.date())
def getDow(strdate):
    ndow=strdate
    if not is_number(ndow):
        try:
            dow=datetime.date(int(strdate[:4]),int(strdate[5:7]),int(strdate[8:]))
            ndow=dow.weekday()
        except ValueError:
            print(strdate)
            exit(0)
    if ndow==6: return "sun"
    elif ndow==0: return "mon"
    elif ndow==1: return "tue"
    elif ndow==2: return "wed"
    elif ndow==3: return "thu"
    elif ndow==4: return "fri"
    elif ndow==5: return "sat"
    else: return "ukn"

#check if value is numeric
def is_number(strvalue):
    try:
        float(strvalue)
        return True
    except ValueError:
        return False

#discretize states
def getState(strdev,strval):
    if strdev in devList:
#        print("->"+strval+"<-",strdev,devList[strdev])
        if not strval: 
            if isinstance(devList[strdev],list): strval=random.choice(devList[strdev])
            else: strval=devList[strdev]
            
        if is_number(strval): 
            if float(strval) <= devList[strdev]:
                return "LOW"
            else:
                return "HIGH"
        else:
            if strval in devList[strdev]:
                return strval
    return "-"

def countStates(strdev):
    count=0
    for dev in dataSet.keys():
        if strdev in dev:
            count+=1
    if count == 1: return 2
    return count

def transformDataset():
    for dev in dataSet.keys():
        for slot in range(0,nSlots):    
            n=dataSet[dev][slot]
            base=countStates(dev)
            if base == 1: base=2
            if n > base : 
                dataSet[dev][slot]=round(math.log(n+1,base),2)  #laplace +1:)
            else:
                dataSet[dev][slot]=0
            #print(n,"-->",dataSet[dev][slot])

#discretize continue values, remove duplicate registers
#and split by day of week and checkpoints
def splitData(strfile,islot,cdow,fdow):
    lastState=OrderedDict() #{} #tuple with laststate and slot -- avoid duplicated info
    counterCP=1 #counter checkpoints
    dirpath=OUTPUTDIR+"/"+str(cdow)+"-"+fdow+"/checkpoint"+str(counterCP).zfill(3)    #./<DOW>/<CHECKPOINT_N>
    os.mkdir(dirpath)
    foutput=open(dirpath+"/raw.log","w") #create new file
    foutput.write("slot,device,state\n")
    finput=open(strfile,"r") #open main file
    currentDate=""
    nextDate=""
    nline=0
    lastLine=""
    for fline in finput:
        linearr=fline.replace('\n','').split(' ') #ignoring missing lines
        if len(linearr) >= 4:
            date=linearr[0]
            time=linearr[1]
            device=linearr[2]
            state=linearr[3]
#            date,time,device,state=fline.replace('\n','').split(' ') #src file informations
            if getDow(date) == fdow:
                nline+=1
                currentDate=datetime.date(int(date[:4]),int(date[5:7]),int(date[8:]))
                if nline==1: 
                    nextDate=currentDate+datetime.timedelta(days=scan_days)

                if currentDate >= nextDate: #next checkpoint or end of file
                    foutput.close()
                    if currentDate == nextDate: #go to next checkpoint
                        counterCP+=1
                        nextDate=nextDate+datetime.timedelta(days=scan_days)
                        dirpath=OUTPUTDIR+"/"+str(cdow)+"-"+fdow+"/checkpoint"+str(counterCP).zfill(3)    #./<DOW>/<CHECKPOINT_N>
                        os.mkdir(dirpath)
                        foutput=open(dirpath+"/raw.log","w") #create new file
                        foutput.write("slot,device,state\n")
                    else:   #end of file
                        break
                newLine=str(getSlot(time,islot))+","+device+","+getState(device,state)+"\n" 

                #remove sequential and repeated registers in same slot: 99,75%
                if (device not in lastState.keys()) or (lastState[device][0] != getState(device,state)) or (lastState[device][1] != int(getSlot(time,islot))):
                   lastState[device]=[getState(device,state), int(getSlot(time,islot))];
                   foutput.write(newLine) #write
                
                #remove sequential and repeated registers(considere the same state in different slots) 100%
                #if (device not in lastState.keys()) or (lastState[device][0] != getState(device,state)):
                #   lastState[device]=[getState(device,state), int(getSlot(time,islot))];
                #   foutput.write(newLine) #write
                
                #Consider all dataset
                #if (device not in lastState.keys()): 
                #    lastState[device]=[getState(device,state), int(getSlot(time,islot))];
                #foutput.write(newLine) #write
    finput.close()


def getDevices(strfile):
    nline=0
    finput=open(strfile,"r") 
    for fline in finput:
        nline+=1
        #split line
        linearr=fline.replace('\n','').split(' ') #ignore missing data
        if len(linearr) >= 4: #ignore missing data
            date=linearr[0]
            device=linearr[2]
            state=linearr[3]
            if nline == 1:
                firstDay=datetime.date(int(date[:4]),int(date[5:7]),int(date[8:])).weekday()
            #collect devices
            if device in devList:
                if state not in devList[device]:
                    if state == "": state=random.choice(devList[device])
                    devList[device].append(state)
            else:
                devList[device]=[state]
#        else:  print(nline,fline)
    finput.close()
    for i in devList.keys():
        if is_number(devList[i][0]):
            minV=float(min(devList[i]))
            maxV=float(max(devList[i]))
            avg=(minV+maxV)/2
            devList[i]=float(avg)
    return firstDay


#read splited files and create datasets
def fillDataset(strfile): #updates dataSet on each analysis
    finput=open(strfile,"r")
    next(finput)
    for fline in finput:
        slot,device,state=fline.replace('\n','').split(',')
        dsitem=device+"-"+state
        if dsitem not in dataSet.keys():
            v=zeros(nSlots,dtype=float)
            dataSet[dsitem]=v
        dataSet[dsitem][int(slot)]+=1
    finput.close()

def getRuleFrequency(Apattern,Cpattern):
    statesSupport=OrderedDict() #{}
    for i in range(0,nSlots):  #for each slot
        if ("-" not in Apattern[i]) and ("-" not in Cpattern[i]):
            ruleStates=Apattern[i]+"-"+Cpattern[i]
            if ruleStates not in statesSupport.keys():
                statesSupport[ruleStates]=0
            statesSupport[ruleStates]+=1
    return statesSupport;

def getFrequency(devPattern):
    statesSupport=OrderedDict() #{}
    for i in range(0,nSlots):  #for each slot
        if "-" not in devPattern[i]:
            if devPattern[i] not in statesSupport.keys():
                statesSupport[devPattern[i]]=0
            statesSupport[devPattern[i]]+=1
    return statesSupport

 
def getPattern(device):
    devSet=OrderedDict() #{}
    devPattern=["-" for x in range(0,nSlots)] #array of pattern
    for key in dataSet.keys(): 
        if device in key: devSet[key]=dataSet[key]
    for i in range(0,nSlots):
        maxV=0; maxS='-';  maxE=0
        for k in devSet.keys():
            if maxV < devSet[k][i]: #check if current is greater than last
                maxV=devSet[k][i]
                maxS=k
                maxE=0
            elif maxV == devSet[k][i]: maxE+=1     #equals probability
        if maxE > 0: maxV=0; maxS='-' # ignores when slot has equals probability
        if maxV > 0: d,s=maxS.split("-"); devPattern[i]=s #store the greater state
    return devPattern


def createTransactions(strfile,devicesPattern):
    devSet=OrderedDict() #{}
    fillFile=False
    foutput=open(strfile,"w");
    for i in range(0,nSlots):
        transaction=""
        counter=0
        for key in devicesPattern.keys():
            if "-" not in devicesPattern[key][i]:
                if counter > 0:
                    transaction+=", "+key+"-"+devicesPattern[key][i]
                else: 
                    transaction+=key+"-"+devicesPattern[key][i]
                    counter+=1
        if len(transaction)>0:
            foutput.write(transaction+"\n")
            fillFile=True
    foutput.close()
    return fillFile

def savePattern(filepath,devicesPatterns):
    foutput=open(filepath,"w")
    header="device-state,"
    for i in range(0,nSlots):
        header+="slot-"+str(i)
        if i < nSlots-1: header+=","
    foutput.write(header+'\n')
    line=""
    for dev in devicesPatterns.keys():
        line=dev+","
        for slot in range(0,nSlots):
            line+=str(devicesPatterns[dev][slot])
            if slot < nSlots-1: line+=","
        foutput.write(line+'\n')
    foutput.close()

def extractARules(strpath,min_supp,min_lift,min_conf): 
    devicesPattern=OrderedDict() #{}
    for dev in devList.keys(): devicesPattern[dev]=getPattern(dev); #pattern of all devices
    savePattern(strpath+"/patterns.log",devicesPattern) 
    #create dataset of transaction
    if createTransactions(strpath+"/transactions.log",devicesPattern):
        Rcommand=["Rscript","aRules.r",strpath+"/transactions.log",str(min_supp),str(min_lift),str(min_conf),strpath+"/arules.log"]
        check_call(Rcommand, stdout=DEVNULL, stderr=STDOUT)
        return True
    return False

def extractRules(strpath,min_supp,min_lift,min_conf): #updates dataSet on each analysis
    devicesPattern=OrderedDict() #{}
    for dev in devList.keys(): devicesPattern[dev]=getPattern(dev); #pattern of all devices

    #exeute DMPSC extraction
    foutput=open(strpath+"/mrules.log","w")
    foutput.write("rules,support,confidence,lift,count\n")
    for antecedent in devList.keys():   #antecessor device-state
        Astates=getFrequency(devicesPattern[antecedent]) #for each valid state, extract max rule
        maxRule=''
        maxAntecedent=''
        maxConsequent=''
        maxSupp=0
        maxLift=-1
        maxConf=0
        maxCoun=0
        for Astate in Astates.keys():
            Asupport=Astates[Astate]/nSlots #antecedent support
            if Asupport >= min_supp:
                for consequent in devList.keys():
                    if antecedent not in consequent: 
                        Cstates=getFrequency(devicesPattern[consequent])
                        for Cstate in Cstates.keys():
                            Csupport=Cstates[Cstate]/nSlots #consequent support
                            if Csupport >= min_supp:
                            
                                ACstates=getRuleFrequency(devicesPattern[antecedent],devicesPattern[consequent])
                                ACstate=Astate+"-"+Cstate
                                if ACstate in ACstates.keys():
                                    #rules metrics
                                    ACsupport=ACstates[ACstate]/nSlots     
                                    ACconfidence=ACsupport/Asupport
                                    AClift=ACconfidence/Csupport
#                                    print(antecedent+" "+Astate+"->"+consequent+" "+Cstate+"["+str(ACsupport)+", "+str(ACconfidence)+", "+str(AClift)+" ]"+str(nSlots))
                                    if (ACsupport >= min_supp) and (ACconfidence >= min_conf) and (AClift >= min_lift):
                                        if (ACsupport > maxSupp) or ((ACsupport == maxSupp) and (AClift > maxLift)) or ((ACsupport == maxSupp) and (AClift == maxLift) and (ACconfidence > maxConf)):
                                            maxRule="{"+antecedent+"-"+Astate+"} => {"+consequent+"-"+Cstate+"},"+str(ACsupport)+","+str(ACconfidence)+","+str(AClift)+","+str(ACstates[ACstate])
                                            maxAntecedent=antecedent+"-"+Astate
                                            maxConsequent=consequent+"-"+Cstate
                                            maxSupp=ACsupport
                                            maxLift=AClift
                                            maxConf=ACconfidence
                                            maxCount=ACstates[ACstate]
            if maxRule: 
                if (maxAntecedent not in mrules.keys()) and (maxAntecedent in dataSet.keys()):
                    mrules[maxAntecedent]=[maxConsequent,maxSupp,maxLift,maxConf,maxCount]
                    foutput.write(maxRule+"\n")
    foutput.close()

def saveDatabase(filepath):
    foutput=open(filepath,"w")
    header="device-state,"
    for i in range(0,nSlots):
        header+="slot-"+str(i)
        if i < nSlots-1: header+=","
    foutput.write(header+'\n')
    line=""
    for dev in dataSet.keys():
        line=dev+","
        for slot in range(0,nSlots):
            line+=str(dataSet[dev][slot])
            if slot < nSlots-1: line+=","
        foutput.write(line+'\n')
    foutput.close()

def compareRules(filepath,Rstatus,min_supp, min_lift,min_conf):
    checkedRules=OrderedDict()
    sawRules=OrderedDict()
    statsRules=zeros(6,dtype=int) #Arules, DMPSC rules, Checked, Hits, Miss, Unmatched
    statsRules[1]=len(mrules);
    if Rstatus:
        finput=open(filepath+"/arules.log","r")
        next(finput)
        for line in finput:
                statsRules[0]+=1
                arule,asupp,aconf,alift,acount=line.replace('\n','').replace('{','').replace('}','').split(',')
                Aitem,Citem=arule.split(" => ")

                if Aitem not in sawRules.keys(): sawRules[Aitem]=[Citem,asupp,alift,aconf,acount]

                if Aitem in checkedRules.keys():    #antecedent already checked
                    if Citem == mrules[Aitem][0]:   #rule equal
                        statsRules[2]+=1            #checked
                        if asupp == sawRules[Aitem][1] and alift == sawRules[Aitem][2] and aconf == sawRules[Aitem][3]:
                            statsRules[3]+=1        #equal metrics
                        else:
                            statusRules[4]+=1       #wrong rule
                else:                               #never checked
                    for itemA in mrules.keys():     #analyse whole mrules
                        if (Aitem == itemA):              #equal antecendet
                            if Citem == mrules[Aitem][0]:   #equal consequent
                                statsRules[2]+=1            #checked
                                statsRules[3]+=1            #hits
                                checkedRules[Aitem]=True
#                            else:
 #                               statsRules[4]+=1            #false negative
  #                              checkedRules[Aitem]=False
    statsRules[5]=statsRules[1]-(statsRules[3]+statsRules[4])
    if statsRules[0] > 0:
        foutput=open(filepath+"/missing.log","w")
        foutput.write("rules,support,confidence,lift,count\n");
        for i in mrules.keys():
            if i not in checkedRules.keys():
                #foutput.write(i+" -> "+str(mrules[i])+"\n")
                foutput.write("{"+i+"} => {"+str(mrules[i][0])+"},"+str(mrules[i][1])+","+str(mrules[i][3])+"," +str(mrules[i][2])+","+str(mrules[i][4])+"\n")
        foutput.close()
        #Run Centralized Apriori again with relaxed metrics
        Rcommand=["Rscript","aRules.r",filepath+"/transactions.log",str(min_supp),str(min_lift),str(min_conf),filepath+"/arules-permissive-metrics.log"]
        check_call(Rcommand, stdout=DEVNULL, stderr=STDOUT)
 
    return statsRules


if (len(sys.argv) == 7) and (os.path.isfile('./'+sys.argv[1])) and (int(sys.argv[2]) > 0) and (int(sys.argv[3])>0) and ((float(sys.argv[4])>0)and (float(sys.argv[4])<=1)) and (float(sys.argv[5])>1) and ((float(sys.argv[6])>0) and (float(sys.argv[6])<=1)):
    #get parameters
    fname=sys.argv[1]
    scan_days=int(sys.argv[2])
    slot_interval=int(sys.argv[3])
    nSlots=getSlot("23:59:59",slot_interval)+1 #Total slots
    msup=float(sys.argv[4])
    mlift=float(sys.argv[5])
    mconf=float(sys.argv[6])
    OUTPUTDIR="./out-"+str(scan_days)+"-"+fname
    #identify devices, check points(w/ lines) and states
    os.mkdir(OUTPUTDIR)

    freport=open(OUTPUTDIR+"/report.log","w")

    firstDay=getDevices(fname) #collect info about devices(id and values)
    print("File:",fname)
    print("Number of Devices:", len(devList))
    print("Scan Interval(per day)",scan_days)
    print("Slot Interval(in min)",slot_interval)
    print("Num of Slots: ",nSlots)
    print("Minimum Support:",msup)
    print("Minimum Lift:",mlift)
    print("Minimum Confidence:",mconf)
    print("---")
    freport.write("File: "+fname+"\n")
    freport.write("Number of Devices: "+str(len(devList))+"\n")
    freport.write("Scan Interval(per day): "+str(scan_days)+"\n")
    freport.write("Slot Interval(in min): "+str(slot_interval)+"\n")
    freport.write("Num of Slots: "+str(nSlots)+"\n")
    freport.write("Minimum Support: "+str(msup)+"\n")
    freport.write("Minimum Lift: "+str(mlift)+"\n")
    freport.write("Minimum Confidence: "+str(mconf)+"\n")
    freport.write("---")

    globalStats=zeros(6)
    globalComparisons=0

    for cDow in range(0,7): #for each day of week
        dataSet.clear() #independent dataSet by day of week
        dowV=(cDow+firstDay)%7
        print("\nDay of week: ",getDow(dowV))
        freport.write("\nDay of week: "+getDow(dowV)+"\n")
        dirpath=OUTPUTDIR+"/"+str(cDow)+"-"+getDow(dowV)
        os.mkdir(dirpath)
        splitData(fname,slot_interval,cDow,getDow(dowV)) #divide by current dow and checkpoints

        nCheckpoints=0

        dailyStats=zeros(6)
        
        for checkPoint in sorted(os.listdir(dirpath), key=lambda f: int(f.split("checkpoint")[1])):  
            #for each checkpoint created (performs analysis, creates rules and compares)

            nCheckpoints+=1
            filepath=dirpath+"/"+checkPoint
            fillDataset(filepath+"/raw.log") #updates dataSet on each analysis
            
            #before logaritmical transformation
            saveDatabase(filepath+"/database.log")
            transformDataset() 

            #knowledge extraction DMPSC
            extractRules(filepath,msup,mlift,mconf)
   
            #knowledge extraction Arules(R)
            Rstatus=extractARules(filepath,msup,mlift,mconf) #True-R Creates Rules, False-R No creates rules

            if Rstatus: globalComparisons+=1 

            #analysis
            checkpointStats=compareRules(filepath,Rstatus,msup,mlift-0.2,mconf-0.05)
            checkpointReportString="Checkpoint: "+str(checkPoint.split("checkpoint")[1])+", "
            checkpointReportString+="States: "+str(len(dataSet))+", "
            checkpointReportString+="Rules(R): "+str(checkpointStats[0])+", "
            checkpointReportString+="Rules(mAKE): "+str(checkpointStats[1])+", "
#            checkpointReportString+="Checked: "+str(checkpointStats[2])+", "
            checkpointReportString+="Hits: "+str(checkpointStats[3])+", "
#            checkpointReportString+="Miss: "+str(checkpointStats[4])+", "
#            checkpointReportString+="Unmatched: "+str(checkpointStats[5])+""
            checkpointReportString+="Miss: "+str(checkpointStats[5])+""
            
            print(checkpointReportString)
            freport.write(checkpointReportString+"\n")

            for i in range(0,len(dailyStats)):
                dailyStats[i]+=checkpointStats[i]

            saveDatabase(filepath+"/databaseT.log")
            mrules.clear()

        for i in range(0,len(globalStats)):
            globalStats[i]+=dailyStats[i]

    #statsRules=zeros(6,dtype=int) #Arules, DMPSC rules, Checked, Hits, Miss, Unmatched
        dailyTot=0
        dailyHit=0
        dailyMiss=0
        dailyUnm=0
        if dailyStats[1] > 0:
            dailyHit=dailyStats[3]/dailyStats[1]
            dailyMiss=dailyStats[4]/dailyStats[1]
            dailyUnm=dailyStats[5]/dailyStats[1]
            
        dailyReportString="Rates:"
        dailyReportString+="Hits: "+str(int(dailyStats[3]))+"("+str(dailyHit)+"), "
#        dailyReportString+="Miss: "+str(int(dailyStats[4]))+"("+str(dailyMiss)+"), "
#        dailyReportString+="Unmatched: "+str(int(dailyStats[5]))+"("+str(dailyUnm)+") "
        dailyReportString+="Miss: "+str(int(dailyStats[5]))+"("+str(dailyUnm)+") "

        print(dailyReportString)
        freport.write(dailyReportString+"\n");

    globalHits=0
    globalMiss=0
    globalUnmatched=0
    if globalStats[2] > 0:
        globalHits=globalStats[3]/globalStats[1]
        globalMiss=globalStats[4]/globalStats[1]
        globalUnmatched=globalStats[5]/globalStats[1]    

    globalReportString="\nExperiment Report:"
    globalReportString+="\nAverage Hits: "+str(globalHits)+"("+str(int(globalStats[3]))+")"
#    globalReportString+="\nAverage Miss: "+str(globalMiss)+"("+str(int(globalStats[4]))+")"
#    globalReportString+="\nAverage Unmatched: "+str(globalUnmatched)+"("+str(int(globalStats[5]))+")"
    globalReportString+="\nAverage Miss: "+str(globalUnmatched)+"("+str(int(globalStats[5]))+")"
    globalReportString+="\nNumber of comparisons: "+str(globalComparisons)
    print("\n---"+globalReportString+"\n---")
    freport.write("\n---"+globalReportString+"\n---")
else: 
    print("Wrong parameters: './parser.py <db_file> <days> <slot_interval> <min_support> <min_lift> <min_confidence>'")
    print("<db_file>: Files in format:  'YYYY-MM-DD HH:MM:SS.sssss DEVICE VALUE'")
    print("<days>: Days inteval to perform extractions")
    print("<slot_interval>: Time cIn minutes: NUM_SLOTS = ((24*60*60)/<SLOT_INTERVAL>) --- day_in_minutes/interval ")
    print("<min_support>: Minimum Support Threshold ( 0 > min_support <= 1 )")
    print("<min_lift>: Minumum Lift Threshold ( min_threshold > 1 )");
    print("<min_confidence>: Minimum Confidence Threshold ( 0 > min_confidence <= 1 )")
