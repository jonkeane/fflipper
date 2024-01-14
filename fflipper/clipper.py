import sys, re, os, time, subprocess, errno
from pathlib import Path
from datetime import datetime  # both datetime imports needed?
from datetime import timedelta  # both datetime imports needed?


# from http://stackoverflow.com/questions/273192
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

# So that resources work inside pyinstalled and dev
def fetch_resource(resource_path):
    try:  # running as *.exe; fetch resource from temp directory
        base_path = Path(sys._MEIPASS)
    except AttributeError:  # running as script; return one up
        return resource_path.resolve().parents[0]
    else:  # return temp resource path, two up
        return base_path.joinpath(resource_path.resolve().parents[1])

class clipper:
    """Generates the actually ffmpeg clipping"""

    def __init__(
        self,
        annos,
        outPath,
        inFile,
        audio,
        videoFilters,
        videoCodec,
        videoQuality,
        otherOptions,
    ):
        self.subProc = None
        self.inFile = inFile
        self.audio = audio
        self.videoFilters = videoFilters
        self.videoCodec = videoCodec
        self.videoQuality = videoQuality
        self.otherOptions = otherOptions

        # Extract start and stop from the annotation
        self.tstart = float(annos[0]) / 1000.0  # convert milliseconds to seconds
        self.tend = float(annos[1]) / 1000.0  # convert milliseconds to seconds

        # Ensure outpath exits, safeit.
        make_sure_path_exists(os.path.dirname(outPath))
        self.outFile = outPath + ".mp4"

    def clip(self, verbose = False):
        cmd = self.clipPrep()

        if verbose:
            print(cmd)

        p = subprocess.Popen(
            cmd,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
        )
        return p

    def clipPrep(self):
        """clips video with no options"""
        # deinterlace+crop+scale '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [o2]; [o2] scale=852:480 [out]"'
        # deinterlace+crop '-vf "[in] yadif=1 [o1]; [o1] crop=1464:825:324:251 [out]"'
        # deinterlace '-vf "[in] yadif=1 [out]"'
        dur = self.tend - self.tstart
        
        path_to_ffmpeg = fetch_resource(Path(__file__)) / "bin" / "ffmpeg"
        cmd = [path_to_ffmpeg]

        opts = []

        opts.extend(["-i", self.inFile])

        if self.videoFilters != "":
            opts.extend(["-vf", self.videoFilters])

        opts.extend(
            [
                "-ss",
                str(timedelta(seconds=self.tstart)),
                "-t",
                str(timedelta(seconds=dur)),
            ]
        )

        if self.videoQuality != "":
            opts.extend(["-qscale", self.videoQuality])

        if self.audio == False:
            opts.extend(["-an"])

        if self.videoCodec != "":
            opts.extend(["-vcodec", self.videoCodec])

        if self.otherOptions != [""]:
            opts.extend(self.otherOptions)

        opts.extend(["-y", self.outFile])
        cmd.extend(opts)

        return cmd