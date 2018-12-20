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
title = "Microsoft Paint"
startTime = ptime.time()
print("Starting initialization process")

# Load the configuration file
print("Loading configuration")
try:
    with open("config.json", "r") as configFile:
        config = json.load(configFile)
except IOError:
    print("Unable to load configuration! Ensure that config.json exists!")
    sys.exit(1)
except ValueError:
    print("Invalid configuration! Ensure that config.json is valid JSON!")
    sys.exit(1)
try :
    with open(".git/refs/heads/master") as versionFile:
        version = versionFile.read()
except IOError:
    version = "unknown"
print("Loaded configuration!")
print("%d keys loaded into registry" % len(config))

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
# Tools that will only be executed if the dragging started over the canvas
mustBeOverCanvas = ["bucket", "crop", "brush"]
# Rectangles whose colours will not be updated by the loop
doNotUpdateOnReDraw = ["colourDisplayRect", "backDisplayRect"]
# List of surfaces to undo and redo
undoList = []
redoList = []

# Whether the tool modified the canvas on the iteration
toolStatus = False

# Stores whether there has been a change since the last save
needToSave = False
# The size of the canvas
canvasSize = (700,  500)

# Stores settings for the music player
musicRegistry = {"playing": "", "queue": [], "played": [], "loop": False, "loopPlaylist": False, "playMode": 0}
# Play mode:
# Float - paused and location
# 0 - Do not auto play next
# 1 - Random
# 2 - By filename

# Defines the canvas surface and fills it with white
canvasSurface = Surface(canvasSize)
canvasSurface.fill(WHITE)

# Adds a blank surface to the undo list
undoList.append(canvasSurface.copy())

# Store the music to be played
musicList = []

# Whether to fills shapes
shapeFilled = False

# Rate limits tools such as air brush
toolDelay = ptime.time()

# Initialize Tkinter and hide it
root = Tk()
root.withdraw()

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
                "brushRect": [Rect(config["rects"]["brushRect"][0]), eval(config["rects"]["brushRect"][1]), config["rects"]["brushRect"][2]]}

# Define the palette collide point rectangle (will not be drawn)
palRect = Rect(config["paletteLocation"][0], config["paletteLocation"][1], config["paletteSize"][0], config["paletteSize"][1])
# Define the canvas collide point rectangle (will not be drawn)
canvasRect = Rect(config["canvasLocation"][0], config["canvasLocation"][1], config["canvasSize"][0], config["canvasSize"][1])
# Define the rectangle to clear the canvas
clearRect = Rect(config["rects"]["clearRect"][0])

# Define the open and save buttons
openRect = Rect(config["rects"]["openRect"][0])
saveRect = Rect(config["rects"]["saveRect"][0])

# Blit the canvas on to the screen
screen.blit(canvasSurface, canvasLoc)

# Load ALL images before the while loop
palPic = image.load(config["paletteImage"])
screen.blit(palPic, config["paletteLocation"])

# Initialize the mixer and give it an event type to trigger on music finish
mixer.init()
mixer.music.set_endevent(SONG_END)

print("%s initialized successfully in %0.4fs \nOn commit %s"%(title, ptime.time()-startTime, version))

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
    draw.line(canvasSurface, lregistry["toolColour"], dragStart, mpos, lregistry["toolThickness"])
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
    global toolDelay

    # Rate limiting so that the program doesn't make many operations per click
    if ptime.time() - toolDelay > 0.001:
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
        print(queue)
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

# Initialize the registry
registry = {"toolName": "Nothing", "toolFunc": nothing, "toolArgs": {"updateOldPerTick": False},
            "toolColour": (255, 255, 255), "toolThickness": 2, "backgroundColour": (255, 255, 255)}

while running:
    mb = mouse.get_pressed()
    mp = mouse.get_pos()
    for evt in event.get():
        if evt.type == QUIT:
            running = False
        if evt.type == KEYDOWN:
            if evt.key == K_f:
                shapeFilled = not shapeFilled
            if evt.key == K_b:
                canvasRe = ""
            if evt.key == K_c:
                print(screen.get_at(mp), canvasSurface.get_at(convertToCanvas(mp)))
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
            tooling = True
            oldscreen = canvasSurface.copy()
            dragStart = mouse.get_pos()
            if evt.button == 4:
                registry["toolThickness"] += 1 if registry["toolThickness"] < 100 else 0
            elif evt.button == 5:
                registry["toolThickness"] -= 1 if registry["toolThickness"] > 1 else 0
        if evt.type == MOUSEBUTTONUP:
            tooling = False
            print("sghafjsgkfsk", clearRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]))
            print(toolStatus)
            # Undo logic:
            if ((canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]) and registry["toolName"] != "Nothing") or
                (clearRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]))) and toolStatus:
                print("sagfsg")
                needToSave = True
                undoList.append(canvasSurface.copy())
                print(len(undoList))
        if evt.type == SONG_END:
            if musicRegistry["loop"]:
                mixer.music.play(musicRegistry["playing"])
            else:
                if musicRegistry["playMode"] == 1:
                    musicName = choice(musicRegistry["queue"])
                    while musicName not in musicRegistry["played"]:
                        musicRegistry["playing"] = musicName
                        mixer.music.play(musicName)
                        musicRegistry["played"].append(musicName)
                elif musicRegistry["playMode"] == 2:
                    musicName = musicRegistry["playing"]
                    pos = musicList.index(musicName)
                    pos += 1 if pos + 1 < len(musicList) else 50000
                    if pos < 10000:
                        musicRegistry["playing"] = musicList[pos]
                        mixer.music.play(musicName)
                    elif musicRegistry["loopPlaylist"]:
                        pos = 0
                        musicRegistry["playing"] = musicList[pos]
                        mixer.music.play(musicName)
    toolStatus = False

    # Sync the colour showing rect's colour in the rectRegistry to the tool colour
    rectRegistry["colourDisplayRect"][1] = registry["toolColour"]
    rectRegistry["backColourDisplayRect"][1] = registry["backgroundColour"]

    # Draw rects
    for key, rectArray in rectRegistry.items():
        draw.rect(screen, rectArray[1], rectArray[0], rectArray[2])
    draw.rect(screen, WHITE, clearRect)
    draw.rect(screen, WHITE, openRect)
    draw.rect(screen, WHITE, saveRect)


    # Check if the cursor was drawing and did not release
    # Check if the cursor has clicked on a tool button
    if mb[0] and not tooling and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        # Set the toolFunc in the registry to be the tool that was chosen, and whether the starting pos will be
        # updated per tick and update the colour of the rectangle to show selected
        if rectRegistry["pencilRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = pencil
            registry["toolName"] = "Pencil"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["pencilRect"][1] = RED
        elif rectRegistry["eraserRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = eraser
            registry["toolName"] = "Eraser"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["eraserRect"][1] = RED
        elif rectRegistry["shapeRectRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeRect
            registry["toolName"] = "ShapeRect"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeRectRect"][1] = RED
        elif rectRegistry["shapeEllipseRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeEllipse
            registry["toolName"] = "ShapeEllipse"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw:
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeEllipseRect"][1] = RED
        elif rectRegistry["lineRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = line
            registry["toolName"] = "Line"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if key not in doNotUpdateOnReDraw or "back":
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
        elif clearRect.collidepoint(mp[0], mp[1]):
            print("hello!")
            canvasSurface.fill(registry["backgroundColour"])
            needToSave = True
            undoList.append(canvasSurface.copy())
            screen.blit(canvasSurface, canvasLoc)
        elif openRect.collidepoint(mp[0], mp[1]):
            openFile(registry)
        elif saveRect.collidepoint(mp[0], mp[1]):
            saveFile()

    # Check if the mouse is over the colour wheel and a tool is currently not being used
    if mb[0] and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        if palRect.collidepoint(mp[0], mp[1])  and ((mp[0]-palRect.centerx)**2 + (mp[1]-palRect.centery)**2)**0.5 < 101:
            # Get the colour and the point
            registry["toolColour"] = screen.get_at((mp[0], mp[1]))

    # Check if the mouse is over the colour wheel and a tool is currently not being used
    if mb[2] and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        if palRect.collidepoint(mp[0], mp[1]) and (
                (mp[0] - palRect.centerx) ** 2 + (mp[1] - palRect.centery) ** 2) ** 0.5 < 101:
            # Get the colour and the point
            registry["backgroundColour"] = screen.get_at((mp[0], mp[1]))

    # Check if the user clicked on left-click
    if mb[0]:
        # Execute the tool function, checking if the drag must start on the canvas
        if not registry["toolName"] in mustBeOverCanvas or canvasRect.collidepoint(mp[0], mp[1]):
            toolStatus = registry["toolFunc"](convertToCanvas(mp), registry)
            screen.blit(canvasSurface, canvasLoc)
        toolDelay = ptime.time()

        # If the old position needs to be updated per tick, even when the tool is engaged (shadow), update it
        if registry["toolArgs"]["updateOldPerTick"]:
            lastTickLocation = convertToCanvas(mp)
    else:
        # If the mouse is currently not being clicked, update the dragStart variable to keep track of where the cursor
        # was. So that we can get a start point for shape tools
        dragStart = convertToCanvas(mp)
        lastTickLocation = convertToCanvas(mp)

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
    # Update the display
    display.flip()
raise SystemExit
