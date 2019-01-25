# Copyright (C) 2018 David Hui. All rights reserved.
# Permission is hereby granted to modify and redistribute this file for educational purposes with attribution.
from pygame import *
import pygame.gfxdraw as gfxdraw
from random import *
import time as ptime
from tkinter import filedialog
from tkinter import messagebox
from tkinter import *
import json
import os
import sys
print("Copyright (c) 2018 David Hui. All rights reserved.")
print("Permission is hereby granted to modify and redistribute this program for educational purposes with attribution.")
dev = True
def smartLog(message, level):
    levelMap = {0: "[CRIT]", 1:"[ERROR]", 2: "[WARN]", 3:"[INFO]"}
    if dev or level < 2:
        print(levelMap[level],message)
        with open("paint.log", "a+") as logFile:
            logFile.write(levelMap[level]+" "+message+"\n")

startTime = ptime.time()
smartLog("Starting initialization process", 3)

smartLog("Development mode is ON! INFO and WARN messages will be displayed!", 3)

# Load the configuration file
smartLog("Loading configuration...", 3)
try:
    with open("config.json", "r") as configFile:
        config = json.load(configFile)
except IOError:
    smartLog("Unable to load configuration! Ensure that config.json exists!", 0)
    sys.exit(1)
except ValueError:
    smartLog("Invalid configuration! Ensure that config.json is valid JSON!", 0)
    sys.exit(1)
try :
    with open(".git/refs/heads/master") as versionFile:
        version = versionFile.read()
except IOError:
    version = "unknown"

smartLog("Loaded configuration!", 3)
smartLog("%d keys loaded into registry" % len(config), 3)

title = config["title"]

size = width, height = config["screenSize"]
screen = display.set_mode(size)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SONG_END = USEREVENT + 1


display.set_caption(title)

backgroundImage = image.load(config["backgroundImage"])
backgroundImage = transform.smoothscale(backgroundImage, size)
screen.blit(backgroundImage, (0,0))

helpImage = image.load(config["helpImage"])
helpImageRect = Rect(width//2-helpImage.get_width()//2, height//2-helpImage.get_height()//2, helpImage.get_width(), helpImage.get_height())

# Control variable
running = True
# Tracks where a drag started
dragStart = (0, 0)
# Tracks where the mouse was at the last loop iteration
lastTickLocation = (0, 0)
# Stores the old canvas when doing drag tools such as ellipse and rectange
oldscreen = None
# Location of the canvas surface
canvasLoc = config["canvasLocation"]
# Stores the subsurface of the canvas that is selected for crop
cropSurface = None
# Whether a tool is currently engaged
tooling = False
# Rectangles whose colours will not be updated by the loop
doNotUpdateOnReDraw = ["colourDisplayRect", "backDisplayRect", "volIndicatorRect"]
# List of surfaces to undo and redo
undoList = []
redoList = []

# Whether the event loop needs more assistance
furthurProcessing = 0

# Whether the tool modified the canvas on the iteration
toolStatus = False

# Stores whether there has been a change since the last save
needToSave = False
# The size of the canvas
canvasSize = (700,  500)

# Stores settings for the music player
musicRegistry = {"playing": -1, "queue": ["music/01.ogg","music/02.ogg", "music/Kalimba.mp3"], "loop": False, "paused": False, "volume": 1.0}

# Stores info for the polygon tool
polygonRegistry = {}

# Stores loaded images
imageRegistry = {}

# Defines the canvas surface and fills it with white
canvasSurface = Surface(canvasSize)
canvasSurface.fill(WHITE)

# Adds a blank surface to the undo list
undoList.append(canvasSurface.copy())

# Store the music to be played
musicList = []

# Whether to fills shapes
shapeFilled = False

# If the polygon tool is currently being ued
onPolygon = False

# If a point was drawn and the mouse has not been released yet
pointDrawLock = False

# If the help menu is open
helpOpen = False

# Rate limits tools such as air brush
toolDelay = ptime.time()

# Initialize Tkinter and hide it
root = Tk()
root.withdraw()

# Initialize fonts
font.init()
infoFont = font.SysFont("Segoe UI", 20)
tipFont = font.SysFont("Segoe UI", 16)

# Initialize the rectangles and store them in a dictionary

rectRegistry = {"colourDisplayRect": [Rect(config["rects"]["colourDisplayRect"][0]), eval(config["rects"]["colourDisplayRect"][1]), config["rects"]["colourDisplayRect"][2]],
                "backColourDisplayRect": [Rect(config["rects"]["backColourDisplayRect"][0]), eval(config["rects"]["backColourDisplayRect"][1]), config["rects"]["backColourDisplayRect"][2]],
                "pencilRect": [Rect(config["rects"]["pencilRect"][0]), eval(config["rects"]["pencilRect"][1]), config["rects"]["pencilRect"][2]],
                "eraserRect": [Rect(config["rects"]["eraserRect"][0]), eval(config["rects"]["eraserRect"][1]), config["rects"]["eraserRect"][2]],
                "shapeRectRect": [Rect(config["rects"]["shapeRectRect"][0]), eval(config["rects"]["shapeRectRect"][1]), config["rects"]["shapeRectRect"][2]],
                "shapeEllipseRect": [Rect(config["rects"]["shapeEllipseRect"][0]), eval(config["rects"]["shapeEllipseRect"][1]), config["rects"]["shapeEllipseRect"][2]],
                "lineRect": [Rect(config["rects"]["lineRect"][0]), eval(config["rects"]["lineRect"][1]), config["rects"]["lineRect"][2]],
                "airbrushRect": [Rect(config["rects"]["airbrushRect"][0]), eval(config["rects"]["airbrushRect"][1]), config["rects"]["airbrushRect"][2]],
                "bucketRect": [Rect(config["rects"]["bucketRect"][0]), eval(config["rects"]["bucketRect"][1]), config["rects"]["bucketRect"][2]],
                "cropRect": [Rect(config["rects"]["cropRect"][0]), eval(config["rects"]["cropRect"][1]), config["rects"]["cropRect"][2]],
                "brushRect": [Rect(config["rects"]["brushRect"][0]), eval(config["rects"]["brushRect"][1]), config["rects"]["brushRect"][2]],
                "polygonRect": [Rect(config["rects"]["polygonRect"][0]), eval(config["rects"]["polygonRect"][1]), config["rects"]["polygonRect"][2]],
                "playPauseRect": [Rect(config["rects"]["playPauseRect"][0]), eval(config["rects"]["playPauseRect"][1]), config["rects"]["playPauseRect"][2]],
                "stopRect": [Rect(config["rects"]["stopRect"][0]), eval(config["rects"]["stopRect"][1]), config["rects"]["stopRect"][2]],
                "prevRect": [Rect(config["rects"]["prevRect"][0]), eval(config["rects"]["prevRect"][1]), config["rects"]["prevRect"][2]],
                "nextRect": [Rect(config["rects"]["nextRect"][0]), eval(config["rects"]["nextRect"][1]), config["rects"]["nextRect"][2]],
                "loopRect": [Rect(config["rects"]["loopRect"][0]), eval(config["rects"]["loopRect"][1]), config["rects"]["loopRect"][2]],
                "helpRect": [Rect(config["rects"]["helpRect"][0]), eval(config["rects"]["helpRect"][1]), config["rects"]["helpRect"][2]],
                "toggleFilledRect": [Rect(config["rects"]["toggleFilledRect"][0]), eval(config["rects"]["toggleFilledRect"][1]), config["rects"]["toggleFilledRect"][2]],
                "volIndicatorRect": [Rect(config["rects"]["volIndicatorRect"][0]), eval(config["rects"]["volIndicatorRect"][1]), config["rects"]["volIndicatorRect"][2]],
                "stampOneRect": [Rect(config["rects"]["stampOneRect"][0]), eval(config["rects"]["stampOneRect"][1]), config["rects"]["stampOneRect"][2]],
                "stampTwoRect": [Rect(config["rects"]["stampTwoRect"][0]), eval(config["rects"]["stampTwoRect"][1]), config["rects"]["stampTwoRect"][2]],
                "stampThreeRect": [Rect(config["rects"]["stampThreeRect"][0]), eval(config["rects"]["stampThreeRect"][1]), config["rects"]["stampThreeRect"][2]],
                "stampFourRect": [Rect(config["rects"]["stampFourRect"][0]), eval(config["rects"]["stampFourRect"][1]), config["rects"]["stampFourRect"][2]],
                "stampFiveRect": [Rect(config["rects"]["stampFiveRect"][0]), eval(config["rects"]["stampFiveRect"][1]), config["rects"]["stampFiveRect"][2]],
                "stampSixRect": [Rect(config["rects"]["stampSixRect"][0]), eval(config["rects"]["stampSixRect"][1]), config["rects"]["stampSixRect"][2]]}

# Define the palette collide point rectangle (will not be drawn)
palRect = Rect(config["paletteLocation"][0], config["paletteLocation"][1], config["paletteSize"][0], config["paletteSize"][1])
# Define the canvas collide point rectangle (will not be drawn)
canvasRect = Rect(config["canvasLocation"][0], config["canvasLocation"][1], config["canvasSize"][0], config["canvasSize"][1])
# Define the rectangle to clear the canvas
clearRect = Rect(config["rects"]["clearRect"][0])

# Volume indicator collide rect
volChooserRect = Rect(config["rects"]["volChooserRect"][0])

# Define the open and save buttons
openRect = Rect(config["rects"]["openRect"][0])
saveRect = Rect(config["rects"]["saveRect"][0])

# Blit the canvas on to the screen
screen.blit(canvasSurface, canvasLoc)

# Load ALL images before the while loop
palPic = image.load(config["paletteImage"])
screen.blit(palPic, config["paletteLocation"])

for key, rectArray in rectRegistry.items():
        if key in config["rects"] and len(config["rects"][key]) > 3:
            if (key == "loopRect" and musicRegistry["loop"]) or (key == "toggleFilledRect" and shapeFilled):
                icon = image.load(config["rects"][key][4])
            else:
                icon = image.load(config["rects"][key][3])

            icon = transform.smoothscale(icon, (rectArray[0][2]-rectArray[2]*2+1, rectArray[0][3]-rectArray[2]*2+1))
            imageRegistry[key] = icon
icon = image.load(config["rects"]["clearRect"][3])
icon = transform.smoothscale(icon, (clearRect.width, clearRect.height))
imageRegistry["clearRect"] = icon

icon = image.load(config["rects"]["openRect"][3])
icon = transform.smoothscale(icon, (openRect.width, openRect.height))
imageRegistry["openRect"] = icon

icon = image.load(config["rects"]["saveRect"][3])
icon = transform.smoothscale(icon, (saveRect.width, saveRect.height))
imageRegistry["saveRect"] = icon

# Load the stamps
for i in range(1, 7):
    exec("stamp{0} = image.load(config[\"stamp{0}Loc\"])".format(i))

# Initialize the mixer and give it an event type to trigger on music finish
mixer.init()
mixer.music.set_endevent(SONG_END)

smartLog("%s initialized successfully in %0.4fs"%(title, ptime.time()-startTime), 3)
smartLog("On commit %s"%version, 3)

# Converts co-ordinates from global scope to canvas scope
def convertToCanvas(pos):
    return (pos[0] - canvasLoc[0], pos[1] - canvasLoc[1])


# Converts co-ordinates from canvas scope to global scope
def convertToGlobal(pos):
    return (pos[0] + canvasLoc[0], pos[1] + canvasLoc[1])


# Placeholder function for no tool (startup)
def nothing(mpos, lregistry):
    return


# Pencil tool
# Draw many lines so that we get a continuous line, like a pencil
def pencil(mpos, lregistry):
    # Draw a line and limit it to 4 pixels wide
    draw.line(canvasSurface, lregistry["toolColour"], lastTickLocation, mpos,
              lregistry["toolThickness"] if lregistry["toolThickness"] <= 4 else 4)
    return True


# Open a file and load it onto the canvas
def openFile(lregistry):
    global needToSave, undoLoc, undoList

    # Check if the user has made any modifications since the last save
    if needToSave:
        q = messagebox.askokcancel(title, "You have unsaved changes that will be overwritten. Continue?")
        if not q:
            # If they say cancel, cancel
            return

    # Ask for the file to open
    root.filename = filedialog.askopenfilename(initialdir="%DEFAULTUSERPROFILE%.", title="Select file",
                                               filetypes=(("JPEG Files", "*.jpg *.jpeg"), ("Bitmap Files", "*.bmp"),
                                                          ("PNG Files", "*.png"), ("All Files", "*.*")))
    # If the filename is not blank (canceled) and it still exists, open it
    if root.filename != "" and os.path.isfile(root.filename):
        openedFile = image.load(root.filename)

        # Fit the image to the canvas if it is too big
        if openedFile.get_width() > canvasSurface.get_width() or openedFile.get_height() > canvasSurface.get_height():
            openedFile = transform.smoothscale(openedFile, canvasSize)

        # Clear the undo list
        del undoList[:]

        # Fill the background with the background colour and blit the image
        canvasSurface.fill(lregistry["backgroundColour"])
        undoList.append(canvasSurface.copy())
        canvasSurface.blit(openedFile, (0,0))
        undoList.append(canvasSurface.copy())
        screen.blit(canvasSurface, canvasLoc)

        needToSave = False


# Saves the canvas to a file
def saveFile():
    global needToSave
    root.filename = filedialog.asksaveasfilename(initialdir="%DEFAULTUSERPROFILE%.", title="Select file",
                                               filetypes=(("JPEG Files", "*.jpg *.jpeg"), ("Bitmap Files", "*.bmp"),
                                                          ("PNG Files", "*.png"), ("All Files", "*.*")), defaultextension="*.*")
    # Check if the user canceled the operation
    if root.filename != "":
        image.save(canvasSurface, root.filename)
        messagebox.showinfo(title, "Your file has been saved.")
        needToSave = False


# Rectangle shape tool
def dShapeRect(mpos, lregistry):
    global shapeFilled
    # Restore old version of screen so that we don't get overlap
    canvasSurface.blit(oldscreen, (0, 0))

    # Very sketchy way of changing the rectangle depending on a negative width and/or height

    # Positive width and height
    rectString = "Rect(dragStart[0]-i, dragStart[1]-i, mpos[0] - (dragStart[0] - i*2), mpos[1] - (dragStart[1] - i*2))"

    # Negative height
    if dragStart[0] < mpos[0] and dragStart[1] > mpos[1]:
        rectString = "Rect(dragStart[0]+i, dragStart[1]-i, mpos[0] - (dragStart[0] + i*2)," \
                     " mpos[1] - (dragStart[1] - i*2))"

    # Negative width
    elif dragStart[0] > mpos[0] and dragStart[1] < mpos[1]:
        rectString = "Rect(dragStart[0]-i, dragStart[1]+i, mpos[0] - (dragStart[0] - i*2), " \
                     "mpos[1] - (dragStart[1] + i*2))"

    # Negative width and height
    elif dragStart[0] < mpos[0] and dragStart[1] < mpos[1]:
        rectString = "Rect(dragStart[0]+i, dragStart[1]+i, mpos[0] - (dragStart[0] + i*2), " \
                     "mpos[1] - (dragStart[1] + i*2))"

    # Draw a smooth rectangle (only for unfilled), unless the thickness is greater than the size of the rectangle
    # In that case, always draw a filled rectangle with the current dragged size
    if lregistry["toolThickness"] * 2 < min(abs(mpos[0] - dragStart[0]), abs(mpos[1] - dragStart[1])) and not shapeFilled:
        for i in range(lregistry["toolThickness"]):
            tempRect = eval(rectString)
            tempRect.normalize()
            draw.rect(canvasSurface, lregistry["toolColour"], tempRect, 1)
    else:
        draw.rect(canvasSurface, lregistry["toolColour"], (dragStart[0], dragStart[1], mpos[0]-dragStart[0],
                                                    mpos[1]-dragStart[1]), 0)
    return True

# Crop tool
def crop(mpos, lregistry):
    global cropSurface
    # Restore the old screen as we are drawing the guide rectangle
    if canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        canvasSurface.blit(oldscreen, (0, 0))
        tempRect = Rect(dragStart[0], dragStart[1], mpos[0]-dragStart[0], mpos[1]-dragStart[1])
        tempRect.normalize()
        # Make sure the width is reasonable before cropping
        if tempRect.height > 2 and tempRect.width > 2:
            # Take a screen capture and then draw the guide rectangle
            cropSurface = oldscreen.subsurface(tempRect)
            draw.rect(canvasSurface, RED, tempRect, 2)
            return True
    return False


# Ellipse tool
def dShapeEllipse(mpos, lregistry):
    global shapeFilled, dragStart
    # Restore old version of screen so that we don't get overlap
    canvasSurface.blit(oldscreen, (0, 0))

    # Define a key colour for the temporary surface
    keyColour = (255, 255, 253)

    # Define a rectangle for the ellipse
    tempRect = Rect(dragStart[0], dragStart[1], mpos[0] - dragStart[0],
                    mpos[1] - dragStart[1])
    tempRect.normalize()
    # Grab the x, y, width, and height of the normalized rectangle
    rx, ry, rw, rh = tempRect
    # Only create an unfilled ellipse if the dimensions are greater than the width and the shape is not to be filled
    if lregistry["toolThickness"] * 2 < min(abs(mpos[0] - dragStart[0]), abs(mpos[1] - dragStart[1])) and not shapeFilled:
        # Create a temp surface with the width and height of the rectangle
        tempSurface = Surface((rw, rh))
        # Set the key colour and fill the surface so that it is transparent
        tempSurface.set_colorkey(keyColour)
        tempSurface.fill(keyColour)

        # Draw an ellipse and then a smaller one filled with the key colour to create the effect of an unfilled ellipse
        draw.ellipse(tempSurface, lregistry["toolColour"], (0, 0, rw, rh))
        draw.ellipse(tempSurface, keyColour,
                     (lregistry["toolThickness"], lregistry["toolThickness"], rw - lregistry["toolThickness"]*2,
                      rh - lregistry["toolThickness"]*2), 0)
        canvasSurface.blit(tempSurface, (rx, ry))

    else:
        draw.ellipse(canvasSurface, lregistry["toolColour"], tempRect, 0)
    return True


# Eraser tool
def eraser(mpos, lregistry):
    # Interpolate circles so that it is smooth
    dx = mpos[0] - lastTickLocation[0]
    dy = mpos[1] - lastTickLocation[1]
    dist = int((dx**2+dy**2)**0.5)
    for i in range(1, dist+1):
        dotX = int(lastTickLocation[0] + i*dx/dist)
        dotY = int(lastTickLocation[1] + i*dy/dist)
        draw.circle(canvasSurface, lregistry["backgroundColour"], (dotX, dotY), lregistry["toolThickness"])
    # Draw an initial circle so that you don't need to move to draw a circle
    draw.circle(canvasSurface, lregistry["backgroundColour"], mpos, lregistry["toolThickness"])
    return True


# Function that draws lines
def line(mpos, lregistry):
    # Restore the copy of the screen before the tool was clicked so that we don't get overlapping lines
    canvasSurface.blit(oldscreen, (0, 0))

    # Draw a line from the start of the click to the current position
    draw.line(canvasSurface, lregistry["toolColour"], dragStart, mpos, lregistry["toolThickness"] if lregistry["toolThickness"] < 6 else 5)
    return True


def airbrush(mpos, lregistry):
    global toolDelay
    # Rate limiting so that the circle is not automatically completely filled
    if ptime.time() - toolDelay > 0.00100003:
        toolDelay = ptime.time()
        # Randomly choose the number of points to draw
        numPoints = randint(0, 10)
        pointList = []
        # Fill the points list with random points
        while len(pointList) < numPoints:
            x = randint(mpos[0]-lregistry["toolThickness"] // 2, mpos[0]+lregistry["toolThickness"] // 2)
            y = randint(mpos[1] - lregistry["toolThickness"] // 2, mpos[1] + lregistry["toolThickness"] // 2)
            # Check if the point is within a circle with radius of half the tool thickness
            if ((x-mpos[0])**2 + (y-mpos[1])**2)**0.5 < lregistry["toolThickness"]/2:
                pointList.append((x, y))
        # Draw the selected points as aa circles (looks better)
        for point in pointList:
            gfxdraw.circle(canvasSurface, point[0], point[1], 1, lregistry["toolColour"])
    return True


# Paint bucket tool
def bucket(mpos, lregistry):
    global toolDelay, pointDrawLock

    # Rate limiting so that the program doesn't make many operations per click
    if not pointDrawLock:
        # Force the user to mouse button up
        pointDrawLock = True
        # Convert the surface into a pixel array (MUCH better performance)
        pxArray = PixelArray(canvasSurface)
        # Grab the colour at the position of the mouse
        colourAtMouse = pxArray[mpos[0], mpos[1]]

        # Create a queue and a set of points already travelled to so that we don't loop infinitely
        queue = set()
        filled = set()

        # Add the current mouse position
        queue.add((mpos[0], mpos[1]))

        # Gets a mapped RGB value to be filled
        fillColour = screen.map_rgb(lregistry["toolColour"])
        smartLog("QUEUE: "+str(queue), 3)
        while queue:
            # Remove the current pos from the queue
            currPos = queue.pop()
            # Add it to the filled set
            filled.add(currPos)
            # Change the colour of the point to the colour desired
            pxArray[currPos[0], currPos[1]] = fillColour

            # Add adjacent points as long as they are the same colour as the point at the mouse and they are valid
            if currPos[0] - 1 >= 0 and pxArray[currPos[0] - 1, currPos[1]] == colourAtMouse and (currPos[0]-1, currPos[1]) not in filled:
                queue.add((currPos[0] - 1, currPos[1]))
            if currPos[0] + 1 < canvasSurface.get_width() and pxArray[currPos[0] + 1, currPos[1]] == colourAtMouse and (currPos[0]+1, currPos[1]) not in filled:
                queue.add((currPos[0] + 1, currPos[1]))
            if currPos[1] - 1 >= 0 and pxArray[currPos[0], currPos[1]-1] == colourAtMouse and (currPos[0], currPos[1]-1) not in filled:
                queue.add((currPos[0], currPos[1] - 1))
            if currPos[1] + 1 < canvasSurface.get_height() and pxArray[currPos[0], currPos[1]+1] == colourAtMouse and (currPos[0], currPos[1]+1) not in filled:
                queue.add((currPos[0], currPos[1] + 1))
        # Delete the pixel array (memory management)
        del pxArray

        # Update the tool delay
        toolDelay = ptime.time()
    return True


# Brush tool
def brush(mpos, lregistry):
    # Interpolate circles so that it is smooth
    dx = mpos[0] - lastTickLocation[0]
    dy = mpos[1] - lastTickLocation[1]
    dist = int((dx ** 2 + dy ** 2) ** 0.5)
    for i in range(1, dist + 1):
        dotX = int(lastTickLocation[0] + i * dx / dist)
        dotY = int(lastTickLocation[1] + i * dy / dist)
        draw.circle(canvasSurface, lregistry["toolColour"], (dotX, dotY), lregistry["toolThickness"])
    # Draw an initial circle so that you don't need to move to draw a circle
    draw.circle(canvasSurface, lregistry["toolColour"], mpos, lregistry["toolThickness"])
    return True

def stamp(id, mpos, lregistry):
    # Restore old version of screen so that we don't get overlap
    canvasSurface.blit(oldscreen, (0, 0))

    # Blit the correct stamp
    exec("canvasSurface.blit(stamp{0}, (mpos[0]-stamp{0}.get_width()//2, mpos[1]-stamp{0}.get_height()//2))".format(id))
    return True

def eyeDropper(mpos, lregistry):
    return canvasSurface.get_at(mpos)

def polygon(mpos, lregistry):
    global polygonRegistry, onPolygon, toolDelay, pointDrawLock, undoList
    # If the tool is currently not engaged, set it up for first use
    if not onPolygon:
        # Get the start point, so that we can check when the user is finished
        polygonRegistry["startPoint"] = mpos
        # Store the last point that the user clicked so that we can make the outline
        polygonRegistry["lastPoint"] = mpos
        # Store the points of the polygon
        polygonRegistry["points"] = []
        # Make a copy of the old surface so that the guides are not saved
        polygonRegistry["oldSurface"] = canvasSurface.copy()

    # If the mouse overlaps the circle area of the starting point, the cursor has been rleased since the last point, and the tool is activated, it means the polygon is finished
    if ((polygonRegistry["startPoint"][0]-mpos[0])**2 + (polygonRegistry["startPoint"][1]-mpos[1])**2)**0.5 < 10 and len(polygonRegistry["points"]) > 2 and onPolygon and not pointDrawLock:
        # Mark tool as disabled
        onPolygon = False
        smartLog("Polygon finished", 3)
        # Blit the original surface
        canvasSurface.blit(polygonRegistry["oldSurface"], (0,0))
        # Draw the polygon
        if shapeFilled:
            draw.polygon(canvasSurface, lregistry["toolColour"], polygonRegistry["points"])
        else:
            for i in range(len(polygonRegistry["points"])):
                try:
                    draw.line(canvasSurface, lregistry["toolColour"], polygonRegistry["points"][i], polygonRegistry["points"][i+1], lregistry["toolThickness"] if lregistry["toolThickness"] < 6 else 5)
                except IndexError:
                    draw.line(canvasSurface, lregistry["toolColour"], polygonRegistry["points"][i], polygonRegistry["points"][0], lregistry["toolThickness"] if lregistry["toolThickness"] < 6 else 5)
        # Add to the undo list
        undoList.append(canvasSurface.copy())
        # Clear the registry
        polygonRegistry = {}
        # Do not inform the caller that the surface has been modified, or else there will be a duplicate undo
        return False
    else:
        # Check that the mouse has been released since the lasft point
        if not pointDrawLock:
            print("draw")
            # Mark the tool as activated
            onPolygon = True
            # Draw a side of the polygon
            draw.line(canvasSurface, BLACK, polygonRegistry["lastPoint"], mpos, 3)
            # Draw a guide circle
            draw.circle(canvasSurface, RED, mpos, 10)
            # Draw another guide circle to cover the line
            draw.circle(canvasSurface, RED, polygonRegistry["lastPoint"], 10)
            polygonRegistry["points"].append(mpos)
            polygonRegistry["lastPoint"] = mpos
            # Only execute after the mouse is released
            pointDrawLock = True
        # Since we are drwaing guides, do not inform the caller that the surface has been modified
        return False


# Initialize the registry
registry = {"toolName": "nothing", "toolFunc": nothing, "toolArgs": {"updateOldPerTick": False},
            "toolColour": (255, 255, 255), "toolThickness": 2, "backgroundColour": (255, 255, 255)}

while running:
    mb = mouse.get_pressed()
    mp = mouse.get_pos()
    for evt in event.get():
        if evt.type == QUIT:
            running = False
        if evt.type == KEYDOWN:
            if evt.key == K_f and dev:
                shapeFilled = not shapeFilled
            if evt.key == K_c and dev:
                smartLog("COLOUR: "+str(screen.get_at(mp)) + " "+ str(canvasSurface.get_at(convertToCanvas(mp))), 3)
            if evt.key == K_ESCAPE:
                # Exit help or cancel the polygon drawing process
                if helpOpen:
                    if not helpImageRect.collidepoint(mp[0], mp[1]):
                        helpOpen = False
                elif onPolygon:
                    onPolygon = False
                    canvasSurface.blit(polygonRegistry["oldSurface"], (0,0))
                    polygonRegistry = {}
            if evt.key == K_u:
                if len(undoList) > 1:
                    redoList.append(undoList.pop())
                    canvasSurface.blit(undoList[len(undoList)-1], (0, 0))
                    screen.blit(canvasSurface, canvasLoc)
            if evt.key == K_r:
                if len(redoList) > 0:
                    undoList.append(redoList.pop())
                    canvasSurface.blit(undoList[len(undoList)-1], (0, 0))
                    screen.blit(canvasSurface, canvasLoc)
        if evt.type == MOUSEBUTTONDOWN:
            if not helpOpen:
                tooling = True
                oldscreen = canvasSurface.copy()
                dragStart = mouse.get_pos()
                if evt.button == 4:
                    registry["toolThickness"] += 1 if registry["toolThickness"] < 100 else 0
                elif evt.button == 5:
                    registry["toolThickness"] -= 1 if registry["toolThickness"] > 1 else 0
        if evt.type == MOUSEBUTTONUP:
            tooling = False
            pointDrawLock = False
            smartLog("TOOL STATUS: %s"%toolStatus, 3)
            smartLog("a"+str(ptime.time()), 3)
            furthurProcessing = 2
        if evt.type == SONG_END:
            if musicRegistry["loop"]:
                mixer.music.stop()
                mixer.music.load(musicRegistry["queue"][musicRegistry["playing"]])
                mixer.music.set_volume(musicRegistry["volume"])
                mixer.music.play()
            else:
                musicRegistry["playing"] = musicRegistry["playing"] + 1 if musicRegistry["playing"] < len(musicRegistry["queue"])-1 else 0
                mixer.music.stop()
                mixer.music.load(musicRegistry["queue"][musicRegistry["playing"]])
                mixer.music.set_volume(musicRegistry["volume"])
                mixer.music.play()

    # For some reason, event loop sometimes is out of sync, so we will make sure that it has processed everything
    if furthurProcessing:
        smartLog("Tool status %s"%toolStatus, 3)
        if toolStatus:
            if (((canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]) or canvasRect.collidepoint(convertToGlobal(mp)[0], convertToGlobal(mp)[1])) and registry["toolName"] != "nothing") or
                (clearRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]))) and toolStatus:
                needToSave = True
                undoList.append(canvasSurface.copy())
                smartLog("Processed.", 3)
                smartLog("LEN UNDOLIST %d"%len(undoList), 3)
                furthurProcessing = 0
        toolStatus = False


    # Sync the colour showing rect's colour in the rectRegistry to the tool colour
    rectRegistry["colourDisplayRect"][1] = registry["toolColour"]
    rectRegistry["backColourDisplayRect"][1] = registry["backgroundColour"]

    # Draw images
    screen.blit(backgroundImage, (0,0))
    screen.blit(palPic, config["paletteLocation"])
    screen.blit(canvasSurface, canvasLoc)

    draw.rect(screen, (175, 175, 175), (0, 0, width, 60))
    volChooserImage = image.load(config["rects"]["volChooserRect"][3])
    volChooserImage = transform.smoothscale(volChooserImage, (volChooserRect.width, volChooserRect.height))
    screen.blit(volChooserImage, volChooserRect.topleft)
    musicFileNameText = infoFont.render("Playing - " + musicRegistry["queue"][musicRegistry["playing"]][musicRegistry["queue"][musicRegistry["playing"]].rfind("/")+1:musicRegistry["queue"][musicRegistry["playing"]].rfind(".")] if musicRegistry["playing"] != -1 and not musicRegistry["paused"] else "PAUSED" if musicRegistry["paused"] else "Nothing is playing", True, WHITE)
    screen.blit(musicFileNameText, (rectRegistry["loopRect"][0].right+30, rectRegistry["loopRect"][0][1]+5))

    toolDescText = infoFont.render("{0}: {1}".format(config["descriptions"][registry["toolName"]][0], config["descriptions"][registry["toolName"]][1]), True, WHITE)
    screen.blit(toolDescText, (20, height-45))

    # Draw rects
    for key, rectArray in rectRegistry.items():
        if (len(config["rects"][key]) < 5 or config["rects"][key][4]) and key != "loopRect":
            draw.rect(screen, rectArray[1], rectArray[0], rectArray[2])
        if key in imageRegistry:
            screen.blit(imageRegistry[key], (rectArray[0][0]+rectArray[2], rectArray[0][1]+rectArray[2]))
            
    #draw.rect(screen, WHITE, clearRect)
    screen.blit(imageRegistry["clearRect"], clearRect.topleft)

    #draw.rect(screen, WHITE, openRect)
    screen.blit(imageRegistry["openRect"], openRect.topleft)

    #draw.rect(screen, WHITE, saveRect)
    screen.blit(imageRegistry["saveRect"], saveRect.topleft)


    # Draw text
    # Mouse location
    # Draw 0, 0 if the mouse is not over the canvas, otherwise convert mouse pos in global context to canvas context
    #txtMouseLoc = eval("infoFont.render(\"X: {0}  Y: {1}\".format"+str(convertToCanvas(mp) if canvasRect.collidepoint(mp[0], mp[1]) else (0,0))+", True, WHITE)")

    txtMouseLoc = infoFont.render("X: {0}  Y:{1}".format(mp[0], mp[1]), True, WHITE)
    screen.blit(txtMouseLoc, (20, height-70))

    txtThickness = infoFont.render("Thickness: {0}".format(registry["toolThickness"]), True, WHITE)
    screen.blit(txtThickness, (20, height-95))
    # Check if the cursor was drawing and did not release
    # Check if the cursor has clicked on a tool button
    if mb[0] and not tooling and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]) and not onPolygon:
        # Set the toolFunc in the registry to be the tool that was chosen, and whether the starting pos will be
        # updated per tick and update the colour of the rectangle to show selected
        if rectRegistry["pencilRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = pencil
            registry["toolName"] = "pencil"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["pencilRect"][1] = RED
        elif rectRegistry["eraserRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = eraser
            registry["toolName"] = "eraser"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["eraserRect"][1] = RED
        elif rectRegistry["shapeRectRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeRect
            registry["toolName"] = "shaperect"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeRectRect"][1] = RED
        elif rectRegistry["shapeEllipseRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeEllipse
            registry["toolName"] = "shapeellipse"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeEllipseRect"][1] = RED
        elif rectRegistry["lineRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = line
            registry["toolName"] = "line"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["lineRect"][1] = RED
        elif rectRegistry["airbrushRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = airbrush
            registry["toolName"] = "airbrush"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["airbrushRect"][1] = RED
        elif rectRegistry["bucketRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = bucket
            registry["toolName"] = "bucket"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["bucketRect"][1] = RED
        elif rectRegistry["cropRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = crop
            registry["toolName"] = "crop"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["cropRect"][1] = RED
        elif rectRegistry["brushRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = brush
            registry["toolName"] = "brush"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["brushRect"][1] = RED
        elif rectRegistry["polygonRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = polygon
            registry["toolName"] = "polygon"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["polygonRect"][1] = RED
        elif rectRegistry["stampOneRect"][0].collidepoint(mp[0], mp[1]):
            # For the stamps, use a lambda to automatically pass the stamp number so that we don't need multiple stamp functions
            registry["toolFunc"] = lambda pos, qregistry: stamp(1, pos, qregistry)
            registry["toolName"] = "stampone"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampOneRect"][1] = RED
        elif rectRegistry["stampTwoRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = lambda pos, qregistry: stamp(2, pos, qregistry)
            registry["toolName"] = "stamptwo"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampTwoRect"][1] = RED
        elif rectRegistry["stampThreeRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = lambda pos, qregistry: stamp(3, pos, qregistry)
            registry["toolName"] = "stampthree"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampThreeRect"][1] = RED
        elif rectRegistry["stampFourRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = lambda pos, qregistry: stamp(4, pos, qregistry)
            registry["toolName"] = "stampfour"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampFourRect"][1] = RED
        elif rectRegistry["stampFiveRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = lambda pos, qregistry: stamp(5, pos, qregistry)
            registry["toolName"] = "stampfive"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampFiveRect"][1] = RED
        elif rectRegistry["stampSixRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = lambda pos, qregistry: stamp(6, pos, qregistry)
            registry["toolName"] = "stampsix"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["stampSixRect"][1] = RED
        elif clearRect.collidepoint(mp[0], mp[1]):
            canvasSurface.fill(registry["backgroundColour"])
            needToSave = True
            undoList.append(canvasSurface.copy())
            screen.blit(canvasSurface, canvasLoc)
        elif openRect.collidepoint(mp[0], mp[1]):
            openFile(registry)
        elif saveRect.collidepoint(mp[0], mp[1]):
            saveFile()
        elif rectRegistry["playPauseRect"][0].collidepoint(mp[0], mp[1]):
            if musicRegistry["playing"] == -1:
                musicRegistry["playing"] = 0
                mixer.music.load(musicRegistry["queue"][musicRegistry["playing"]])
                mixer.music.play()
            else:
                smartLog("Mixer busy: %s"%mixer.music.get_busy(), 3)
                if musicRegistry["paused"]:
                    mixer.music.unpause()
                    musicRegistry["paused"] = False
                else:
                    mixer.music.pause()
                    musicRegistry["paused"] = True
            smartLog("playpause", 3)
        elif rectRegistry["stopRect"][0].collidepoint(mp[0], mp[1]):
            musicRegistry["playing"] = -1
            musicRegistry["paused"] = False
            mixer.music.stop()
        elif rectRegistry["prevRect"][0].collidepoint(mp[0], mp[1]):
            musicRegistry["playing"] = musicRegistry["playing"] - 1 if musicRegistry["playing"] > 0 else len(musicRegistry["queue"])-1
            mixer.music.stop()
            mixer.music.load(musicRegistry["queue"][musicRegistry["playing"]])
            mixer.music.set_volume(musicRegistry["volume"])
            mixer.music.play()
        elif rectRegistry["nextRect"][0].collidepoint(mp[0], mp[1]):
            musicRegistry["playing"] = musicRegistry["playing"] + 1 if musicRegistry["playing"] < len(musicRegistry["queue"])-1 else 0
            mixer.music.stop()
            mixer.music.load(musicRegistry["queue"][musicRegistry["playing"]])
            mixer.music.set_volume(musicRegistry["volume"])
            mixer.music.play()
        elif rectRegistry["loopRect"][0].collidepoint(mp[0], mp[1]):
            musicRegistry["loop"] = not musicRegistry["loop"]
            if musicRegistry["loop"]:
                icon = image.load(config["rects"]["loopRect"][4])
            else:
                icon = image.load(config["rects"]["loopRect"][3])

            icon = transform.smoothscale(icon, (rectRegistry["loopRect"][0][2]-rectRegistry["loopRect"][2]*2, rectRegistry["loopRect"][0][3]-rectRegistry["loopRect"][2]*2))
            imageRegistry["loopRect"] = icon
        elif rectRegistry["toggleFilledRect"][0].collidepoint(mp[0], mp[1]):
            shapeFilled = not shapeFilled
            if shapeFilled:
                icon = image.load(config["rects"]["toggleFilledRect"][4])
            else:
                icon = image.load(config["rects"]["toggleFilledRect"][3])

            icon = transform.smoothscale(icon, (rectRegistry["toggleFilledRect"][0][2]-rectRegistry["toggleFilledRect"][2]*2, rectRegistry["toggleFilledRect"][0][3]-rectRegistry["toggleFilledRect"][2]*2))
            imageRegistry["toggleFilledRect"] = icon
        elif rectRegistry["helpRect"][0].collidepoint(mp[0], mp[1]):
            helpOpen = True

    if volChooserRect.collidepoint(mp[0], mp[1]) and mb[0] and not helpOpen:
        leftMost = config["rects"]["volIndicatorRect"][0][0] - 150
        rectRegistry["volIndicatorRect"][0][0] = mp[0] if leftMost-1 < mp[0] < config["rects"]["volIndicatorRect"][0][0]+1 else config["rects"]["volIndicatorRect"][0][0] if mp[0] > config["rects"]["volIndicatorRect"][0][0] else leftMost
        musicRegistry["volume"] = (rectRegistry["volIndicatorRect"][0][0] - leftMost)/150
        mixer.music.set_volume(musicRegistry["volume"])

    if not helpOpen:
        for key, checkRect in rectRegistry.items():
            if key not in ["colourDisplayRect", "backColourDisplayRect", "volIndicatorRect", "helpRect", "playPauseRect","stopRect","prevRect","nextRect", "loopRect"]:
                if checkRect[0].collidepoint(mp[0], mp[1]):
                    draw.rect(screen, RED, checkRect[0], checkRect[2])

    # Check if the mouse is over the colour wheel and a tool is currently not being used
    if mb[0] and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]) and not helpOpen:
        if palRect.collidepoint(mp[0], mp[1])  and ((mp[0]-palRect.centerx)**2 + (mp[1]-palRect.centery)**2)**0.5 < 101 and not onPolygon:
            # Get the colour and the point
            registry["toolColour"] = screen.get_at((mp[0], mp[1]))

    # Check if the mouse is over the colour wheel and a tool is currently not being used
    if mb[2] and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]) and not helpOpen:
        if palRect.collidepoint(mp[0], mp[1]) and (
                (mp[0] - palRect.centerx) ** 2 + (mp[1] - palRect.centery) ** 2) ** 0.5 < 101 and not onPolygon:
            # Get the colour and the point
            registry["backgroundColour"] = screen.get_at((mp[0], mp[1]))

    # Check if the user clicked on left-click
    if mb[0] and not helpOpen:
        # Execute the tool function, checking if the drag must start on the canvas
        if canvasRect.collidepoint(mp[0], mp[1]):
            toolStatus = registry["toolFunc"](convertToCanvas(mp), registry)
            smartLog("JUST FINISHED TOOL STATUS %s"%toolStatus, 3)
            smartLog("b"+str(ptime.time()), 3)
            screen.blit(canvasSurface, canvasLoc)
        toolDelay = ptime.time()

        # If the old position needs to be updated per tick, even when the tool is engaged (shadow), update it
        if registry["toolArgs"]["updateOldPerTick"]:
            lastTickLocation = convertToCanvas(mp)
    elif not helpOpen:
        # If the mouse is currently not being clicked, update the dragStart variable to keep track of where the cursor
        # was. So that we can get a start point for shape tools
        dragStart = convertToCanvas(mp)
        lastTickLocation = convertToCanvas(mp)

    # Tooltips
    if not helpOpen:
        rectRegistryAndStatic = rectRegistry.copy()
        rectRegistryAndStatic.update({"clearRect": [clearRect], "saveRect": [saveRect], "openRect": [openRect], "volChooserRect": [volChooserRect]})
        for rectName, rectData in rectRegistryAndStatic.items():
            if rectData[0].collidepoint(mp[0], mp[1]):
                if rectName in config["tooltips"]:
                    tipText = tipFont.render(eval(config["tooltips"][rectName]), True, WHITE)
                    tipRect = Rect(mp[0], mp[1]-tipText.get_height(), tipText.get_width()+10, tipText.get_height())
                    draw.rect(screen, BLACK, tipRect)
                    screen.blit(tipText, (mp[0]+5, mp[1]-tipText.get_height()-2))

    # Draw the cropped surface onto the canvas after the tool is let go
    if cropSurface and not tooling:
        # Resize it and blit the new cropped surface
        newCrop = transform.smoothscale(cropSurface, canvasSize)
        canvasSurface.blit(newCrop, (0, 0))
        del newCrop
        # Blit the canvas to the screen
        screen.blit(canvasSurface, canvasLoc)
        # Clear the cropped surface
        cropSurface = None
        # Remove the latest surface, as it will contain the guide rectangle and replace it with a copy of the canvas
        undoList.pop()
        undoList.append(canvasSurface.copy())
        # Mark as a change occurred
        needToSave = True
    furthurProcessing -= 1 if furthurProcessing > 0 else 0

    if helpOpen:
        screen.blit(helpImage, (width//2-helpImage.get_width()//2, height//2-helpImage.get_height()//2))
    # Update the display
    display.flip()
raise SystemExit
