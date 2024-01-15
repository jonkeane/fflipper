import sys, re, os, time, subprocess, multiprocessing, functools
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
import pyelan.pyelan as pyelan
from fflipper.clipper import clipper
from fflipper.utils import fetch_resource


fp = functools.partial

# -------------------------------------------------------------------------------
# Number Appender
# -------------------------------------------------------------------------------


# this is not used, and does not work.
def numAppend(seq, idfun=None):
    # order preserving
    if idfun is None:

        def idfun(x):
            return x

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen:
            item = "".join([marker, "1"])
        seen[marker] = 1
        result.append(item)
    return result


class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")

    def place(self, **kw):
        raise TclError("cannot use place with this widget")


# This uses Frame as imported from tkinter directly for the same style
# (ttk.Frame has a slightly different look)
class ScrollableLabelFrame(LabelFrame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = LabelFrame(self.canvas, borderwidth=0)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # scroll binding https://gist.github.com/JackTheEngineer/81df334f3dcff09fd19e4169dd560c59
        self.canvas.bind_all("<Enter>", self._bind_to_mousewheel)
        self.canvas.bind_all("<Leave>", self._unbind_from_mousewheel)

    def _on_mousewheel(event, scroll=None):
        os = sys.platform
        if os == "Windows":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif os == "Darwin":
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            self.canvas.yview_scroll(int(scroll), "units")

    def _bind_to_mousewheel(self, event):
        os = sys.platform
        if os == "Windows":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        elif os == "Darwin":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<Button-4>", fp(self._on_mousewheel, scroll=-1))
            self.canvas.bind_all("<Button-5>", fp(self._on_mousewheel, scroll=1))

    def _unbind_from_mousewheel(self, event):
        os = sys.platform
        if os == "Windows":
            self.canvas.unbind_all("<MouseWheel>")
        elif os == "Darwin":
            self.canvas.unbind_all("<MouseWheel>")
        else:
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

class MyDialog(simpledialog.Dialog):
    def __init__(self, parent, title, contents):
        self.contents = contents
        super().__init__(parent, title)

    def body(self, frame):
        error_text = Text(self, height=50, width=100, relief='flat')
        error_text.insert(END, self.contents)
        error_text.config(state=DISABLED) # forbid text edition
        error_text.pack()

        return frame

    def ok_pressed(self):
        self.destroy()

    def buttonbox(self):
        self.ok_button = Button(self, text='close', command=self.ok_pressed)
        self.ok_button.pack(fill = 'x', padx = 50, pady = 20)
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.ok_pressed())

class fflipper:
    """The main class that operates the Tk gui."""

    def __init__(self):
        self.allTiers = []  # storage for the tiers of an ELAN file
        self.savePath = os.curdir  # storage for the save path
        self.checkBoxen = []  # storage for the tier checkboxes
        self.annosToClip = []  # for subprocess of clipping

        # Generate the self.root window.
        self.root = Tk()
        self.root.title("fflipper")
        self.root.config(padx=10, pady=10)
        self.elanFind = Frame(self.root, width=700, height=25)
        self.elanFind.grid(row=0, columnspan=4, sticky=N + S + E + W)
        self.elanFind.grid_propagate(False)

        # generate the header
        self.selElan = Label(
            self.elanFind,
            text="Please select an ELAN file to clip. Make sure that the media is associated correctly.",
        )
        self.selElan.grid(row=0, column=0, sticky=W)

        self.elanFile = Button(
            self.elanFind,
            text="Open an ELAN file",
            command=lambda: self.selectTiers(self.tierSelection),
        )
        self.elanFile.grid(row=0, column=1, sticky=E)

        # generate the tiers frame
        self.tierSelection = ScrollableLabelFrame(
            self.root, width=300, height=200, text="Tiers"
        )
        self.tierSelection.grid(row=1, column=0, columnspan=2, sticky=W)
        self.tierSelection.grid_propagate(0)

        separator = Frame(self.root, width=10)
        separator.grid(row=1, column=2, rowspan=2)

        # generate the progress area.
        self.progressArea = ScrollableLabelFrame(self.root, text="Progress")
        self.progressArea.grid(row=1, column=3, rowspan=2, sticky=N + S + E + W)
        self.progressArea.grid_propagate(0)

        # generate the options area.
        # + 8 pixels for scroll bar
        optionsArea = LabelFrame(self.root, width=308, height=400, text="Options")
        optionsArea.grid(row=2, column=0, columnspan=2, sticky=W)
        optionsArea.grid_propagate(0)

        # append tier name to annotation
        self.appendTier = BooleanVar()
        self.appendTier.set(True)
        aTier = Checkbutton(
            optionsArea,
            text="append tier name to annotation",
            variable=self.appendTier,
            command=self.samplePathUpdate,
        )
        aTier.grid(row=0, sticky=W)

        # Doesn't work because it doesn't make the directory, need to fix that immediately before clipping, or does ffmpeg have a make dir option?
        self.folderTier = BooleanVar()
        self.folderTier.set(False)
        fTier = Checkbutton(
            optionsArea,
            text="each tier in a separate folder",
            variable=self.folderTier,
            command=self.samplePathUpdate,
        )
        fTier.grid(row=1, sticky=W)

        # no audio?
        self.audio = BooleanVar()
        self.audio.set(False)
        udio = Checkbutton(optionsArea, text="audio", variable=self.audio)
        udio.grid(row=2, sticky=W)

        # video codec
        separator.grid(row=3)

        self.videoCodec = StringVar()
        self.videoCodec.set("h264")
        cLabel = Label(optionsArea, text="video codec:")
        cLabel.grid(row=4, sticky=W)
        vCodec = Entry(optionsArea, textvariable=self.videoCodec, width=30)
        vCodec.grid(row=5, sticky=W, padx=10)
        vCodec.bind("<KeyRelease>", lambda event: self.samplePathUpdate())

        # video filters
        separator.grid(row=6)

        self.videoFilters = StringVar()
        self.videoFilters.set("")  # [in] yadif=1 [out] for deinterlacing
        vfLabel = Label(optionsArea, text="video filters:")
        vfLabel.grid(row=7, sticky=W)
        vFilters = Entry(optionsArea, textvariable=self.videoFilters, width=30)
        vFilters.grid(row=8, sticky=W, padx=10)
        vFilters.bind("<KeyRelease>", lambda event: self.samplePathUpdate())

        # video quality options
        separator.grid(row=9)

        self.videoQuality = StringVar()
        self.videoQuality.set("0")
        vfLabel = Label(optionsArea, text="video quality:")
        vfLabel.grid(row=10, sticky=W)
        vQuality = Entry(optionsArea, textvariable=self.videoQuality, width=30)
        vQuality.grid(row=11, sticky=W, padx=10)
        vQuality.bind("<KeyRelease>", lambda event: self.samplePathUpdate())

        # other options
        separator.grid(row=12)

        self.otherOptions = StringVar()
        self.otherOptions.set("")
        vfLabel = Label(optionsArea, text="other options:")
        vfLabel.grid(row=13, sticky=W)
        oOptions = Entry(optionsArea, textvariable=self.otherOptions, width=30)
        oOptions.grid(row=14, sticky=W, padx=10)
        oOptions.bind("<KeyRelease>", lambda event: self.samplePathUpdate())

        # prepend to each file option
        separator.grid(row=15)

        self.prependName = StringVar()
        self.prependName.set("")
        pLabel = Label(optionsArea, text="prepend to every clip:")
        pLabel.grid(row=16, sticky=W)
        pName = Entry(optionsArea, textvariable=self.prependName, width=30)
        pName.grid(row=17, sticky=W, padx=10)
        pName.bind("<KeyRelease>", lambda event: self.samplePathUpdate())

        # save to button
        separator.grid(row=18)

        self.saveTo = Button(optionsArea, text="Save to...", command=self.sPath)
        self.saveTo.grid(row=19, column=0, sticky=W)

        # about/licnese button
        self.saveTo = Button(optionsArea, text="About", command=self.about)
        self.saveTo.grid(row=19, column=0, sticky=E)

        # clipping button
        self.clip = Button(self.root, text="Begin clipping", command=self.prepAndDo)
        self.clip.grid(row=3, column=0, sticky=W)

        # clear button
        self.clip = Button(self.root, text="Clear clips", command=self.clearClips)
        self.clip.grid(row=3, column=3, sticky=E)

        # locations string. Mostly works, doesn't update on import of clips (feature, not a bug?)
        self.pathSample = StringVar()
        self.pathSamp = Label(
            self.root, textvariable=self.pathSample, wraplength=680, fg="dark gray"
        )
        self.pathSamp.grid(row=4, column=1, columnspan=3, sticky=E)

    def samplePathUpdate(self):
        # clear any clips in progress
        self.clearClips()

        path = self.samplePathGen()
        self.pathSample.set(path)

    def pathGen(self, tier, annoVal):
        filename = self.prependName.get()
        basePath = self.savePath
        if self.folderTier.get():
            if basePath[-1] == os.sep:
                basePath = "".join([basePath, tier])
            else:
                basePath = os.sep.join([basePath, tier])
        if self.appendTier.get():
            filename = filename + tier
        filename += annoVal

        # do not add extraneous separators. change to os.sep.join()? probably not.
        if basePath[-1] == os.sep:
            path = "".join([basePath, filename])
        else:
            path = os.sep.join([basePath, filename])
        return path

    def samplePathGen(self):
        relTiers = self.relativizeTiers()
        # Check if there are any relative tiers.
        if relTiers.tiers != []:
            path = self.pathGen(
                tier=relTiers.tiers[0].tierName,
                annoVal=relTiers.tiers[0].annotations[0].value,
            )
        else:
            path = ""
        return path

    def relativizeTiers(self):
        newTierNames = []
        for checkBox in self.checkBoxen:
            if checkBox[1].get():
                newTierNames.append(checkBox[0])
        try:
            relTiers = pyelan.tierSet.selectedTiers(self.allTiers, newTierNames)
        except TypeError:
            # error if there are no tiers selected.
            messagebox.showwarning(
                "No tiers detected",
                "There are no tiers to work with. Please select a (new) ELAN file.",
            )
        return relTiers

    def sPath(self):
        path = filedialog.askdirectory()
        if path:  # check that there is a new path.
            self.savePath = path
        self.samplePathUpdate()

    def prepAndDo(self):
        self.clipPrep()
        self.doClipping()

    def clipPrep(self):
        relTiers = self.relativizeTiers()
        if relTiers.tiers == []:
            # error if there are no tiers selected.
            messagebox.showwarning("No tiers selected", "There are no tiers selected.")

        # grab the first media file only. This might not be the right medial file if there is more than one.
        inFile = relTiers.media[0]
        audio = self.audio.get()
        videoFilters = self.videoFilters.get()
        videoQuality = self.videoQuality.get()
        videoCodec = self.videoCodec.get()
        otherOptions = self.otherOptions.get()

        for tr in relTiers.tiers:
            trName = tr.tierName
            # setup each annotation as a clipping event (along with a progress and annotation value)
            for anno in tr.annotations:
                outFile = self.pathGen(tier=trName, annoVal=anno.value)
                annos = (anno.begin, anno.end)
                self.annosToClip.append(
                    {
                        "clipper": clipper(
                            annos=annos,
                            outPath=outFile,
                            inFile=inFile,
                            audio=audio,
                            videoFilters=videoFilters,
                            videoCodec=videoCodec,
                            videoQuality=videoQuality,
                            otherOptions=otherOptions,
                        ),
                        "annotation": anno,
                        "progress": None,
                        "process": None,
                        "done": False,
                    }
                )

            # setup the progress area
            self.setupProgress(
                self.progressArea, tiername=tr.tierName, annosToClip=self.annosToClip
            )

    def doClipping(self):
        # do the actual clipping
        # establish the number of cores available
        numCores = multiprocessing.cpu_count()
        freeProcs = numCores
        print("Starting process monitoring.")
        nComplete = 0
        nClips = len(self.annosToClip)

        allComplete = False
        while not allComplete:
            for singleAnno in self.annosToClip:
                if singleAnno["process"] is None:
                    if freeProcs > 0:
                        # We have free processors, start starting jobs
                        singleAnno["process"] = singleAnno["clipper"].clip()
                        singleAnno["progress"].children["!progressbar"].config(
                            mode="determinate"
                        )
                        self.root.update()
                        freeProcs -= 1
                    else:
                        # We continue if there are no freeProcs cause there will be no process to poll
                        continue

                # process polling only if there is a process to poll
                singleAnno["process"].poll()
                if singleAnno["process"].returncode is None:
                    frameReg = re.compile("^frame=\s+(\d+).*")

                    outPut = singleAnno["process"].stdout.readline()
                    frames = frameReg.match(outPut)
                    if frames:
                        print("frames:", frames.group(1))
                elif singleAnno["process"].returncode == 0:
                    singleAnno["progress"].children["!progressbar"].stop()
                    singleAnno["progress"].children["!progressbar"]["value"] = 100
                    self.root.update()

                    singleAnno["done"] = True
                    freeProcs += 1
                else:
                    singleAnno["done"] = True
                    freeProcs += 1

                    error_out = singleAnno["process"].stdout.read()
                    error_button = Button(
                        singleAnno["progress"],
                        text='🚨 ERROR',
                        command=lambda: MyDialog(title="🚨 ERROR", contents = error_out, parent=self.root),
                        width=5,
                        height=1,
                        justify=LEFT
                    )
                    error_button.grid(row=0, column=0, sticky=W)
                    singleAnno["progress"].children["!progressbar"].stop()
                    singleAnno["progress"].children["!progressbar"]["value"] = 0



            allComplete = all([singleAnno["done"] for singleAnno in self.annosToClip])
        # TODO: something to mark being all done?
        self.root.update()

        return self.annosToClip

    def setupProgress(self, progress, tiername, annosToClip):
        msg = Label(
            progress.scrollable_frame,
            text="Tier: " + tiername,
            wraplength=2000,
            anchor=W,
            justify=LEFT,
        )
        row_start = len(progress.scrollable_frame.children)
        msg.grid(row=row_start, sticky=N + W)

        row_start += 1
        for annoToClip in annosToClip:
            # Don't add to status if they already have progress:
            if annoToClip["progress"] is not None:
                continue
            annoToClip["progress"] = Frame(progress.scrollable_frame)
            annoToClip["progress"].grid(row=row_start, sticky=W)
            label = Label(
                annoToClip["progress"],
                text=annoToClip["annotation"].value,
                wraplength=2000,
                anchor=W,
                justify=LEFT,
            )
            label.grid(row=0, column=2, sticky=W)
            progress_bar = ttk.Progressbar(annoToClip["progress"], mode="indeterminate")
            progress_bar.grid(row=0, column=1, sticky=W)
            progress_bar.start()
            row_start += 1
        # TODO: need to update scrolling area?

    def selectTiers(self, tierSelection):
        file_opt = options = {}
        options["filetypes"] = [("eaf files", ".eaf"), ("all files", ".*")]
        file = filedialog.askopenfilename(**options)
       
        # clear any clips in progress
        self.clearClips()

        # clear tiers
        if len(tierSelection.scrollable_frame.children) > 0:
            # Delete all frames in the progress window
            [widget.destroy() for widget in tierSelection.scrollable_frame.winfo_children()]
        self.annosToClip = []

        try:
            self.allTiers = pyelan.tierSet(file=file)
        except pyelan.noMediaError as e:
            # error if there are no tiers selected.
            messagebox.showwarning(
                "No media found",
                "Could not find the media attached to the ELAN file (path:"
                + e.filename
                + "). Please open the ELAN file, find the media, and then save it again.",
            )

        self.msg = Label(
            tierSelection.scrollable_frame,
            text="Which tiers would you like to clip?",
            wraplength=2000,
            anchor=W,
            justify=LEFT,
        )
        self.msg.grid(row=0, sticky=N + W)

        self.checkBoxen = []
        r = 1
        for tier in self.allTiers.tiers:
            name = tier.tierName
            count = len(tier.annotations)
            text = "".join([name, " (", str(count), " annotations)"])
            self.checkBoxen.append([name, BooleanVar()])
            self.checkBoxen[-1][1].set("False")
            self.checkBoxen[-1].append(
                Checkbutton(
                    tierSelection.scrollable_frame,
                    text=text,
                    variable=self.checkBoxen[-1][1],
                    command=self.samplePathUpdate,
                )
            )
            self.checkBoxen[-1][-1].grid(row=r, sticky=W)
            r += 1
        # Change the save to path to the path of the ELAN file.
        self.savePath = self.allTiers.pathELAN

        # to alter the scroll size of the canvas.
        self.root.update_idletasks()


    def clearClips(self):
        if len(self.annosToClip) > 0:
            # Delete all frames in the progress window
            [widget.destroy() for widget in self.annosToClip[0]["progress"].master.winfo_children()]
        self.annosToClip = []


    def about(self):
        file = fetch_resource(Path(__file__)) / "about"
        details = open(file).read()
        MyDialog(title="About", contents = details, parent=self.root)


if __name__ == "__main__" :
    app = fflipper()

    app.root.mainloop()