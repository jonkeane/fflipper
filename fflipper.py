import sys, re, os, subprocess
from datetime import datetime
from datetime import timedelta
import time
import elementtree
from elementtree import ElementTree as ET
from pipes import quote
import tkFileDialog


#-------------------------------------------------------------------------------
# Extract annotations from all tiers .eaf file (which is an XML file)
# creates a dictionary where each key is a tier name mapped to a list of tuples
# that include each annotation
#-------------------------------------------------------------------------------

def identifyTiers(file):
    verbose = False
    tree = ET.parse(file)
    root = tree.getroot()
    tiers = []
    for tier in root.findall('TIER'):
        tiers.append(tier.attrib['TIER_ID'])
    return tiers
    

def extractClipTier(file,tiers):
    verbose = False
    tree = ET.parse(file)
    root = tree.getroot()
    rootLen = len(root)    
    pairs = [(X.attrib['TIME_SLOT_ID'],X.attrib['TIME_VALUE']) for X in root[1]]
    timeDict = dict(pairs)
    if verbose: print(timeDict)
    clipTiers = []
    for tier in root.findall('TIER'):
        if verbose: print( tier.attrib['TIER_ID'])
        if tier.attrib['TIER_ID'] in tiers:
            annos = []
            for xx in tier:
                time1 = timeDict[xx[0].attrib['TIME_SLOT_REF1']]
                time2 = timeDict[xx[0].attrib['TIME_SLOT_REF2']]
                value = xx[0][0].text
                annos.append((time1, time2, value))
            clipTiers.append((tier.attrib['TIER_ID'],annos))
        else:
            continue
    if clipTiers == {}:
        print "No tier named 'Clips', please supply an eaf with one to segment on."
        exit
    # Find the media file
    # check? <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">
    header = root.findall('HEADER')
    media = header[0].findall('MEDIA_DESCRIPTOR')
    mediaPath = media[0].attrib['MEDIA_URL']
    # remove "file://" from the path
    mediaPath = mediaPath[7:] 
    return clipTiers,mediaPath

#-------------------------------------------------------------------------------
# Converts a tuple (in milliseconds) into frames given a frame rate
#-------------------------------------------------------------------------------

def millisToFrames(span, fps = (60.*(1000./1001.))):
    secsPerFrame = 1000./fps
    span = [int(float(span[0])/secsPerFrame), int(float(span[1])/secsPerFrame)]
    return span


#-------------------------------------------------------------------------------
# Converts a tuple (in frames) into milliseconds given a frame rate
#-------------------------------------------------------------------------------

def framesToMillis(span, fps = (60.*(1000./1001.))):
    secsPerFrame = 1000./fps
    span = [int(float(span[0])*secsPerFrame), int(float(span[1])*secsPerFrame+secsPerFrame)]
    return span


#-------------------------------------------------------------------------------
# Clipping function
#-------------------------------------------------------------------------------

def clipper(infile, outfile, tstart, tend, options, log, verbose=True):
    ''' clipps video with options '''
    #deinterlace+crop+scale '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [o2]; [o2] scale=852:480 [out]"'
    #deinterlace+crop '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [out]"'
    #deinterlace '-vf "[in] yadif=1 [out]"'
    dur = tend-tstart
    cmd = ''.join(['ffmpeg -i ',infile,' -ss ',str(tstart),' -t ',str(dur),' ',options,' -sameq -y ',outfile])
    if verbose: print cmd
    logFile = open(log, 'w')
    p = subprocess.Popen(cmd, shell=True, stdout=logFile, stderr=logFile)
    return p

#-------------------------------------------------------------------------------
# Number Appender
#-------------------------------------------------------------------------------

def f5(seq, idfun=None):  
    # order preserving 
    if idfun is None: 
        def idfun(x): return x 
    seen = {} 
    result = [] 
    for item in seq: 
        marker = idfun(item) 
        # in old Python versions: 
        # if seen.has_key(marker) 
        # but in new ones: 
        if marker in seen:
            item = ''.join([marker,"1"]) 
        seen[marker] = 1 
        result.append(item) 
    return result


#-------------------------------------------------------------------------------
# Main clipping function
#-------------------------------------------------------------------------------

def mainClipper():
    file = tkFileDialog.askopenfilename()
    ## try:
    ##     file = sys.argv[1]
    ## except (ValueError, IndexError):
    ##     print "No ELAN file is supplied."
    ##     sys.exit()
    annos,path = extractClipTier(file)
    n = 0
    procs = []
    for timep in annos:
        tstart = float(timep[0])/1000. # convert milliseconds to seconds
        tend = float(timep[1])/1000. # convert milliseconds to seconds
        name = timep[2]
        flag = ""
        outName = path.split("/")[-1]
        outName = outName.split(".")[0]
        outfile = quote(''.join(['/'.join(path.split("/")[0:-1]),"/",flag,outName,"-",name,"-clip",str(n),".mp4"]))
        # allow non logging
        logfile = quote(''.join([flag,outName,"-",name,"-clip",str(n),".log"]))
        infile = quote(path)
        print outfile
        ## procs.append(subprocess.Popen("echo $PATH", shell=True))
        procs.append(clipper(infile=infile, outfile=outfile, tstart=tstart, tend=tend, options='', log=logfile, verbose=True))
        n += 1

    print "Waiting for the process to finish."
    procs[0].wait()
    print(procs[0].poll())
    print "Finished!"
    return



def testClipper():
    file = tkFileDialog.askopenfilename()
    tiers = identifyTiers(file)
    annos,path = extractClipTier(file,tiers)
    print(annos)
    return
    
            
#mainClipper()
testClipper()
