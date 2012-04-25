import sys, re, os, time, subprocess
from pipes import quote
from datetime import datetime #both datetime imports needed?
from datetime import timedelta #both datetime imports needed?



class clipper:
    """Generates the actually ffmpeg clipping"""
    def __init__(self, annos, outPath, inFile):
        tstart = float(annos[0])/1000. # convert milliseconds to seconds
        tend = float(annos[1])/1000. # convert milliseconds to seconds
        outFile = quote(outPath+'.mp4')

        # allow non logging
        #logfile = quote(''.join([flag,outName,"-",name,"-clip",str(n),".log"]))
        #infile = quote(path)

        proc = self.clipFunc(infile=inFile, outfile=outFile, tstart=tstart, tend=tend, log=None, verbose=True)
        self.subProc = proc
    
    def clipFunc(self, infile, outfile, tstart, tend, log=None, verbose=True):
        ''' clipps video with no options '''
        #deinterlace+crop+scale '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [o2]; [o2] scale=852:480 [out]"'
        #deinterlace+crop '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [out]"'
        #deinterlace '-vf "[in] yadif=1 [out]"'
        dur = tend-tstart
        cmd = ["../Resources/ffmpeg"]
        cmd = ["ffmpeg"]
        opts = ["-i", infile, "-ss", str(tstart), "-t", str(dur),"-sameq", "-y", outfile]
        cmd.extend(opts)
        if verbose: print(cmd)
        if log: logFile = open(log, 'w')
        p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout = subprocess.PIPE, bufsize=1, universal_newlines=True)
        return p

