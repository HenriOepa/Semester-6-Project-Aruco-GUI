#I would heartily recommend remaking this whole thing
#Likely a database would be of help too

from tkinter import ttk
import tkinter as tk
from tkinter.messagebox import showinfo
from PIL import Image, ImageTk, ImageOps
from tkinter import filedialog as fd
from tktooltip import ToolTip
import os, sys, asyncio, time, math, threading, csv, cv2, subprocess
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import numpy as np
import cv2.aruco as aruco
import asynctkinter as atk
import multiprocessing as mp
import matplotlib as mpl
import matplotlib.pyplot as plt
import glob as glob


#Launches tkinter, sets the icon, title, window size and where it will be opened on the screen
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.moveWindow()
        self.changeIcon()


    def changeIcon(self):
        try:
            ico = Image.open('misc/index.png')
            photo = ImageTk.PhotoImage(ico)
            self.wm_iconphoto(False, photo)
        except FileNotFoundError:
            return

    def moveWindow(self):
        window_height = 720
        window_width = 1280

        self.resizable(0,0)

        self.title("ArUco GUI")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2.2) - (window_height/2))

        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

    #def test(self):
        #self.forget()
        #secondWindow.tkraise()
        #secondWindow.pack()


#Mainframe for the app, contains 3 separate windows
#Also contains logic for the menu
class MainFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.pack_propagate(False)
        self.config(height=720, width=1280)
        self.pack(fill="both", expand=True)

        self.index = 0

        self.menu()

        self.frameList=[ArucoMain(self),secondWindow(self), thirdWindow(self)]
        self.frameList[1].forget()
        self.frameList[2].forget()

        options = {'padx' : 5, 'pady': 5}
        self.pack(**options)

    def menu(self):
        head_frame = tk.Frame(self, bg='#284578')

        head_frame.pack(side=tk.TOP, fill=tk.X)
        head_frame.pack_propagate(False)
        head_frame.configure(height=50)

        def toggle_menu():

            def changeToMain():
                collapse_menu()
                self.frameList[self.index].forget()
                self.index = 0
                self.frameList[self.index].tkraise()
                self.frameList[self.index].pack()
                ArucoMain.vidPath = secondWindow.videoPath
                ArucoMain.mtxPath = secondWindow.matrixPath

            def changeToSecond():
                collapse_menu()
                self.frameList[self.index].forget()
                self.index = 1
                self.frameList[self.index].tkraise()
                self.frameList[self.index].pack()
                ArucoMain.vidPath = secondWindow.videoPath
                ArucoMain.mtxPath = secondWindow.matrixPath

            def changeToThird():
                collapse_menu()
                self.frameList[self.index].forget()
                self.index = 2
                self.frameList[self.index].tkraise()
                self.frameList[self.index].pack()
                ArucoMain.vidPath = secondWindow.videoPath
                ArucoMain.mtxPath = secondWindow.matrixPath

            def collapse_menu():
                toggle_menu_fm.destroy()
                toggle_btn.config(command=toggle_menu)

            toggle_menu_fm = tk.Frame(self, bg='#284578')
            winHeight = self.winfo_height()
            toggle_menu_fm.place(x=0, y=50, height=winHeight, width=280)

            toggle_btn.config(command=collapse_menu)

            menuOptions = {'bg' : '#284578', 'fg' : 'white', 'font' : ('Bold', 18), 'bd' : 0, 'activebackground': '#284578', 'activeforeground' : 'white'}

            menu_btn = tk.Button(toggle_menu_fm, text='ArUco', **menuOptions, command = changeToMain).place(x=10, y=20)
            settings_btn = tk.Button(toggle_menu_fm, text='ArUco Settings', **menuOptions, command = changeToSecond).place(x=10, y=70)
            param_btn = tk.Button(toggle_menu_fm, text='Parameters Settings', **menuOptions, command = changeToThird).place(x=10, y=120)
        
        toggle_btn = tk.Button(head_frame, text='☰', bg='#284578', fg='white', font=('Bold', 20),
                                bd=0, activebackground='#284578', activeforeground='white', command=toggle_menu)
        
        toggle_btn.pack(side=tk.TOP, anchor=tk.W)


#The main window where videos and graphs are analyzed
class ArucoMain(tk.Frame):
    #Parameters for communication between classes
    vidPath = ""
    mtxPath = ""
    formerVidPath = ""
    formerMtxPath = ""
    prevData = []
    paramChanged = False
    currentDictionary = ""

    def __init__(self, master):
        super().__init__(master)

        #Most parameters and flags are here
        self.timeOfUse = None
        self.pauseVal = False
        self.frameChange = False
        self.showRejected = False
        self.playIsActive = False
        self.stopThread = False
        self.saveFrameVal = False
        self.isPortrait = False
        self.rotateVideo = False
        self.dataFiles = []
        self.numOfFiles = 0
        self.currentFile = 0
        self.frameCount = 0
        self.canvas = None
        self.toolbar = None
        self.graphType = "acceleration"
        
        self.pack_propagate(False)
        self.config(height=720, width=1280)
        self.pack(fill="both", expand=True)

        #Options for buttons and where they're placed
        options = {'height' : 1, 'width' : 3, 'font' : ('bold', 10), 'bd' : 0, 'highlightthickness' : 1}

        scroll_height = 490
        start_wid = 875

        #Update information on the main page when the window is viewed
        def updateStuff(e):
            if len(secondWindow.videoPath) < 1:
                self.x.set("Currently selected file: NONE")
            else:
                self.x.set("Currently selected file: " + secondWindow.videoPath)

            if len(secondWindow.videoPath) > 0 and len(secondWindow.matrixPath) > 0:
                self.startButton["state"] = "normal"
            else:
                self.startButton["state"] = "disable"

            self.dic.set("Currently used dictionary: " + secondWindow.usedDict)


        #Buttons and labels on the main page
        self.startButton = tk.Button(self, text = 'Start video', command = self.temp)
        self.startButton.place(x=start_wid-220, y=scroll_height)

        self.button = tk.Button(self, text = ' ⏭ ', **options, command=self.moveToEnd).place(x=start_wid+120, y=scroll_height)
        self.button1 = tk.Button(self, text = '⏵', **options, command=self.moveForwardOne).place(x=start_wid+90, y=scroll_height)
        self.button2 = tk.Button(self, text = '⏹', **options, command=self.pause)
        self.button2.place(x=start_wid+60, y=scroll_height)
        self.button3 = tk.Button(self, text = '⏴', **options, command=self.moveBackOne).place(x=start_wid+30, y=scroll_height)
        self.button4 = tk.Button(self, text = ' ⏮ ', **options, command=self.moveToStart).place(x=start_wid, y=scroll_height)

        self.forwardGraph = tk.Button(self, text = 'Next Graph', padx=3, command= self.nextGraph).place(x = 335, y = scroll_height + 50)
        self.backGraph = tk.Button(self, text = 'Previous Graph', padx=3, command= self.previousGraph).place(x = 235, y = scroll_height + 50)
        self.takeToFolder = tk.Button(self, text = "Open data folder...", command = self.openDataFolder).place(x = 50, y = scroll_height)
        coordGraph = tk.Button(self, text = 'Coordinates Graph', padx=3, command=self.coordinatesGraph).place(x = 385, y = 50)
        veloGraph = tk.Button(self, text = 'Velocity Graph', padx=3, command=self.velocityGraph).place(x = 292, y = 50)
        accGraph = tk.Button(self, text = 'Acceleration Graph', padx=3, command= self.accelerationGraph).place(x = 175, y = 50)

        self.saveButton = tk.Button(self, text = 'Save frame', command= self.saveFrame).place(x=start_wid-90, y=scroll_height+30)
        self.rejectedButton = tk.Button(self, text = 'Enable/Disable Rejections', command=self.showRejectedAreas).place(x=start_wid-14, y=scroll_height+30)
        self.rotateVidBtn = tk.Button(self, text="Video rotation: off", command=self.setToRotate)
        self.rotateVidBtn.place(x=start_wid+140, y=scroll_height+30)

        self.x = tk.StringVar()
        self.x.set(secondWindow.videoPath)

        self.dic = tk.StringVar()
        self.dic.set(secondWindow.usedDict)

        self.labl = tk.Label(self, textvariable=self.x).place(x=700, y=50)
        self.loading = tk.Label(self, text = "")
        self.loading.place(x=700, y=25)
        self.currentDictLbl = tk.Label(self, textvariable=self.dic).place(x=990, y= scroll_height + 82)

        self.imgSaved = tk.Label(self, text = "")
        self.imgSaved.place(x=920, y=550)
        self.currentTime = tk.Label(self, text = "Current time: ")
        self.currentTime.place(x=1100, y=490)

        #updateStuff is called when visibility of the frame changes
        self.bind('<Visibility>', updateStuff)

        #Creates the canvases
        self.windowTry()



    #Opens folder in a few window when button is pressed
    def openDataFolder(self):

        if self.timeOfUse is not None:

            #txt files used for displaying graphs and csv files
            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderPath = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))

            if not os.path.exists(folderPath):
                os.makedirs(folderPath)

            subprocess.Popen(['explorer', folderPath])

    #Due to some quirks, portrait videos can be occasionally flipped
    #This sets the flag to rotate the video on demand
    def setToRotate(self):
        if self.rotateVideo:
            self.rotateVideo = False
            self.rotateVidBtn.config(text="Video rotation: off")
        else:
            self.rotateVideo = True
            self.rotateVidBtn.config(text="Video rotation: on")

    #Sets the flag to show rejected areas on the frame
    def showRejectedAreas(self):
        if self.showRejected == False:
            self.showRejected = True
        else:
            self.showRejected = False

    #Sets the flag to pause the video, changes pause button color
    def pause(self):
        if self.pauseVal == False:
            self.pauseVal = True
            self.button2.config(fg="red")
        else:
            self.pauseVal = False
            self.button2.config(fg="black")

    #Moves back one frame by reducing the frame count that's being kept track of
    def moveBackOne(self):
        self.frameCount = self.frameCount - 1

        if self.frameCount < 0:
            self.frameCount = 0
        
        self.pauseVal = True
        self.frameChange = True
        self.button2.config(fg="red")

    #Moves forward one frame by increasing the frame count that's being kept track of
    def moveForwardOne(self):

        video = ArucoMain.vidPath
        if len(video) < 1:
            return
        
        #Try if video can be opened or not
        try:
            temp = cv2.VideoCapture(video)

            if not temp.isOpened():
                temp.release()
                return

            #Gets max number of frames in video
            maxFrames = temp.get(cv2.CAP_PROP_FRAME_COUNT) - 1
            temp.release()
        except cv2.error as e:
            return e
        
        self.frameCount = self.frameCount + 1

        if self.frameCount > maxFrames:
            self.frameCount = maxFrames
        
        self.pauseVal = True
        self.frameChange = True
        self.button2.config(fg="red")

    #Sets the frame track variable to 0, which is the beginning of the video
    def moveToStart(self):
        self.frameCount = 0

        self.pauseVal = True
        self.frameChange = True
        self.button2.config(fg="red")

    #Gets the maximum amount of frames, but sets it to just below maximum
    #due to the video being taken at max frame would result in the ret break happening
    def moveToEnd(self):
        video = ArucoMain.vidPath
        if len(video) < 1:
            return
        
        #Checks if video can be opened
        try:
            temp = cv2.VideoCapture(video)

            if not temp.isOpened():
                temp.release()
                return

            #Gets max number of frames in video
            self.frameCount = temp.get(cv2.CAP_PROP_FRAME_COUNT) - 1
            temp.release()
        except cv2.error as e:
            return e
        
        self.pauseVal = True
        self.frameChange = True
        self.button2.config(fg="red")

    #Logic for the play button, checks if video can be opened, sets the time of use
    #Sets time label and pause buttons back to default, sets the text in play button
    def temp(self):
    
        if len(ArucoMain.vidPath) > 0:

            try:
                temp = cv2.VideoCapture(ArucoMain.vidPath)
                if not temp.isOpened():
                    temp.release()
                    return
                temp.release()
            except cv2.error as e:
                return e
            

            self.timeOfUse = time.asctime().replace(" ", "").replace(":","")

            self.button2.config(fg="black")
            self.currentTime.config(text="Current time: ")

            if self.playIsActive:
                self.stopThread = True
                self.startButton.config(text="Start video")
            else:
                self.stopThread = False
                self.startButton.config(text="Stop video")


            #Starts a threaded method, daemon is set so when the app is closed, the process won't
            #still be running in the background
            threading.Thread(target=self.play, daemon=True).start()

    #Goes to the next graph
    def nextGraph(self):
        #If there's more than 1 file, the files are cycled through and graph is opened
        if self.numOfFiles != 0:
            self.currentFile = self.currentFile + 1
            self.currentFile = self.currentFile % self.numOfFiles

            if self.graphType == "coordinates":
                self.coordinatesGraph()
            elif self.graphType == "velocity":
                self.velocityGraph()
            elif self.graphType == "acceleration":
                self.accelerationGraph()

    #Goes to theprevious graph
    def previousGraph(self):
        #If there's more than 1 file, the files are cycled through and graph is opened
        if self.numOfFiles != 0:
            self.currentFile = self.currentFile - 1
            self.currentFile = self.currentFile % self.numOfFiles

            if self.graphType == "coordinates":
                self.coordinatesGraph()
            elif self.graphType == "velocity":
                self.velocityGraph()
            elif self.graphType == "acceleration":
                self.accelerationGraph()


    def coordinatesGraph(self):
        self.graphType = "coordinates"

        if self.numOfFiles != 0:

            plotTime = []
            plotX = []
            plotY = []
            plotZ = []
            values = []
            maxY = 0
            minY = 9.814

            #Checks if there's already a graph in the canvas
            if self.canvas is not None and self.toolbar is not None:
            # If they do, remove them from the grid
                self.canvas.get_tk_widget().pack_forget()
                self.toolbar.pack_forget()

            #Read a line from file, get the data and store it. Find maximum y value
            with open(self.dataFiles[self.currentFile]) as f:

                while (line := f.readline().rstrip()):
                    #Clears old entries
                    values.clear()
                    #Values are gotten from the file, split from comma
                    values.extend(line.split(","))

                    plotTime.append(float(values[0]))
                    plotX.append(float(values[1]))
                    plotY.append(float(values[2]))
                    plotZ.append(float(values[3]))

                    if float(values[1]) > maxY:
                        maxY = float(values[1])

                    if float(values[2]) > maxY:
                        maxY = float(values[2])

                    if float(values[3]) > maxY:
                        maxY = float(values[3])

                    if float(values[1]) < minY:
                        minY = float(values[1])

                    if float(values[2]) < minY:
                        minY = float(values[2])

                    if float(values[3]) < minY:
                        minY = float(values[3])


            f.close()

            #To stop weird graphs from showing
            if maxY == 0:
                maxY = 1
            if minY == 0:
                minY = -1

            #Gets the tag id from file name
            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))

            index = self.dataFiles[self.currentFile][len(folderName) + 1: len(self.dataFiles[self.currentFile]) - len("_measurement.txt")]
            titleName = str(index) + ' tag measurement'
            

            # Create figure and axis objects, plot the graphs
            fig = plt.Figure(figsize=(self.graph_canvas.winfo_width() / 100, self.graph_canvas.winfo_height() / 100))
            ax = fig.add_subplot(111)
            ax.set_title(titleName)

            ax.plot(plotTime, plotX, scaley=True, label='X coordinate')
            ax.plot(plotTime, plotY, scaley=True, label='Y coordinate')
            ax.plot(plotTime, plotZ, scaley=True, label='Z coordinate')

            ax.set_xticks(np.arange(0, float(values[0]), step=(float(values[0]) / 10)))
            ax.set_yticks(np.arange(minY, maxY, step=((maxY - minY + 0.001) / 10)))

            ax.legend()

            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Unit (mm)")
            ax.grid()

            #Create canvas and add it to the tkinter canvas
            self.canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Create toolbar and add it to the canvas
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_canvas)
            self.toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Put the graph into the canvas
            self.canvas.draw()

            self.canvas.get_tk_widget().configure(width=self.graph_canvas.winfo_width(), height=self.graph_canvas.winfo_height() - 42)


    def velocityGraph(self):
        self.graphType = "velocity"

        if self.numOfFiles != 0:
            #Holds previous time
            previousTime = 0

            plotTime = []
            plotVelocity = []
            values = []
            maxY = 0
            minY = 9.814

            #Checks if there's already a graph in the canvas
            if self.canvas is not None and self.toolbar is not None:
            # If they do, remove them from the grid
                self.canvas.get_tk_widget().pack_forget()
                self.toolbar.pack_forget()

            #Read a line from file, get the data and store it. Find maximum y value
            with open(self.dataFiles[self.currentFile]) as f:

                while (line := f.readline().rstrip()):
                    #Clears old entries
                    values.clear()
                    #Values are gotten from the file, split from comma
                    values.extend(line.split(","))
                    plotTime.append(float(values[0]))

                    try:
                        #Because length is in mm, have to divide by 1000 to get value in meters
                        #Time is already represented in seconds
                        #Formula for velocity is (current distance - previous distance) / time - previous time
                        #values[4] is vector length, taken from file

                        velocity = ((float(values[4]) / 1000) / (float(values[0]) - previousTime))

                    except ZeroDivisionError:
                        velocity = 0

                    plotVelocity.append(velocity)
                    previousTime = float(values[0])

                    if velocity > maxY:
                        maxY = velocity

                    if velocity < minY:
                        minY = velocity


            f.close()

            #To stop weird graphs from showing
            if maxY == 0:
                maxY = 1
            if minY == 0:
                minY = -1

            #Gets the tag number from the file name
            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))

            index = self.dataFiles[self.currentFile][len(folderName) + 1: len(self.dataFiles[self.currentFile]) - len("_measurement.txt")]
            titleName = str(index) + ' tag measurement'
            

            # Create figure and axis objects
            fig = plt.Figure(figsize=(self.graph_canvas.winfo_width() / 100, self.graph_canvas.winfo_height() / 100))
            ax = fig.add_subplot(111)
            ax.set_title(titleName)
            ax.plot(plotTime, plotVelocity, scaley=True)
            ax.set_xticks(np.arange(0, float(values[0]), step=(float(values[0]) / 10)))
            ax.set_yticks(np.arange(minY, maxY, step=((maxY - minY + 0.001) / 10)))
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Velocity (m/s)")
            ax.grid()

            #Create canvas and add it to the tkinter canvas
            self.canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Create toolbar and add it to the canvas
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_canvas)
            self.toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Put the graph into the canvas
            self.canvas.draw()

            self.canvas.get_tk_widget().configure(width=self.graph_canvas.winfo_width(), height=self.graph_canvas.winfo_height() - 42)


    def accelerationGraph(self):
        self.graphType = "acceleration"
        self.previousVelo = 0

        if self.numOfFiles != 0:
            #Holds previous time
            previousTime = 0

            plotTime = []
            plotVector = []
            values = []
            maxY = 0
            minY = 9.814

            #Checks if there's already a graph in the canvas
            if self.canvas is not None and self.toolbar is not None:
            # If they do, remove them from the grid
                self.canvas.get_tk_widget().pack_forget()
                self.toolbar.pack_forget()


            #Read a line from file, get the data and store it. Find maximum y value
            with open(self.dataFiles[self.currentFile]) as f:

                while (line := f.readline().rstrip()):
                    #Clears old entries
                    values.clear()
                    #Values are gotten from the file, split from comma
                    values.extend(line.split(","))
                    plotTime.append(float(values[0]))

                    try:
                        #Because length is in mm, have to divide by 1000 to get value in meters
                        #Time is already represented in seconds
                        #Formula for acceleration is (current distance - previous distance) / time * time
                        #values[4] is vector length, taken from file
                        timePassed = (float(values[0]) - previousTime)

                        velocity = ((float(values[4]) / 1000) / timePassed)
                        acceleration = (velocity - self.previousVelo) / timePassed

                        self.previousVelo = velocity

                    except ZeroDivisionError:
                        acceleration = 0
                        self.previousVelo = 0

                    plotVector.append(acceleration)
                    previousTime = float(values[0])

                    if acceleration > maxY:
                        maxY = acceleration

                    if acceleration < minY:
                        minY = acceleration


            f.close()

            #To stop weird graphs from showing
            if maxY == 0:
                maxY = 1
            if minY == 0:
                minY = -1

            #Gets the tag id from file name
            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))

            index = self.dataFiles[self.currentFile][len(folderName) + 1: len(self.dataFiles[self.currentFile]) - len("_measurement.txt")]
            titleName = str(index) + ' tag measurement'
            

            # Create figure and axis objects
            fig = plt.Figure(figsize=(self.graph_canvas.winfo_width() / 100, self.graph_canvas.winfo_height() / 100))
            ax = fig.add_subplot(111)
            ax.set_title(titleName)
            ax.plot(plotTime, plotVector, scaley=True)
            ax.set_xticks(np.arange(0, float(values[0]), step=(float(values[0]) / 10)))
            ax.set_yticks(np.arange(minY, maxY, step=((maxY - minY + 0.001) / 10)))
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Acceleration (m/s^2)")
            ax.grid()

            #Create canvas and add it to the tkinter canvas
            self.canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Create toolbar and add it to the canvas
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_canvas)
            self.toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            #Put the graph to the canvas
            self.canvas.draw()
            
            self.canvas.get_tk_widget().configure(width=self.graph_canvas.winfo_width(), height=400 - 37)

    #Sets the value to true so the image can be saved
    #Hides the text after 5 seconds
    def saveFrame(self):
        def changeText():
            self.imgSaved.config(text="")

        self.saveFrameVal = True
        if self.playIsActive:
            self.imgSaved.config(text="Image saved!")
            self.after(5000, changeText)
        else:
            self.imgSaved.config(text="No video found!")
            self.after(5000, changeText)


    #The main video processing and presentation method
    def play(self):

        dataFiles = []
        numOfFiles = 0
        currentFile = 0

        self.playIsActive = True
        self.saveFrameVal = False
        self.prevTime = 0
        oldFrame = None

        video = ArucoMain.vidPath
        matrix = ArucoMain.mtxPath

        #Preprocesses the file so the graph can be shown during the video

        def writeToFile(id, data, fps, curTime):
            
            #txt files used for displaying graphs and csv files
            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))
            filePath = str(folderName) + '/' + str(id) + '_measurement.txt'
            CSVfilePath = str(folderName) + '/' + str(id) + '_measurement.csv'

            if not os.path.exists(folderName):
                os.makedirs(folderName)

            #Checks if file already exists, if not, creates it 
            if not os.path.exists(filePath):
                f = open(filePath, 'w')
                f.close()

            #Create new csv file
            if not os.path.exists(CSVfilePath):
                csvHeader = ['time', 'x-coordinate', 'y-coordinate', 'z-coordinate', 'distance(vector length)']

                with open(CSVfilePath, 'w', newline="") as csvfile:

                    write = csv.writer(csvfile)

                    write.writerow(csvHeader)
                

            #Write data to file
            #Format will be aaa,bbb,ccc,ddd etc
            dataToWrite = ','.join(data)
            f = open(filePath, 'a')
            #\n in the end so the data would not be written in a single row
            f.write(dataToWrite + '\n')
            f.close()

            #csv file writing

            with open(CSVfilePath, 'a', newline="") as csvfile:
                    
                write = csv.writer(csvfile)

                write.writerow(data)


            self.prevTime = curTime


        def checkData(dataWrite, coordX, coordY, dist, fps, frameTime):
            checkData = ("{:.2f}".format(coordX),"{:.2f}".format(coordY), "{:.2f}".format(dist))

            currentData = "".join(checkData)

            #Last time I had an issue where the same data was being written twice
            #This solved the issue
            if currentData != ArucoMain.prevData:

                writeToFile(self.ids[self.index1], dataWrite, fps, frameTime)

            ArucoMain.prevData = "".join(checkData)

        def preprocessing(cap, matrix, parameters, markerSize, aruco_dict):
            #Write the data from markers inot a file
            ArucoMain.prevData = ""

            
            #cap = cv2.VideoCapture(video)
            fps = cap.get(cv2.CAP_PROP_FPS)
            #prev_time = 0
            prevCoords = []
            startCoords = []
            indexes = []
            timePassed = 0
            frameNum = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            num = 0
            
            if fps == 0:
                fps = 30

            timeBetween = 1 / fps

            #Try if matrix file is valid. If not, exit   
            try:
                with open(matrix, 'rb') as f:
                    camera_matrix = np.load(f)
                    camera_distortion = np.load(f)
            except FileNotFoundError:
                return


                #Run the video through beforehand so that the data could be used for generating a graph
            while True:

                if self.stopThread:
                    self.playIsActive = False
                    return
                
                
                ret, frame = cap.read()

                num = num + 1

                if not ret:
                    self.loading.config(text = "All frames have been processed")
                    break
                

                string = "Processed " + str(num) + " frames out of " + str(int(frameNum))

                self.loading.config(text = string)

                timePassed += 1 / fps

                #Create a mask of the frame captured
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                #Detect markers on the frame, get corners, ids and rejected areas
                corners, self.ids, rejected_img_points = aruco.detectMarkers(gray, aruco_dict, camera_matrix, camera_distortion, parameters=parameters)

                if corners:
                    aruco.drawDetectedMarkers(frame, corners)

                    eparams = aruco.EstimateParameters_create()

                    #Estimate marker pose, get translation and rotation vectors
                    rvecs, tvecs, obj = aruco.estimatePoseSingleMarkers(corners, markerSize, camera_matrix, camera_distortion, estimateParameters=eparams)

                    marker_num = range(0, self.ids.size)

                    for markerIds, markerCorn, self.index1 in zip(self.ids, corners, marker_num):

                        rvec = rvecs[self.index1][0]
                        tvec = tvecs[self.index1][0]

                        #If list is empty, set values
                        try:
                            _ = prevCoords[self.index1][0]
                        except:
                            prevCoords.insert(self.index1, [self.ids[self.index1], tvec[0], tvec[1], tvecs[self.index1][0][2]])

                        #Set starting coordinates, check how much marker has moved from a position
                        #Not really useful
                        try:
                            _ = startCoords[self.index1][0]
                        except:
                            startCoords.insert(self.index1, [markerIds[0], tvec[0], tvec[1], tvecs[self.index1][0][2]])

                        #Get indexes that have been detected
                        #Needs some extra work
                        try:
                            _ = indexes[self.index1]
                        except:
                            indexes.insert(0,self.ids[self.index1])

                        #Find correct id from list
                        #Prevents the occasional data being wrongly placed
                        for count in range(0, len(prevCoords)):
                            
                            if prevCoords[count][0] == markerIds[0]:
                                idNum = count
                                break

                            count += 1

                        #If id has not appreared previously, add to list
                        if self.ids[self.index1] not in indexes:
                            indexes.append(self.ids[self.index1])

                        #Calculate vector length based on the coordinates
                        moveVector = math.sqrt(math.pow(tvec[0] - prevCoords[idNum][1], 2) + math.pow(tvec[1] - prevCoords[idNum][2], 2) +
                        math.pow(tvecs[self.index1][0][2] - prevCoords[idNum][3], 2))

                        #Format of the data to be written to the file
                        data2Write = ("{:.5f}".format(timePassed), "{:.4f}".format(tvec[0]),
                        "{:.4f}".format(tvec[1]), "{:.4f}".format(tvecs[self.index1][0][2]), "{:.8f}".format(moveVector))

                        #Write measurement data into a file
                        checkData(data2Write, tvec[0], tvec[1], tvecs[self.index1][0][2], fps, timePassed)

                        #Save the coordinates so the vector could be calculated
                        prevCoords.pop(idNum)
                        prevCoords.insert(idNum, [markerIds[0], tvec[0], tvec[1], tvecs[self.index1][0][2]])

        
        #Gets the number of data files generated by preprocessing
        def graphData():
            self.numOfFiles = 0
            self.currentFile = 0

            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'Measurements\Measurement_' + str(self.timeOfUse))

            self.dataFiles = glob.glob(str(folderName) + '/*.txt')


            for file in self.dataFiles:

                self.numOfFiles = self.numOfFiles + 1


        #Saves the current frame to the specified folder
        def saveFrameToFolder(frame):
            num = 1

            file_path = os.path.dirname(os.path.realpath(sys.argv[0]))
            folderName = os.path.join(file_path, 'misc/Images/')

            if not os.path.exists(folderName):
                os.makedirs(folderName)

            #Get the files 
            temp = []
            temp = glob.glob(folderName + '*.png')

            #Gets a non-existing image name for the saved image
            imgPath = str(folderName) + 'image_' + str(num) + '_' + str(self.timeOfUse) + '.png'

            for img in temp:
                imgPath = str(folderName) + 'image_' + str(num) + '_' + str(self.timeOfUse) + '.png'

                if os.path.isfile(imgPath):
                    num += 1
                    pass
                else:
                    break
            
            #In-case the frame's colors are wrong
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            #Writes the image to the folder
            cv2.imwrite(imgPath, frame)

            self.saveFrameVal = False



        ######################################################
        #               Actual video stuff here              #
        ######################################################

        #Check if video is actually selected
        if len(video) < 1:
            return
        
        #Try if video can be opened, else return error
        try:
            temp = cv2.VideoCapture(video)
            if not temp.isOpened():
                temp.release()
                return
            temp.release()
        except cv2.error as e:
            return e
            
        #Try if matrix file is valid. If not, exit   
        try:
            with open(matrix, 'rb') as f:
                camera_matrix = np.load(f)
                camera_distortion = np.load(f)
        except:
            return

        #Get values from the paramters and aruco settings files
        paramValues = []
        currentValues = []
        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        paramLoc = folderLoc + "/paramValues.txt"

        paramFile = open(paramLoc, "r")
        paramLine = paramFile.readline().rstrip()
        paramValues.extend(paramLine.split(";"))
        paramFile.close()

        location = folderLoc + "/arucoValues.txt"

        arucoFile = open(location, "r")
        line = arucoFile.readline().rstrip()
        currentValues.extend(line.split(";"))
        arucoFile.close()

        #Check if there's correct amount of parameters
        if len(paramValues) > 24 or len(paramValues) < 24:
            self.loading.config(text = "ERROR: Incorrect amount of parameters. Restore default values")
            return
        
        counter = 0
        paraDefaults = ["1", "30", "5", "0.1", "0.03", "4", "0.35", "0.6", "1", "10", "23",
                         "3", "4.0", "0.05", "0.13", "1", "5.0", "0.1", "0.05", "3", "0.05", "7", "0", "0"]

        #Checks if values are correct, if they aren't, default values will be used in their place
        for val in paramValues:
            if counter == 0 or counter == 1 or counter == 2 or counter == 5 or counter == 8 or counter == 9 or counter == 10 or counter == 11 or counter == 15 or counter == 19 or counter == 21 or counter == 22 or counter == 23:
                try:
                    temp = int(val)
                except ValueError:
                    paramValues[counter] = paraDefaults[counter]
            else:
                try:
                    temp = float(val)
                except ValueError:
                    paramValues[counter] = paraDefaults[counter]

            counter = counter + 1

        #Get selected dictionary value and set the used library as such
        dictVal = int(currentValues[0])

        if dictVal == 0:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
        elif dictVal == 1:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)
        elif dictVal == 2:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_250)
        elif dictVal == 3:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_1000)
        elif dictVal == 4:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_50)
        elif dictVal == 5:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_100)
        elif dictVal == 6:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_250)
        elif dictVal == 7:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_1000)
        elif dictVal == 8:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_50)
        elif dictVal == 9:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_100)
        elif dictVal == 10:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        elif dictVal == 11:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_1000)
        elif dictVal == 12:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_7X7_50)
        elif dictVal == 13:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_7X7_100)
        elif dictVal == 14:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_7X7_250)
        elif dictVal == 15:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_7X7_1000)
        elif dictVal == 16:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL)
        
        #Get marker size in mm
        markerSize = float(currentValues[1])

        #Detector parameters to improve tag detection, gotten from the previous settings files
        parameters = aruco.DetectorParameters_create()
        parameters.cornerRefinementMethod = int(paramValues[0])
        parameters.cornerRefinementMaxIterations = int(paramValues[1])
        parameters.cornerRefinementWinSize = int(paramValues[2])
        parameters.cornerRefinementMinAccuracy = float(paramValues[3])
        parameters.polygonalApproxAccuracyRate = float(paramValues[4])
        parameters.perspectiveRemovePixelPerCell = int(paramValues[5])
        parameters.maxErroneousBitsInBorderRate = float(paramValues[6])
        parameters.errorCorrectionRate = float(paramValues[7])
        parameters.markerBorderBits = int(paramValues[8])
        parameters.adaptiveThreshWinSizeStep = int(paramValues[9])
        parameters.adaptiveThreshWinSizeMax = int(paramValues[10])
        parameters.adaptiveThreshWinSizeMin = int(paramValues[11])
        parameters.maxMarkerPerimeterRate = float(paramValues[12])
        parameters.minMarkerPerimeterRate = float(paramValues[13])
        parameters.perspectiveRemoveIgnoredMarginPerCell = float(paramValues[14])
        parameters.minSideLengthCanonicalImg = int(paramValues[15])
        parameters.minOtsuStdDev = float(paramValues[16])
        parameters.minMarkerLengthRatioOriginalImg = float(paramValues[17])
        parameters.minMarkerDistanceRate = float(paramValues[18])
        parameters.minDistanceToBorder = int(paramValues[19])
        parameters.minCornerDistanceRate = float(paramValues[20])
        parameters.adaptiveThreshConstant = int(paramValues[21])
        parameters.detectInvertedMarker = bool(int(paramValues[22]))
        parameters.useAruco3Detection = bool(int(paramValues[23]))

        #If current video path and parameters are the same, skip processing the video again
        if self.formerVidPath != video or ArucoMain.paramChanged:

            if self.stopThread:
                self.playIsActive = False
                return
            
            #Checks if there's already a graph in the canvas
            if self.canvas is not None and self.toolbar is not None:
            # If they do, remove them from the grid
                self.canvas.get_tk_widget().pack_forget()
                self.toolbar.pack_forget()

            ArucoMain.paramChanged = False

            #Sets the start video button to disabled so preprocessing can't be interrupted
            self.startButton["state"] = "disable"

            cap = cv2.VideoCapture(video)

            preprocessing(cap, matrix, parameters, markerSize, aruco_dict)

            cap.release()

            graphData()

            if self.numOfFiles != 0:

                self.accelerationGraph()

            #Reenabled start video button
            self.startButton["state"] = "normal"

        #Sets the former video path to current video so when start video is pressed again
        #it is checked along with paramsChanged
        self.formerVidPath = video
        
        #Global variables to display the video in canvas - avoids data cleanup that is performed by python
        global aImg1, frame

        video = ArucoMain.vidPath
        self.frameCount = 0
        self.frameChange = False
        self.pauseVal = False

        
        cap = cv2.VideoCapture(video)
        fps = cap.get(cv2.CAP_PROP_FPS)

        #If fps is 0, set it to 30
        if fps == 0:
            fps = 30

        #Get the needed dimensions to show the frames in canvas
        can_wid, can_hei = 600, 400
        vid_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        prev_time = 0


        if vid_width > vid_height:
            self.isPortrait = False
            ratio = can_wid / vid_width
            new_wid = int(vid_width * ratio)
            new_hei = int(vid_height * ratio)
            start_x = int(((can_wid - new_wid) / 2) + 2)
            start_y = int(((can_hei - new_hei) / 2) + 2)

            if new_hei > can_hei:
                other_ratio = can_hei / new_hei
                new_wid = int(vid_width * other_ratio)
                new_hei = int(vid_height * other_ratio)
                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

        elif vid_height >= vid_width:
            self.isPortrait = True
            ratio = can_hei / vid_height
            new_wid = int(vid_width * ratio)
            new_hei = int(vid_height * ratio)
            start_x = int(((can_wid - new_wid) / 2) + 2)
            start_y = int(((can_hei - new_hei) / 2) + 2)

            if new_wid > can_wid:
                other_ratio = can_wid / new_wid
                new_wid = int(vid_width * other_ratio)
                new_hei = int(vid_height * other_ratio)
                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

        #Show video in canvas
        while True:
            
            #If flag is set, will try to end the thread
            if self.stopThread:
                self.playIsActive = False
                return
            
            current_Time = time.time()
            
            #Video is shown at its actual speed
            if((current_Time - prev_time) >= (1 / fps)):
                
                #If frame count is smaller than max, increase frame count
                if self.frameCount < cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1:
                    self.frameCount = self.frameCount + 1

                #Read the video file
                ret, frame = cap.read()

                #If no frame was got, clear the canvas and set the time label
                if not ret:
                    self.window_canvas.delete("all")
                    self.currentTime.config(text="Current time: ")
                    break

                #Update current time label
                self.currentTime.config(text="Current time: {:.4f}sec".format(self.frameCount * (1 / fps)))

                #If it's in portrait mode, rotate video
                if self.isPortrait:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                #If the video is wrongly rotated previously, rotates it back
                if self.rotateVideo:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)


                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, rejected_img_points = aruco.detectMarkers(gray, aruco_dict, camera_matrix, camera_distortion, parameters=parameters)
                
                #If flag is set, will show rejected areas on the frame
                if self.showRejected:
                    for rejected in rejected_img_points:
                        rejected = rejected.reshape((4, 2))
                        cv2.polylines(frame, [rejected.astype(np.int32)], True, (0, 0, 255), 7, cv2.LINE_AA)

                if corners:
                    aruco.drawDetectedMarkers(frame, corners)

                    eparams = aruco.EstimateParameters_create()

                    #Estimate marker pose, get translation and rotation vectors
                    rvecs, tvecs, obj = aruco.estimatePoseSingleMarkers(corners, markerSize, camera_matrix, camera_distortion, estimateParameters=eparams)

                    marker_num = range(0, ids.size)

                    for markerIds, markerCorn, index in zip(ids, corners, marker_num):

                        rvec = rvecs[index][0]
                        tvec = tvecs[index][0]

                        #Outline detected markers with yellow lines
                        cv2.polylines(frame, [markerCorn.astype(np.int32)], True, (0, 255, 255), 7, cv2.LINE_AA)
                        
                        #Tag positions(where to place text on screen)
                        markerCorn = markerCorn.reshape(4, 2)
                        markerCorn = markerCorn.astype(int)
                        top_right = markerCorn[0].ravel()
                        top_left = markerCorn[1].ravel()
                        bottom_right = markerCorn[2].ravel()
                        bottom_left = markerCorn[3].ravel()

                        #Draw axes and put text "ID: [NUM]"
                        cv2.drawFrameAxes(frame, camera_matrix, camera_distortion, rvec, tvec, 30, 2)
                        cv2.putText(frame, f"ID:%3.0f"%(markerIds[0]), top_right, cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 1, cv2.LINE_AA)

                        #Show the values on the marker
                        marker_info = " x=%3.0fmm, y=%3.0fmm, z=%2.2fmm"%( tvec[0], tvec[1], tvecs[index][0][2])

                        cv2.putText(frame, marker_info, bottom_right, cv2.FONT_HERSHEY_DUPLEX, 1, (0, 250, 0), 1, cv2.LINE_8)
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                #Saves the current frame into folder
                if self.saveFrameVal:
                    saveFrameToFolder(frame)

                #Resizes the frame, turns it into an image from array and then shows it in the canvas
                frame = cv2.resize(frame, (new_wid, new_hei), interpolation = cv2.INTER_AREA)

                aImg1 = ImageTk.PhotoImage(Image.fromarray(frame))

                self.window_canvas.create_image((start_x, start_y), image=aImg1, anchor=tk.NW)

                #If pause it set, will go here - all the logic is nearly the same as before
                while self.pauseVal:

                    if self.stopThread:
                        self.playIsActive = False
                        return

                    #Safeguard so ret will not be reached while in pause
                    if self.frameCount >= (cap.get(cv2.CAP_PROP_FRAME_COUNT)):
                        self.frameCount = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1)


                    cap.set(cv2.CAP_PROP_POS_FRAMES, self.frameCount)

                    ret, frame = cap.read()

                    if not ret:
                        self.window_canvas.delete("all")
                        self.currentTime.config(text="Current time: ")
                        break
                    
                    #self.currentTime.config(text="Current time: " + str(self.frameCount * (1 / fps)))
                    self.currentTime.config(text="Current time: {:.4f}sec".format(self.frameCount * (1 / fps)))

                    if self.isPortrait:
                        frame = cv2.rotate(frame, cv2.ROTATE_180)

                    if self.rotateVideo:
                        frame = cv2.rotate(frame, cv2.ROTATE_180)

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    corners, ids, rejected_img_points = aruco.detectMarkers(gray, aruco_dict, camera_matrix, camera_distortion, parameters=parameters)

                    if self.showRejected:
                        for rejected in rejected_img_points:
                            rejected = rejected.reshape((4, 2))
                            cv2.polylines(frame, [rejected.astype(np.int32)], True, (0, 0, 255), 7, cv2.LINE_AA)

                    if corners:
                        aruco.drawDetectedMarkers(frame, corners)

                        eparams = aruco.EstimateParameters_create()

                        #Estimate marker pose, get translation and rotation vectors
                        rvecs, tvecs, obj = aruco.estimatePoseSingleMarkers(corners, markerSize, camera_matrix, camera_distortion, estimateParameters=eparams)

                        marker_num = range(0, ids.size)

                        for markerIds, markerCorn, index in zip(ids, corners, marker_num):

                            rvec = rvecs[index][0]
                            tvec = tvecs[index][0]

                            #Outline detected markers with yellow lines
                            cv2.polylines(frame, [markerCorn.astype(np.int32)], True, (0, 255, 255), 7, cv2.LINE_AA)
                            
                            #Tag positions(where to place text on screen)
                            markerCorn = markerCorn.reshape(4, 2)
                            markerCorn = markerCorn.astype(int)
                            top_right = markerCorn[0].ravel()
                            top_left = markerCorn[1].ravel()
                            bottom_right = markerCorn[2].ravel()
                            bottom_left = markerCorn[3].ravel()

                            #Draw axes and put text "ID: [NUM]"
                            cv2.drawFrameAxes(frame, camera_matrix, camera_distortion, rvec, tvec, 30, 2)
                            cv2.putText(frame, f"ID:%3.0f"%(markerIds[0]), top_right, cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 1, cv2.LINE_AA)

                            #Show the values on the marker
                            marker_info = " x=%3.0fmm, y=%3.0fmm, z=%2.2fmm"%( tvec[0], tvec[1], tvecs[index][0][2])

                            cv2.putText(frame, marker_info, bottom_right, cv2.FONT_HERSHEY_DUPLEX, 1, (0, 250, 0), 1, cv2.LINE_8)

                    
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    if self.saveFrameVal:
                        saveFrameToFolder(frame)
                    
                    #if self.frameChange:
                    self.frameChange = False

                    frame = cv2.resize(frame, (new_wid, new_hei), interpolation = cv2.INTER_AREA)

                    aImg1 = ImageTk.PhotoImage(Image.fromarray(frame))
                    self.window_canvas.create_image((start_x, start_y), image=aImg1, anchor=tk.NW)

                    if self.stopThread:
                        self.playIsActive = False
                        return

                    if not self.pauseVal:
                        break

                prev_time = current_Time

        cap.release()

        #Sets 2 flags to false and sets the text on start video button
        self.playIsActive = False
        self.stopThread = False
        self.startButton.config(text="Start video")

    
    #Creates the canvases
    def windowTry(self):
        global img, img1

        can_wid, can_hei = 600, 400

        self.border_canvas = tk.Canvas(self, height=can_hei+6, width=can_wid+6, bg="black")
        self.window_canvas = tk.Canvas(self, height=can_hei, width=can_wid, bg="#dbdbd0")

        self.border_canvas2 = tk.Canvas(self, height=can_hei+6, width=can_wid+6, bg="black")
        self.graph_canvas = tk.Canvas(self, height=can_hei, width=can_wid, bg="#dbdbd0")

        self.window_canvas.pack()
        self.border_canvas.pack()

        self.window_canvas.place(x=650, y=80)
        self.border_canvas.place(x=647, y=77)

        self.graph_canvas.place(x=25, y=80)
        self.border_canvas2.place(x=22, y=77)


#Window where user can pick settings for ArUco
class secondWindow(tk.Frame):
    videoPath = ""
    matrixPath = ""
    usedDict = ""
    def __init__(self, master):
        super().__init__(master)

        self.pack_propagate(False)
        self.config(height=720, width=1280)
        self.pack(fill="both", expand=True)

        #Creates the canvas for the marker, labels and buttons/text
        labelCan = tk.Canvas(self, height=300, width=200)
        labelCan.place(x=240, y=150)
        infoCan = tk.Canvas(self, height=300, width=400)
        infoCan.place(x=400, y=150)
        self.markerCan = tk.Canvas(self, height=300, width=300)
        self.markerCan.place(x=850, y=150)

        #Sets the labels
        lbl = tk.Label(labelCan, text="ArUco Dictionary", font=('bold', 12)).grid(row=0, column=0, sticky="E", pady=4, padx=3)
        lbl = tk.Label(labelCan, text="Marker size (mm)", font=('bold', 12)).grid(row=1, column=0, sticky="E", pady=4, padx=3)
        lbl = tk.Label(labelCan, text="Matrix file", font=('bold', 12)).grid(row=2, column=0, sticky="E", pady=4, padx=3)
        lbl = tk.Label(labelCan, text="Video file", font=('bold', 12)).grid(row=3, column=0, sticky="E", pady=4, padx=3)

        #Size options for labels
        sizeOptions = {'height' : 1, 'width' : 50}
        locOptions = {'column' : 0, 'sticky' : 'W', 'pady' : 6, 'padx' : 3}
        self.val = tk.StringVar(self)

        #Dictionary options
        self.Dictionary = [
                        "DICT_4X4_50",
                        "DICT_4X4_100",
                        "DICT_4X4_250",
                        "DICT_4X4_1000",
                        "DICT_5X5_50",
                        "DICT_5X5_100",
                        "DICT_5X5_250",
                        "DICT_5X5_1000",
                        "DICT_6X6_50",
                        "DICT_6X6_100",
                        "DICT_6X6_250",
                        "DICT_6X6_1000",
                        "DICT_7X7_50",
                        "DICT_7X7_100",
                        "DICT_7X7_250",
                        "DICT_7X7_1000",
                        "DICT_ARUCO_ORIGINAL"
                        ]
        
        lbl2 = tk.Label(self, text="Example marker from selected dictionary:", font=('bold', 12)).place(x=855, y=125)

        #Dropdown menu
        self.arucoDic_choice = ttk.OptionMenu(infoCan, self.val, self.Dictionary[16], direction='below',
                                         command=self.callback, *self.Dictionary, style = 'raised.TMenubutton')
        self.arucoDic_choice.grid(row=0, column=0, sticky="WE", pady=4, padx=3)

        self.markerSize_text = tk.Text(infoCan, **sizeOptions)
        self.markerSize_text.grid(row=1, **locOptions)

        self.mtxPathBtn = tk.Button(infoCan, text="Choose matrix file...", font=('bold', 9), height=1, command=self.askMtx)
        self.mtxPathBtn.grid(row=2, column=0, sticky="WE", pady = 3)

        self.vidPathBtn = tk.Button(infoCan, text="Choose video file...", font=('bold', 9), height=1, command=self.askVid)
        self.vidPathBtn.grid(row=3, column=0, sticky="WE", pady = 3)

        self.restoreDef = tk.Button(self, text="Restore default values", font=('bold', 13), width=18, height=1, command=self.restoreDefaults).place(x=400, y=300)
        self.applySet = tk.Button(self, text="Apply settings", font=('bold', 13), width=18, height=1, command=self.applySettings).place(x=640, y=300)

        self.messageLabel = tk.Label(self, text="", font=("Times New Roman", 16))
        self.messageLabel.place(x=500, y=50)

        #Gets the values from file
        self.updateValues()


    #Asks for the video from user, although no currently specified extension is set
    def askVid(self):
        temp = fd.askopenfilename()

        if len(temp) > 0:
            secondWindow.videoPath = temp

    #Asks for the matrix from user, although no currently specified extension is set
    def askMtx(self):
        temp = fd.askopenfilename()

        if len(temp) > 0:
            secondWindow.matrixPath = temp


    #Writes the settings into a text file
    def applySettings(self):
        def vanishText():
            self.messageLabel.config(text="")

        self.restore = False

        ArucoMain.paramChanged = True

        curValues = []

        #Checks if file exists, if not, creates it
        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/arucoValues.txt"

        if not os.path.exists(folderLoc):
            os.makedirs(folderLoc)

        if not os.path.exists(location):
            f = open(location, 'x')
            f.close()


        #Gets the selected dictionary
        dictVal = 0
        for string in self.Dictionary:
            if(string == self.val.get().strip()):
                break
            dictVal = dictVal + 1
            if dictVal >= 17:
                dictVal = 16
                break

        curValues.append(str(dictVal))

        try:
            curValues.append(str(float(self.markerSize_text.get('1.0', tk.END).strip())))
        except ValueError:
            curValues.append("100.0")

        values = ";".join(curValues)
        f = open(location, 'w')
        f.write(values)
        f.close()

        curValues.clear()
        self.updateValues()
        
        self.messageLabel.config(text="New settings applied")
        self.after(5000, vanishText)


    #Restores default values (from opencv) and writes them into the file
    def restoreDefaults(self):

        def vanishText():
            self.messageLabel.config(text="")

        self.restore = False

        ArucoMain.paramChanged = True

        defVals = ["16", "100"]

        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/arucoValues.txt"

        if not os.path.exists(folderLoc):
            os.makedirs(folderLoc)

        if not os.path.exists(location):
            f = open(location, 'x')
            f.close()

        
        values = ";".join(defVals)
        f = open(location, 'w')
        f.write(values)
        f.close()

        self.updateValues()

        self.messageLabel.config(text="New settings applied")
        self.after(5000, vanishText)

    #Updates the values in text slots and the sample marker image
    def updateValues(self):
        currentValues = []
        self.restore = False

        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/arucoValues.txt"

        if not os.path.exists(folderLoc):
            self.restore = True

        if not os.path.exists(location):
            self.restore = True

        if self.restore is True:
            self.restoreDefaults()

        f = open(location, "r")
        line = f.readline().rstrip()
        currentValues.extend(line.split(";"))
        f.close()

        if len(currentValues) < 2 or len(currentValues) > 2:
            self.restoreDefaults()
            return


        if int(currentValues[0]) >= 17:
            self.val.set(self.Dictionary[16])
            self.applySettings()
            secondWindow.usedDict = self.Dictionary[int(currentValues[0])]
        else:
            self.val.set(self.Dictionary[int(currentValues[0])])
            secondWindow.usedDict = self.Dictionary[int(currentValues[0])]


        try:
            temp = float(currentValues[1])
        except ValueError:
            currentValues[1] = 100

        self.markerSize_text.delete('1.0', tk.END)
        self.markerSize_text.insert(tk.INSERT, float(currentValues[1]))


        #Places and resizes the sample marker image
        def placeImage(fileName):
            global mImg, mImg1
            can_wid = 300
            can_hei = 300

            folderLoc = os.path.join(sys.path[0] + "/misc" + "/markers/")
            location = folderLoc + fileName

            if not os.path.exists(folderLoc):
                return

            try:
                mImg = Image.open(location)
            except:
                return

            img_wid = mImg.size[0]
            img_hei = mImg.size[1]

            if img_wid > img_hei:
                ratio = can_wid / img_wid
                new_wid = int(img_wid * ratio)
                new_hei = int(img_hei * ratio)

                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

                if new_hei > can_hei:
                    other_ratio = can_hei / new_hei
                    new_wid = int(img_wid * other_ratio)
                    new_hei = int(img_hei * other_ratio)

                    start_x = int(((can_wid - new_wid) / 2) + 2)
                    start_y = int(((can_hei - new_hei) / 2) + 2)


            elif img_hei >= img_wid:
                ratio = can_hei / img_hei
                new_wid = int(img_wid * ratio)
                new_hei = int(img_hei * ratio)

                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

                if new_wid > can_wid:
                    other_ratio = can_wid / new_wid
                    new_wid = int(img_wid * other_ratio)
                    new_hei = int(img_hei * other_ratio)

                    start_x = int(((can_wid - new_wid) / 2) + 2)
                    start_y = int(((can_hei - new_hei) / 2) + 2)
            
            mImg = mImg.resize((new_wid, new_hei), Image.Resampling.LANCZOS)
            mImg1 = ImageTk.PhotoImage(mImg)

            self.markerCan.create_image(start_x, start_y, image=mImg1, anchor=tk.NW)

        if int(currentValues[0]) <= 3:
            placeImage("4by4.png")
        elif int(currentValues[0]) <= 7  and int(currentValues[0]) >= 4:
            placeImage("5by5.png")
        elif int(currentValues[0]) <= 11  and int(currentValues[0]) >= 8:
            placeImage("6by6.png")
        elif int(currentValues[0]) <= 15  and int(currentValues[0]) >= 12:
            placeImage("7by7.png")
        else:
            placeImage("original.png")

    #Marker image logic once again, though this should update it when a new selection is gotten from dropdown menu
    def callback(self, selection):
        counter = 0
        for marker in self.Dictionary:
            if self.val.get() == marker:
                break
            counter = counter + 1


        def placeImage(fileName):
            global mImg, mImg1
            can_wid = 300
            can_hei = 300

            folderLoc = os.path.join(sys.path[0] + "/misc" + "/markers/")
            location = folderLoc + fileName

            if not os.path.exists(folderLoc):
                return(self.val.get()) 

            try:
                mImg = Image.open(location)
            except:
                return(self.val.get()) 

            img_wid = mImg.size[0]
            img_hei = mImg.size[1]

            if img_wid > img_hei:
                ratio = can_wid / img_wid
                new_wid = int(img_wid * ratio)
                new_hei = int(img_hei * ratio)

                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

                if new_hei > can_hei:
                    other_ratio = can_hei / new_hei
                    new_wid = int(img_wid * other_ratio)
                    new_hei = int(img_hei * other_ratio)

                    start_x = int(((can_wid - new_wid) / 2) + 2)
                    start_y = int(((can_hei - new_hei) / 2) + 2)


            elif img_hei >= img_wid:
                ratio = can_hei / img_hei
                new_wid = int(img_wid * ratio)
                new_hei = int(img_hei * ratio)

                start_x = int(((can_wid - new_wid) / 2) + 2)
                start_y = int(((can_hei - new_hei) / 2) + 2)

                if new_wid > can_wid:
                    other_ratio = can_wid / new_wid
                    new_wid = int(img_wid * other_ratio)
                    new_hei = int(img_hei * other_ratio)

                    start_x = int(((can_wid - new_wid) / 2) + 2)
                    start_y = int(((can_hei - new_hei) / 2) + 2)
            
            mImg = mImg.resize((new_wid, new_hei), Image.Resampling.LANCZOS)
            mImg1 = ImageTk.PhotoImage(mImg)

            self.markerCan.create_image(start_x, start_y, image=mImg1, anchor=tk.NW)

        if counter <= 3:
            placeImage("4by4.png")
        elif counter <= 7  and counter >= 4:
            placeImage("5by5.png")
        elif counter <= 11  and counter >= 8:
            placeImage("6by6.png")
        elif counter <= 15  and counter >= 12:
            placeImage("7by7.png")
        else:
            placeImage("original.png")

        return(self.val.get()) 



#Window where parameters can be set
class thirdWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.holdCurrentValues = []
        self.isLoaded = False

        self.pack_propagate(False)
        self.config(height=720, width=1280)
        self.pack(fill="both", expand=True)

        self.restoreDef = tk.Button(self, text="Restore default values", font=('bold', 13), width=18, height=1, command=self.restoreDefaultParams).place(x=510, y=600)
        self.applySet = tk.Button(self, text="Apply settings", font=('bold', 13), width=18, height=1, command = self.applyNewValues).place(x=745, y=600)

        labelCanvas = tk.Canvas(self, height=500, width=200)
        labelCanvas.place(x=10, y=50)

        textCanvas = tk.Canvas(self, height=475, width=200,bd=0)
        textCanvas.place(x=320, y=50)

        secondLabelCanvas = tk.Canvas(self, height=500, width=200)
        secondLabelCanvas.place(x=630, y=50)

        secondTextCanvas = tk.Canvas(self, height=475, width=200,bd=0)
        secondTextCanvas.place(x=920, y=50)

        #Label names and information when you hover over them
        self.labelNames = [
        "cornerRefinementMethod",
        "cornerRefinementMaxIterations",
        "cornerRefinementWinSize",
        "cornerRefinementMinAccuracy",
        "polygonalApproxAccuracyRate",
        "perspectiveRemovePixelPerCell",
        "maxErroneousBitsInBorderRate",
        "errorCorrectionRate",
        "markerBorderBits",
        "adaptiveThreshWinSizeStep",
        "adaptiveThreshWinSizeMax",
        "adaptiveThreshWinSizeMin",
        "maxMarkerPerimeterRate",
        "minMarkerPerimeterRate",
        "perspectiveRemoveIgnoredMarginPerCell",
        "minSideLengthCanonicalImg",
        "minOtsuStdDev",
        "minMarkerLengthRatioOriginalImg",
        "minMarkerDistanceRate",
        "minDistanceToBorder",
        "minCornerDistanceRate",
        "adaptiveThreshConstant",
        "detectInvertedMarker",
        "useAruco3Detection"
        ]


        self.info = [
        "More info at https://docs.opencv.org/4.x/de/d67/group__objdetect__aruco.html#gafce26321f39d331bc12032a72b90eda6",
        "maximum number of iterations for stop criteria of the corner refinement process (default 30). ",
        "window size for the corner refinement process (in pixels) (default 5). ",
        "minimum error for the stop cristeria of the corner refinement process (default: 0.1) ",
        "minimum accuracy during the polygonal approximation process to determine which contours are squares. (default 0.03) ",
        "number of bits (per dimension) for each cell of the marker when removing the perspective (default 4). ",
        " maximum number of accepted erroneous bits in the border (i.e. number of allowed white bits in the border). Represented as a rate respect to the total number of bits per marker (default 0.35).",
        "error correction rate respect to the maximun error correction capability for each dictionary (default 0.6). ",
        "number of bits of the marker border, i.e. marker border width (default 1). ",
        "increments from adaptiveThreshWinSizeMin to adaptiveThreshWinSizeMax during the thresholding (default 10). ",
        "maximum window size for adaptive thresholding before finding contours (default 23). ",
        "minimum window size for adaptive thresholding before finding contours (default 3). ",
        "determine maximum perimeter for marker contour to be detected. This is defined as a rate respect to the maximum dimension of the input image (default 4.0).",
        "minimum mean distance beetween two marker corners to be considered imilar, so that the smaller one is removed. The rate is relative to the smaller perimeter of the two markers (default 0.05).",
        "width of the margin of pixels on each cell not considered for the determination of the cell bit. Represents the rate respect to the total size of the cell, i.e. perspectiveRemovePixelPerCell (default 0.13)",
        "minimum side length of a marker in the canonical image. Latter is the binarized image in which contours are searched. ",
        "minimun standard deviation in pixels values during the decodification step to apply Otsu thresholding (otherwise, all the bits are set to 0 or 1 depending on mean higher than 128 or not) (default 5.0) ",
        "range [0,1], eq (2) from paper. The parameter tau_i has a direct influence on the processing speed. ",
        "minimum mean distance beetween two marker corners to be considered imilar, so that the smaller one is removed. The rate is relative to the smaller perimeter of the two markers (default 0.05).",
        "minimum distance of any corner to the image border for detected markers (in pixels) (default 3) ",
        "minimum distance between corners for detected markers relative to its perimeter (default 0.05) ",
        "constant for adaptive thresholding before finding contours (default 7) ",
        "to check if there is a white marker. In order to generate a 'white' marker just invert a normal marker by using a tilde, ~markerImage. (default false)",
        "enable the new and faster Aruco detection strategy. Proposed in the paper: Romero-Ramirez et al: Speeded up detection of squared fiducial markers (2018) https://www.researchgate.net/publication/325787310_Speeded_Up_Detection_of_Squared_Fiducial_Markers"
        ]

        self.num = 0
        dictionary = {}
        
        #Creates the labels for parameters and sets the tooptips
        for self.i in self.labelNames:
            if self.num > 14:
                dictionary["lbl{0}".format(self.num)] = tk.Label(secondLabelCanvas, text=self.i, font=('bold', 12))
                dictionary["lbl{0}".format(self.num)].grid(row=self.num - 15, column=0, sticky="E", pady=4, padx=3)
                ToolTip(dictionary["lbl{0}".format(self.num)], msg=self.info[self.num], delay=0.5)
            else:
                dictionary["lbl{0}".format(self.num)] = tk.Label(labelCanvas, text=self.i, font=('bold', 12))
                dictionary["lbl{0}".format(self.num)].grid(row=self.num, column=0, sticky="E", pady=4, padx=3)
                ToolTip(dictionary["lbl{0}".format(self.num)], msg=self.info[self.num], delay=0.5)
            self.num = self.num + 1


        self.messageLabel = tk.Label(self, text="", font=("Times New Roman", 16))
        self.messageLabel.place(x=620, y=550)

        #Refinement methods for dropdown menu
        self.RefinementMethods = [
                             "CORNER_REFINE_NONE", 
                             "CORNER_REFINE_SUBPIX",
                             "CORNER_REFINE_CONTOUR"
                             ]
        
        sizeOptions = {'height' : 1, 'width' : 35}
        locOptions = {'column' : 0, 'sticky' : 'WE', 'pady' : 6, 'padx' : 3}
        self.val = tk.StringVar(self)

        self.currentValues = []
        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/paramValues.txt"

        self.overwriteFlag = False

        try:
            f = open(location, "r")
            line = f.readline().rstrip()
            self.currentValues.extend(line.split(";"))
            f.close()

        except FileNotFoundError:
            self.restoreDefaultParams()
            f = open(location, "r")
            line = f.readline().rstrip()
            self.currentValues.extend(line.split(";"))
            f.close()

        counter = 0
        paraDefaults = ["1", "30", "5", "0.1", "0.03", "4", "0.35", "0.6", "1", "10", "23",
                         "3", "4.0", "0.05", "0.13", "1", "5.0", "0.1", "0.05", "3", "0.05", "7", "0", "0"]

        #Checks if values are correct, if they aren't, they will be overwritten and set to default
        for val in self.currentValues:
            if counter == 0 or counter == 1 or counter == 2 or counter == 5 or counter == 8 or counter == 9 or counter == 10 or counter == 11 or counter == 15 or counter == 19 or counter == 21 or counter == 22 or counter == 23:
                try:
                    temp = int(val)
                except ValueError:
                    self.currentValues[counter] = paraDefaults[counter]
                    self.overwriteFlag = True
            else:
                try:
                    temp = float(val)
                except ValueError:
                    self.currentValues[counter] = paraDefaults[counter]
                    self.overwriteFlag = True

            counter = counter + 1

        #Creates dropdown menu to select refinement method from
        try:
            if int(self.currentValues[0]) >= 3:
                self.currentValues[0] = '1'
                self.cornerRefinementMethod_choice = ttk.OptionMenu(textCanvas, self.val, self.RefinementMethods[int(self.currentValues[0])], direction='below', *self.RefinementMethods,
                                                                    command = self.callback, style = 'raised.TMenubutton')
                self.cornerRefinementMethod_choice.grid(row=0, column=0, sticky="WE", pady=4, padx=3)
                self.overwriteFlag = True
            else:
                self.cornerRefinementMethod_choice = ttk.OptionMenu(textCanvas, self.val, self.RefinementMethods[int(self.currentValues[0])], direction='below', *self.RefinementMethods,
                                                                    command = self.callback, style = 'raised.TMenubutton')
                self.cornerRefinementMethod_choice.grid(row=0, column=0, sticky="WE", pady=4, padx=3)
        except IndexError:
                self.currentValues.append("1")
                self.cornerRefinementMethod_choice = ttk.OptionMenu(textCanvas, self.val, self.RefinementMethods[int(self.currentValues[0])], direction='below', *self.RefinementMethods,
                                                                    command = self.callback, style = 'raised.TMenubutton')
                self.cornerRefinementMethod_choice.grid(row=0, column=0, sticky="WE", pady=4, padx=3)
                self.overwriteFlag = True
    

        #Creates rest of the text boxes and sets their values
        self.cornerRefinementMaxIterations_text = tk.Text(textCanvas, **sizeOptions)
        self.cornerRefinementMaxIterations_text.grid(row=1, **locOptions)
        try:
            self.cornerRefinementMaxIterations_text.insert(tk.INSERT, int(self.currentValues[1]))
        except IndexError:
            self.currentValues.append(paraDefaults[1])
            self.overwriteFlag = True
            self.cornerRefinementMaxIterations_text.insert(tk.INSERT, int(self.currentValues[1]))

        self.cornerRefinementWinSize_text = tk.Text(textCanvas, **sizeOptions)
        self.cornerRefinementWinSize_text.grid(row=2, **locOptions)
        try:
            self.cornerRefinementWinSize_text.insert(tk.INSERT, int(self.currentValues[2]))
        except IndexError:
            self.currentValues.append(paraDefaults[2])
            self.overwriteFlag = True
            self.cornerRefinementWinSize_text.insert(tk.INSERT, int(self.currentValues[2]))

        self.cornerRefinementMinAccuracy_text = tk.Text(textCanvas, **sizeOptions)
        self.cornerRefinementMinAccuracy_text.grid(row=3, **locOptions)
        try:
            self.cornerRefinementMinAccuracy_text.insert(tk.INSERT, float(self.currentValues[3]))
        except IndexError:
            self.currentValues.append(paraDefaults[3])
            self.overwriteFlag = True
            self.cornerRefinementMinAccuracy_text.insert(tk.INSERT, float(self.currentValues[3]))

        self.polygonalApproxAccuracyRate_text = tk.Text(textCanvas, **sizeOptions)
        self.polygonalApproxAccuracyRate_text.grid(row=4, **locOptions)
        try:
            self.polygonalApproxAccuracyRate_text.insert(tk.INSERT, float(self.currentValues[4]))
        except IndexError:
            self.currentValues.append(paraDefaults[4])
            self.overwriteFlag = True
            self.polygonalApproxAccuracyRate_text.insert(tk.INSERT, float(self.currentValues[4]))

        self.perspectiveRemovePixelPerCell_text = tk.Text(textCanvas, **sizeOptions)
        self.perspectiveRemovePixelPerCell_text.grid(row=5, **locOptions)
        try:
            self.perspectiveRemovePixelPerCell_text.insert(tk.INSERT, int(self.currentValues[5]))
        except IndexError:
            self.currentValues.append(paraDefaults[5])
            self.overwriteFlag = True
            self.perspectiveRemovePixelPerCell_text.insert(tk.INSERT, int(self.currentValues[5]))

        self.maxErroneousBitsInBorderRate_text = tk.Text(textCanvas, **sizeOptions)
        self.maxErroneousBitsInBorderRate_text.grid(row=6, **locOptions)
        try:
            self.maxErroneousBitsInBorderRate_text.insert(tk.INSERT, float(self.currentValues[6]))
        except IndexError:
            self.currentValues.append(paraDefaults[6])
            self.overwriteFlag = True
            self.maxErroneousBitsInBorderRate_text.insert(tk.INSERT, float(self.currentValues[6]))

        self.errorCorrectionRate_text = tk.Text(textCanvas, **sizeOptions)
        self.errorCorrectionRate_text.grid(row=7, **locOptions)
        try:
            self.errorCorrectionRate_text.insert(tk.INSERT, float(self.currentValues[7]))
        except IndexError:
            self.currentValues.append(paraDefaults[7])
            self.overwriteFlag = True
            self.errorCorrectionRate_text.insert(tk.INSERT, float(self.currentValues[7]))

        self.markerBorderBits_text = tk.Text(textCanvas, **sizeOptions)
        self.markerBorderBits_text.grid(row=8, **locOptions)
        try:
            self.markerBorderBits_text.insert(tk.INSERT, int(self.currentValues[8]))
        except IndexError:
            self.currentValues.append(paraDefaults[8])
            self.overwriteFlag = True
            self.markerBorderBits_text.insert(tk.INSERT, int(self.currentValues[8]))

        self.adaptiveThreshWinSizeStep_text = tk.Text(textCanvas, **sizeOptions)
        self.adaptiveThreshWinSizeStep_text.grid(row=9, **locOptions)
        try:
            self.adaptiveThreshWinSizeStep_text.insert(tk.INSERT, int(self.currentValues[9]))
        except IndexError:
            self.currentValues.append(paraDefaults[9])
            self.overwriteFlag = True
            self.adaptiveThreshWinSizeStep_text.insert(tk.INSERT, int(self.currentValues[9]))

        self.adaptiveThreshWinSizeMax_text = tk.Text(textCanvas, **sizeOptions)
        self.adaptiveThreshWinSizeMax_text.grid(row=10, **locOptions)
        try:
            self.adaptiveThreshWinSizeMax_text.insert(tk.INSERT, int(self.currentValues[10]))
        except IndexError:
            self.currentValues.append(paraDefaults[10])
            self.overwriteFlag = True
            self.adaptiveThreshWinSizeMax_text.insert(tk.INSERT, int(self.currentValues[10]))

        self.adaptiveThreshWinSizeMin_text = tk.Text(textCanvas, **sizeOptions)
        self.adaptiveThreshWinSizeMin_text.grid(row=11, **locOptions)
        try:
            self.adaptiveThreshWinSizeMin_text.insert(tk.INSERT, int(self.currentValues[11]))
        except IndexError:
            self.currentValues.append(paraDefaults[11])
            self.overwriteFlag = True
            self.adaptiveThreshWinSizeMin_text.insert(tk.INSERT, int(self.currentValues[11]))

        self.maxMarkerPerimeterRate_text = tk.Text(textCanvas,**sizeOptions)
        self.maxMarkerPerimeterRate_text.grid(row=12, **locOptions)
        try:
            self.maxMarkerPerimeterRate_text.insert(tk.INSERT, float(self.currentValues[12]))
        except IndexError:
            self.currentValues.append(paraDefaults[12])
            self.overwriteFlag = True
            self.maxMarkerPerimeterRate_text.insert(tk.INSERT, float(self.currentValues[12]))

        self.minMarkerPerimeterRate_text = tk.Text(textCanvas, **sizeOptions)
        self.minMarkerPerimeterRate_text.grid(row=13, **locOptions)
        try:
            self.minMarkerPerimeterRate_text.insert(tk.INSERT, float(self.currentValues[13]))
        except IndexError:
            self.currentValues.append(paraDefaults[13])
            self.overwriteFlag = True
            self.minMarkerPerimeterRate_text.insert(tk.INSERT, float(self.currentValues[13]))

        self.perspectiveRemoveIgnoredMarginPerCell_text = tk.Text(textCanvas, **sizeOptions)
        self.perspectiveRemoveIgnoredMarginPerCell_text.grid(row=14, **locOptions)
        try:
            self.perspectiveRemoveIgnoredMarginPerCell_text.insert(tk.INSERT, float(self.currentValues[14]))
        except IndexError:
            self.currentValues.append(paraDefaults[14])
            self.overwriteFlag = True
            self.perspectiveRemoveIgnoredMarginPerCell_text.insert(tk.INSERT, float(self.currentValues[14]))

        self.minSideLengthCanonicalImg_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minSideLengthCanonicalImg_text.grid(row=0, **locOptions)
        try:
            self.minSideLengthCanonicalImg_text.insert(tk.INSERT, int(self.currentValues[15]))
        except IndexError:
            self.currentValues.append(paraDefaults[15])
            self.overwriteFlag = True
            self.minSideLengthCanonicalImg_text.insert(tk.INSERT, int(self.currentValues[15]))

        self.minOtsuStdDev_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minOtsuStdDev_text.grid(row=1, **locOptions)
        try:
            self.minOtsuStdDev_text.insert(tk.INSERT, float(self.currentValues[16]))
        except IndexError:
            self.currentValues.append(paraDefaults[16])
            self.overwriteFlag = True
            self.minOtsuStdDev_text.insert(tk.INSERT, float(self.currentValues[16]))

        self.minMarkerLengthRatioOriginalImg_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minMarkerLengthRatioOriginalImg_text.grid(row=2, **locOptions)
        try:
            self.minMarkerLengthRatioOriginalImg_text.insert(tk.INSERT, float(self.currentValues[17]))
        except IndexError:
            self.currentValues.append(paraDefaults[17])
            self.overwriteFlag = True
            self.minMarkerLengthRatioOriginalImg_text.insert(tk.INSERT, float(self.currentValues[17]))

        self.minMarkerDistanceRate_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minMarkerDistanceRate_text.grid(row=3, **locOptions)
        try:
            self.minMarkerDistanceRate_text.insert(tk.INSERT, float(self.currentValues[18]))
        except IndexError:
            self.currentValues.append(paraDefaults[18])
            self.overwriteFlag = True
            self.minMarkerDistanceRate_text.insert(tk.INSERT, float(self.currentValues[18]))

        self.minDistanceToBorder_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minDistanceToBorder_text.grid(row=4, **locOptions)
        try:
            self.minDistanceToBorder_text.insert(tk.INSERT, int(self.currentValues[19]))
        except IndexError:
            self.currentValues.append(paraDefaults[19])
            self.overwriteFlag = True
            self.minDistanceToBorder_text.insert(tk.INSERT, int(self.currentValues[19]))

        self.minCornerDistanceRate_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.minCornerDistanceRate_text.grid(row=5, **locOptions)
        try:
            self.minCornerDistanceRate_text.insert(tk.INSERT, float(self.currentValues[20]))
        except IndexError:
            self.currentValues.append(paraDefaults[20])
            self.overwriteFlag = True
            self.minCornerDistanceRate_text.insert(tk.INSERT, float(self.currentValues[20]))

        self.adaptiveThreshConstant_text = tk.Text(secondTextCanvas, **sizeOptions)
        self.adaptiveThreshConstant_text.grid(row=6, **locOptions)
        try:
            self.adaptiveThreshConstant_text.insert(tk.INSERT, int(self.currentValues[21]))
        except IndexError:
            self.currentValues.append(paraDefaults[21])
            self.overwriteFlag = True
            self.adaptiveThreshConstant_text.insert(tk.INSERT, int(self.currentValues[21]))

        self.dIMVar = tk.IntVar()
        try:
            self.dIMVar.set(int(self.currentValues[22]))
        except IndexError:
            self.dIMVar.set(int(paraDefaults[22]))
            self.currentValues.append(paraDefaults[22])
            self.overwriteFlag = True
        self.detectInvertedMarker_check = tk.Checkbutton(secondTextCanvas, variable=self.dIMVar, onvalue=1, offvalue=0)
        self.detectInvertedMarker_check.grid(row=7)

        self.uA3DVar = tk.IntVar()
        try:
            self.uA3DVar.set(int(self.currentValues[23]))
        except IndexError:
            self.uA3DVar.set(int(paraDefaults[23]))
            self.currentValues.append(paraDefaults[23])
            self.overwriteFlag = True
        self.useAruco3Detection_check = tk.Checkbutton(secondTextCanvas, variable=self.uA3DVar, onvalue=1, offvalue=0)
        self.useAruco3Detection_check.grid(row=8)

        self.holdCurrentValues = self.currentValues

        self.isLoaded = True

        #If overwrite was set, new settings will be applied
        if self.overwriteFlag:
            self.applyNewValues()
            #self.overwriteFlag = False




    #Updates the values of the text boxes and dropdown menu
    def updateValues(self):
        currentValues = []
        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/paramValues.txt"

        if not os.path.exists(folderLoc):
            return

        if not os.path.exists(location):
            return

        f = open(location, "r")
        line = f.readline().rstrip()
        currentValues.extend(line.split(";"))
        f.close()


        if int(currentValues[0]) >= 3:
            self.val.set(self.RefinementMethods[1])
            self.applyNewValues()
        else:
            self.val.set(self.RefinementMethods[int(currentValues[0])])


        self.cornerRefinementMaxIterations_text.delete('1.0', tk.END)
        self.cornerRefinementMaxIterations_text.insert(tk.INSERT, int(currentValues[1]))

        self.cornerRefinementWinSize_text.delete('1.0', tk.END)
        self.cornerRefinementWinSize_text.insert(tk.INSERT, int(currentValues[2]))

        self.cornerRefinementMinAccuracy_text.delete('1.0', tk.END)
        self.cornerRefinementMinAccuracy_text.insert(tk.INSERT, float(currentValues[3]))

        self.polygonalApproxAccuracyRate_text.delete('1.0', tk.END)
        self.polygonalApproxAccuracyRate_text.insert(tk.INSERT, float(currentValues[4]))

        self.perspectiveRemovePixelPerCell_text.delete('1.0', tk.END)
        self.perspectiveRemovePixelPerCell_text.insert(tk.INSERT, int(currentValues[5]))

        self.maxErroneousBitsInBorderRate_text.delete('1.0', tk.END)
        self.maxErroneousBitsInBorderRate_text.insert(tk.INSERT, float(currentValues[6]))

        self.errorCorrectionRate_text.delete('1.0', tk.END)
        self.errorCorrectionRate_text.insert(tk.INSERT, float(currentValues[7]))

        self.markerBorderBits_text.delete('1.0', tk.END)
        self.markerBorderBits_text.insert(tk.INSERT, int(currentValues[8]))

        self.adaptiveThreshWinSizeStep_text.delete('1.0', tk.END)
        self.adaptiveThreshWinSizeStep_text.insert(tk.INSERT, int(currentValues[9]))

        self.adaptiveThreshWinSizeMax_text.delete('1.0', tk.END)
        self.adaptiveThreshWinSizeMax_text.insert(tk.INSERT, int(currentValues[10]))

        self.adaptiveThreshWinSizeMin_text.delete('1.0', tk.END)
        self.adaptiveThreshWinSizeMin_text.insert(tk.INSERT, int(currentValues[11]))

        self.maxMarkerPerimeterRate_text.delete('1.0', tk.END)
        self.maxMarkerPerimeterRate_text.insert(tk.INSERT, float(currentValues[12]))

        self.minMarkerPerimeterRate_text.delete('1.0', tk.END)
        self.minMarkerPerimeterRate_text.insert(tk.INSERT, float(currentValues[13]))

        self.perspectiveRemoveIgnoredMarginPerCell_text.delete('1.0', tk.END)
        self.perspectiveRemoveIgnoredMarginPerCell_text.insert(tk.INSERT, float(currentValues[14]))

        self.minSideLengthCanonicalImg_text.delete('1.0', tk.END)
        self.minSideLengthCanonicalImg_text.insert(tk.INSERT, int(currentValues[15]))

        self.minOtsuStdDev_text.delete('1.0', tk.END)
        self.minOtsuStdDev_text.insert(tk.INSERT, float(currentValues[16]))

        self.minMarkerLengthRatioOriginalImg_text.delete('1.0', tk.END)
        self.minMarkerLengthRatioOriginalImg_text.insert(tk.INSERT, float(currentValues[17]))

        self.minMarkerDistanceRate_text.delete('1.0', tk.END)
        self.minMarkerDistanceRate_text.insert(tk.INSERT, float(currentValues[18]))

        self.minDistanceToBorder_text.delete('1.0', tk.END)
        self.minDistanceToBorder_text.insert(tk.INSERT, int(currentValues[19]))

        self.minCornerDistanceRate_text.delete('1.0', tk.END)
        self.minCornerDistanceRate_text.insert(tk.INSERT, float(currentValues[20]))

        self.adaptiveThreshConstant_text.delete('1.0', tk.END)
        self.adaptiveThreshConstant_text.insert(tk.INSERT, int(currentValues[21]))

        self.dIMVar.set(int(currentValues[22]))

        self.uA3DVar.set(int(currentValues[23]))

        currentValues.clear()
        

    #Checks the folder location, values and writes them into a text file
    def applyNewValues(self):

        def vanishText():
            self.messageLabel.config(text="")

        paraDefaults = ["1", "30", "5", "0.1", "0.03", "4", "0.35", "0.6", "1", "10", "23",
                         "3", "4.0", "0.05", "0.13", "1", "5.0", "0.1", "0.05", "3", "0.05", "7", "0", "0"]

        currentValues = []
        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/paramValues.txt"

        if not os.path.exists(folderLoc):
            os.makedirs(folderLoc)

        if not os.path.exists(location):
            f = open(location, 'x')
            f.close()

        
        methodVal = 0
        for string in self.RefinementMethods:
            if(string == self.val.get().strip()):
                break
            methodVal = methodVal + 1
            if methodVal >= 3:
                methodVal = 1
                break

        currentValues.append(str(methodVal))

        try:
            currentValues.append(str(int(self.cornerRefinementMaxIterations_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[1])

        try:
            currentValues.append(str(int(self.cornerRefinementWinSize_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[2])

        try: 
            currentValues.append(str(float(self.cornerRefinementMinAccuracy_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[3])

        try:
            currentValues.append(str(float(self.polygonalApproxAccuracyRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[4])

        try:
            currentValues.append(str(int(self.perspectiveRemovePixelPerCell_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[5])

        try:
            currentValues.append(str(float(self.maxErroneousBitsInBorderRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[6])

        try:
            currentValues.append(str(float(self.errorCorrectionRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[7])

        try:
            currentValues.append(str(int(self.markerBorderBits_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[8])

        try:
            currentValues.append(str(int(self.adaptiveThreshWinSizeStep_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[9])

        try:
            currentValues.append(str(int(self.adaptiveThreshWinSizeMax_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[10])

        try:
            currentValues.append(str(int(self.adaptiveThreshWinSizeMin_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[11])

        try:
            currentValues.append(str(float(self.maxMarkerPerimeterRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[12])

        try:
            currentValues.append(str(float(self.minMarkerPerimeterRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[13])

        try:
            currentValues.append(str(float(self.perspectiveRemoveIgnoredMarginPerCell_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[14])

        try:
            currentValues.append(str(int(self.minSideLengthCanonicalImg_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[15])

        try:
            currentValues.append(str(float(self.minOtsuStdDev_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[16])

        try:   
            currentValues.append(str(float(self.minMarkerLengthRatioOriginalImg_text.get('1.0', tk.END).strip())))

            if float(currentValues[17]) > 1:
                currentValues[17] = "1.0"
            elif float(currentValues[17]) < 0:
                currentValues[17] = "0.0"

        except ValueError:
            currentValues.append(paraDefaults[17])
        
        try:
            currentValues.append(str(float(self.minMarkerDistanceRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[18])

        try:
            currentValues.append(str(int(self.minDistanceToBorder_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[19])

        try:
            currentValues.append(str(float(self.minCornerDistanceRate_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[20])

        try:
            currentValues.append(str(int(self.adaptiveThreshConstant_text.get('1.0', tk.END).strip())))
        except ValueError:
            currentValues.append(paraDefaults[21])

        try:
            currentValues.append(str(self.dIMVar.get()))
        except ValueError:
            currentValues.append(paraDefaults[22])
        
        try:
            currentValues.append(str(self.uA3DVar.get()))
        except ValueError:
            currentValues.append(paraDefaults[23])


        if not self.holdCurrentValues == currentValues or self.overwriteFlag:
            self.holdCurrentValues = currentValues
            self.overwriteFlag = False
            ArucoMain.paramChanged = True


            values = ";".join(currentValues)
            f = open(location, 'w')
            f.write(values)
            f.close()

            self.updateValues()

            self.messageLabel.config(text="Settings applied")
            self.after(5000, vanishText)


    
    #Dropdown menu selection change
    def callback(self, selection):
        return(self.val.get()) 

    #Restores default values and writes them into the file
    def restoreDefaultParams(self):

        def vanishText():
            self.messageLabel.config(text="")

        ArucoMain.paramChanged = True

        paraDefaults = ["1", "30", "5", "0.1", "0.03", "4", "0.35", "0.6", "1", "10", "23",
                         "3", "4.0", "0.05", "0.13", "1", "5.0", "0.1", "0.05", "3", "0.05", "7", "0", "0"]

        folderLoc = os.path.join(sys.path[0] + "/misc" + "/settings")
        location = folderLoc + "/paramValues.txt"


        if not os.path.exists(folderLoc):
            os.makedirs(folderLoc)

        if not os.path.exists(location):
            f = open(location, 'x')
            f.close()

        values = ";".join(paraDefaults)
        f = open(location, 'w')
        f.write(values)
        f.close()

        self.holdCurrentValues = paraDefaults

        if self.isLoaded:
            self.updateValues()

        self.messageLabel.config(text="Settings applied")
        self.after(5000, vanishText)



#Main loop
if __name__ == "__main__":
    app = App()
    frame = MainFrame(app)
    app.mainloop()
