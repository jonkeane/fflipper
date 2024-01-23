import sys, re, os, time, subprocess, errno, platform
from pathlib import Path
from datetime import datetime  # both datetime imports needed?
from datetime import timedelta  # both datetime imports needed?
from fflipper.utils import fetch_resource

# from http://stackoverflow.com/questions/273192
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

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

        # if we are running outside of a bundle, we need to add one more layer
        if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
            system = platform.system().lower()
            if (system == "darwin"):
                plat = platform.platform()
                if ("x86" in plat):
                    platform_dir = "macos_x86"
                else:
                    platform_dir = "macos_arm"
            path_to_ffmpeg = Path(str(path_to_ffmpeg).replace("bin", f"bin/{platform_dir}"))

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
