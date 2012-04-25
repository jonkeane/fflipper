import sys, re, os, time, subprocess
from Tkinter import *
## from ttk import *
import tkFileDialog
import tkMessageBox
import clipper
import pyelan.pyelan as pyelan





#-------------------------------------------------------------------------------
# Number Appender
#-------------------------------------------------------------------------------

def numAppend(seq, idfun=None):  
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



class fflipper:
    """The main class that operates the Tk gui."""
    def __init__(self, master):
        self.allTiers = [] # storage for the tiers of an ELAN file
        self.savePath = os.curdir # storage for the save path
        self.checkBoxen = [] # storage for the tier checkboxes
        self.subProcs = [] # for subprocess of clipping

        # Generate the self.master window.
        master.title("fflipper")
        master.config(padx = 10, pady = 10)
        self.elanFind = Frame(master, width=700, height=25)
        self.elanFind.grid(row=0, columnspan=4, sticky=N+S+E+W)
        self.elanFind.grid_propagate(False)


        # generate the header
        self.selElan = Label(self.elanFind, text="Please select an ELAN file to clip. Make sure that the media is associated correctly.")
        self.selElan.grid(row=0, column=0, sticky=W)

        self.elanFile = Button(self.elanFind, text="Open an ELAN file", command=lambda: self.selectTiers(self.tierSelectionTB, self.canvasTier))
        self.elanFile.grid(row=0, column=1, sticky=E)



        # generate the tiers frame
        self.tierSelection = LabelFrame(master, width=300, height=400, text='Tiers')
        self.tierSelection.grid(row=1, column=0, columnspan=2, sticky=W)
        self.tierSelection.grid_propagate(0)

        # autscrollbars for tiers
        vscrollbar = AutoScrollbar(self.tierSelection)
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar = AutoScrollbar(self.tierSelection, orient=HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=E+W)

        # scrolling canvas for tiers
        self.canvasTier = Canvas(self.tierSelection,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set)
        self.canvasTier.grid(row=0, column=0, sticky=N+S+E+W)
    
        vscrollbar.config(command=self.canvasTier.yview)
        hscrollbar.config(command=self.canvasTier.xview)
        
        # make the canvas expandable
        self.tierSelection.grid_rowconfigure(0, weight=1)
        self.tierSelection.grid_columnconfigure(0, weight=1)
    
        # create a frame within the canvas
        self.tierSelectionTB = Frame(self.canvasTier)
        self.tierSelectionTB.rowconfigure(1, weight=1)
        self.tierSelectionTB.columnconfigure(1, weight=1)

        self.canvasTier.bind("<MouseWheel>", lambda event:  self.canvasTier.yview("scroll", event.delta,"units"))
        self.tierSelectionTB.bind("<MouseWheel>", lambda event:  self.canvasTier.yview("scroll", event.delta,"units"))

        
        # ties the frame to the canvas ("the canvas acts like a geometry manager")
        self.canvasTier.create_window(0, 0, anchor=NW, window=self.tierSelectionTB)
        # Can probably be deleted, because they are dealt with in the tiers function
        #self.tierSelectionTB.update_idletasks()
        #self.canvasTier.config(scrollregion=self.canvasTier.bbox("all"))


        separator = Frame(master,width=10)
        separator.grid(row=1,column=2, rowspan=2)

        # generate the progress area.
        progressArea = LabelFrame(master, width=500, height=600, text='Progress')
        progressArea.grid(row=1, column=3, rowspan=2, sticky=W)
        progressArea.grid_propagate(0)


        # generate the options area.
        optionsArea = LabelFrame(master, width=300, height=200, text='Options')
        optionsArea.grid(row=2, column=0, columnspan=2, sticky=W)
        optionsArea.grid_propagate(0)

        self.appendTier = BooleanVar()
        self.appendTier.set(True)
        aTier = Checkbutton(optionsArea, text="append tier name to annotation", variable=self.appendTier, command=self.samplePathUpdate)
        aTier.grid(row = 0, sticky=W)

        # Doesn't work because it doesn't make the directory, need to fix that immediately before clipping, or does ffmpeg have a make dir option?
        self.folderTier = BooleanVar()
        self.folderTier.set(False)
        fTier = Checkbutton(optionsArea, text="each tier in a separate folder", variable=self.folderTier, command=self.samplePathUpdate)
        fTier.grid(row = 1, sticky=W)

        separato = Frame(optionsArea,height=15,width=10)
        separato.grid(row=2)

        self.prependName = StringVar()
        self.prependName.set('')
        pLabel = Label(optionsArea, text="prepend to every clip:")
        pLabel.grid(row=3, sticky=W)
        pName = Entry(optionsArea, textvariable=self.prependName, width=35)
        pName.grid(row = 4, sticky=E)
        pName.bind("<KeyRelease>", lambda event: self.samplePathUpdate())
        

        separat = Frame(optionsArea,height=15,width=10)
        separat.grid(row=5)

        # save to button
        self.saveTo = Button(optionsArea, text="Save to...", command=self.sPath)
        self.saveTo.grid(row=6, column=0, sticky=W )

        # clipping button
        self.clip = Button(master, text="Begin clipping", command=self.clipPrep)
        self.clip.grid(row=3, column=0, sticky=W )

        # locations string. Mostly works, doesn't update on import of clips (feature, not a bug?)
        self.pathSample = StringVar()
        self.pathSamp = Label(master, textvariable=self.pathSample, wraplength=680, fg="dark gray")
        self.pathSamp.grid(row=3, column = 1, columnspan=3, sticky=E)
        

    def samplePathUpdate(self):
        path = self.samplePathGen()
        self.pathSample.set(path)

    def pathGen(self, tier, annoVal):
        filename = self.prependName.get()
        basePath = self.savePath
        if self.folderTier.get():
            if basePath[-1] == os.sep:
                basePath = ''.join([basePath,tier])
            else:
                basePath = os.sep.join([basePath,tier])                
        if self.appendTier.get():
            filename = filename+tier
        filename +=  annoVal

        # do not add extraneous separators. change to os.sep.join()? probably not.
        if basePath[-1] == os.sep:
            path = ''.join([basePath,filename])
        else:
            path = os.sep.join([basePath,filename])
        return path
 
    def samplePathGen(self):
        relTiers = self.relativizeTiers()
        # Check if there are any relative tiers.
        if relTiers.tiers != []:
            path = self.pathGen(tier=relTiers.tiers[0].tierName, annoVal=relTiers.tiers[0].annotations[0].value)
        else:
            path = ''
        return path

    def relativizeTiers(self):
        newTierNames=[]
        for checkBox in self.checkBoxen:
            if checkBox[1].get():
                newTierNames.append(checkBox[0])
        try:
            relTiers = pyelan.tierSet.selectedTiers(self.allTiers,newTierNames)
        except TypeError:
            #error if there are no tiers selected.
            tkMessageBox.showwarning(
                "No tiers detected",
                "There are no tiers to work with. Please select a (new) ELAN file.")       
        return relTiers

    def sPath(self):
        path = tkFileDialog.askdirectory()
        if path: #check that there is a new path.
            self.savePath = path
        self.samplePathUpdate()

    def clipPrep(self):
        relTiers = self.relativizeTiers()
        if relTiers.tiers == []:
            #error if there are no tiers selected.
            tkMessageBox.showwarning(
            "No tiers selected",
            "There are no tiers selected.")
        
        inFile = relTiers.media
        for tr in relTiers.tiers:
            trName = tr.tierName
            numCores = 16
            freeProcs = numCores
            numAnnosLeft = len (tr.annotations)
            print("numannosleft",numAnnosLeft)
            for anno in tr.annotations:
                outFile = self.pathGen( tier=trName, annoVal=anno.value)
                annos = (anno.begin, anno.end)
                self.subProcs.append(clipper.clipper(annos=annos, outPath=outFile, inFile=inFile))
                numAnnosLeft = numAnnosLeft - 1
                print("numannosleft",numAnnosLeft)
                freeProcs = freeProcs-1
                if numAnnosLeft == 0:
                    freeProcs = 0
                    print("Last Process!")              
                while freeProcs == 0:
                    # monitor process
                    print("Starting process monitoring.")
                    nComplete = 0
                    numProcs = len(self.subProcs)
                    while nComplete < numProcs:
                        for singleProc in self.subProcs:
                            if singleProc.subProc.returncode is None:
                                frameReg = re.compile("^frame=\s+(\d+).*")

                                outPut = singleProc.subProc.stdout.readline()
                                frames = frameReg.match(outPut)
                                if frames:
                                    print("frames:",frames.group(1))

                                singleProc.subProc.poll()
                            else:
                                if singleProc.subProc.returncode:
                                    print("Error!")
                                    print(singleProc.subProc.stdout.read())
                                print("done!")
                        nnComp = 0
                        nnRun = 0
                        for singleProc in self.subProcs:
                            if singleProc.subProc.returncode is None:
                                nnRun += 1
                            else:
                                nnComp += 1
                        nComplete = nnComp
                    self.subProcs = [] # for subprocess of clipping
                    print(nComplete,"/",numProcs)
                    print("Reseting to the next batch of processes.")
                    freeProcs = numCores
        return self.subProcs
                
        

    def selectTiers(self,tierSelection, canvasTier):
        file_opt = options =  {}
        options['filetypes'] = [('eaf files', '.eaf'), ('all files', '.*')]
        file = tkFileDialog.askopenfilename(**options)
        try:
            self.allTiers = pyelan.tierSet(file=file)
        except pyelan.noMediaError, e:
            #error if there are no tiers selected.
            tkMessageBox.showwarning(
                "No media found",
                "Could not find the media attached to the ELAN file (path:"+e.filename+"). Please open the ELAN file, find the media, and then save it again.")
        ## top = Toplevel()
        ## top.title("Tier selection")
        ## frame = Frame(top)
        ## frame.pack()
        
        self.msg = Label(tierSelection, text="Which tiers would you like to clip?", wraplength=2000, anchor=W, justify=LEFT)
        self.msg.grid(row=0, sticky=N+W)
        self.msg.bind("<MouseWheel>", lambda event:  self.canvasTier.yview("scroll", event.delta,"units"))
        
        self.checkBoxen = []
        r = 1
        for tier in self.allTiers.tiers:
            name = tier.tierName
            count = len(tier.annotations)
            text = ''.join([name," (",str(count)," annotations)"])
            self.checkBoxen.append([name,BooleanVar()])
            self.checkBoxen[-1][1].set('False')
            self.checkBoxen[-1].append(Checkbutton(tierSelection, text=text, variable=self.checkBoxen[-1][1], command=self.samplePathUpdate))
            self.checkBoxen[-1][-1].grid(row = r, sticky=W)
            self.checkBoxen[-1][-1].bind("<MouseWheel>", lambda event:  self.canvasTier.yview("scroll", event.delta,"units"))
            r += 1
        #Change the save to path to the path of the ELAN file.
        self.savePath = self.allTiers.pathELAN
        
        # to alter the scroll size of the canvas.
        tierSelection.update_idletasks()
        canvasTier.config(scrollregion=canvasTier.bbox(ALL))


            


if __name__ == '__main__':
    root = Tk()
    
    app = fflipper(root)
    
    root.mainloop()

