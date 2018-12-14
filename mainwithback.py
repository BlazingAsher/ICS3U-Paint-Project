# Copyright (C) 2018 David Hui. All rights reserved.
# Permission is hereby granted to modify and redistribute this file for educational purposes with attribution.
from pygame import *
import pygame.gfxdraw as gfxdraw
from random import randint
import time as ptime


size = width, height = (1080, 768)
screen = display.set_mode(size)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
display.set_caption("MasseyHacks Paint")
running = True
dragStart = (0, 0)
lastTickLocation = (0, 0)
oldscreen = None
canvasLoc = (150, 80)

backgroundSurface = Surface((700, 500))
backgroundSurface.fill((255, 255, 255))

canvasSurface = Surface((700, 500))
canvasSurface.set_colorkey((255, 255, 254))
canvasSurface.fill((255, 255, 254))

# Whether a tool is currently engaged
lock = False
shapeFilled = False
toolDelay = ptime.time()


# Initialize the rectangles
rectRegistry = {"colourDisplayRect": [Rect(865, 300, 50, 50), WHITE, 0],
                "pencilRect": [Rect(20, 80, 40, 40), GREEN, 2], "eraserRect": [Rect(70, 80, 40, 40), GREEN, 2],
                "shapeRectRect": [Rect(20, 170, 40, 40), GREEN, 2],
                "shapeEllipseRect": [Rect(70, 170, 40, 40), GREEN, 2],
                "lineRect": [Rect(20, 260, 40, 40), GREEN, 2], "airbrushRect": [Rect(70, 260, 40, 40), GREEN, 2],
                "bucketRect": [Rect(20, 350, 40, 40), GREEN, 2]}

palRect = Rect(865, 80, 200, 200)
canvasRect = Rect(150, 80, 700, 500)

#draw.rect(screen, WHITE, canvasRect)

screen.blit(backgroundSurface, canvasLoc)
screen.blit(canvasSurface, canvasLoc)

# Local ALL images before the while loop
palPic = image.load("images/colpal.png")
screen.blit(palPic, (865, 80))


def convertToCanvas(pos):
    global canvasLoc
    return (pos[0] - canvasLoc[0], pos[1] - canvasLoc[1])


def convertToGlobal(pos):
    global canvasLoc
    return (pos[0] + canvasLoc[0], pos[1] + canvasLoc[1])


# Placeholder function for no tool (startup)
def nothing(mpos, lregistry):
    return


# Pencil tool
# Draw many lines so that we get a continuous line, like a pencil
def pencil(mpos, lregistry):
    draw.circle(canvasSurface, GREEN, (0, 0), 5)
    print(mpos)
    draw.line(canvasSurface, lregistry["toolColour"], lastTickLocation, mpos, lregistry["toolThickness"])

# Rectangle shape tool
def dShapeRect(mpos, lregistry):
    global shapeFilled
    # Restore old version of screen so that we don't get overlap
    canvasSurface.blit(oldscreen, (0, 0))
    #canvasSurface.fill(BLUE)

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
    # In that case, always draw a filled rectangle with the specified size
    if lregistry["toolThickness"] * 2 < min(abs(mpos[0] - dragStart[0]), abs(mpos[1] - dragStart[1])) and not shapeFilled:
        for i in range(lregistry["toolThickness"]):
            tempRect = eval(rectString)
            tempRect.normalize()
            draw.rect(canvasSurface, lregistry["toolColour"], tempRect, 1)
    else:
        draw.rect(canvasSurface, lregistry["toolColour"], (dragStart[0], dragStart[1], mpos[0]-dragStart[0],
                                                    mpos[1]-dragStart[1]), 0)


def dShapeEllipse(mpos, lregistry):
    global shapeFilled, dragStart
    # Restore old version of screen so that we don't get overlap
    #canvasSurface.blit(oldscreen, (0, 0))
    print(randint(0,255))
    #screen.fill(WHITE)

    keyColour = (255, 255, 253)

    tempRect = Rect(dragStart[0], dragStart[1], mpos[0] - dragStart[0],
                    mpos[1] - dragStart[1])
    tempRect.normalize()
    rx, ry, rw, rh = tempRect
    if lregistry["toolThickness"] * 2 < min(abs(mpos[0] - dragStart[0]), abs(mpos[1] - dragStart[1])) and not shapeFilled:
        tempSurface = Surface((rw, rh))
        tempSurface.set_colorkey(keyColour)
        tempSurface.fill(keyColour)
        tempRect = Rect(0, 0, rw, rh)
        tempRect.normalize()
        draw.ellipse(tempSurface, lregistry["toolColour"], (0, 0, rw, rh))
        draw.ellipse(tempSurface, keyColour,
                     (lregistry["toolThickness"], lregistry["toolThickness"], rw - lregistry["toolThickness"]*2,
                      rh - lregistry["toolThickness"]*2), 0)
        canvasSurface.blit(tempSurface, (rx, ry))

    else:
        draw.ellipse(canvasSurface, lregistry["toolColour"], tempRect, 0)


def eraser(mpos, lregistry):
    # Draw a white circle to "erase"
    draw.circle(canvasSurface, (255, 255, 254), mpos, lregistry["toolThickness"])
    screen.blit(backgroundSurface, canvasLoc)


# Function that draws lines
def line(mpos, lregistry):
    # Restore the copy of the screen before the tool was clicked so that we don't get overlapping lines
    canvasSurface.blit(oldscreen, (0, 0))

    # Draw a line from the start of the click to the current position
    draw.line(canvasSurface, lregistry["toolColour"], dragStart, mpos, lregistry["toolThickness"])


def airbrush(mpos, lregistry):
    global toolDelay
    # Rate limiting
    if ptime.time() - toolDelay > 0.00100003:
        toolDelay = ptime.time()
        numPoints = randint(0, 10)
        pointList = []
        while len(pointList) < numPoints:
            x = randint(mpos[0]-lregistry["toolThickness"] // 2, mpos[0]+lregistry["toolThickness"] // 2)
            y = randint(mpos[1] - lregistry["toolThickness"] // 2, mpos[1] + lregistry["toolThickness"] // 2)
            if ((x-mpos[0])**2 + (y-mpos[1])**2)**0.5 < lregistry["toolThickness"]/2:
                pointList.append((x, y))
        for point in pointList:
            gfxdraw.circle(canvasSurface, point[0], point[1], 1, lregistry["toolColour"])


def bucket(mpos, lregistry):
    global screen, width, height
    pxArray = PixelArray(canvasSurface)
    sPxArray = PixelArray(screen)
    colourAtMouse = sPxArray[convertToGlobal(mpos)]

    queue = set()
    filled = set()
    queue.add((mpos[0], mpos[1]))
    fillColour = screen.map_rgb(lregistry["toolColour"])
    print(queue)
    while queue:
        currPos = queue.pop()
        filled.add(currPos)
        pxArray[currPos[0], currPos[1]] = fillColour
        if currPos[0] - 1 >= 0 and sPxArray[convertToGlobal((currPos[0] - 1, currPos[1]))] == colourAtMouse and (currPos[0]-1, currPos[1]) not in filled:
            queue.add((currPos[0] - 1, currPos[1]))
        if currPos[0] + 1 < canvasSurface.get_width() and sPxArray[convertToGlobal((currPos[0] + 1, currPos[1]))] == colourAtMouse and (currPos[0]+1, currPos[1]) not in filled:
            queue.add((currPos[0] + 1, currPos[1]))
        if currPos[1] - 1 >= 0 and sPxArray[convertToGlobal((currPos[0], currPos[1]-1))] == colourAtMouse and (currPos[0], currPos[1]-1) not in filled:
            queue.add((currPos[0], currPos[1] - 1))
        if currPos[1] + 1 < canvasSurface.get_height() and sPxArray[convertToGlobal((currPos[0], currPos[1]+1))] == colourAtMouse and (currPos[0], currPos[1]+1) not in filled:
            queue.add((currPos[0], currPos[1] + 1))
    del pxArray
    del sPxArray


# Initialize the registry
registry = {"toolName": "Nothing", "toolFunc": nothing, "toolArgs": {"updateOldPerTick": False},
            "toolColour": (255, 255, 255), "toolThickness": 2}

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
        if evt.type == MOUSEBUTTONDOWN:
            oldscreen = canvasSurface.copy()
            dragStart = mouse.get_pos()
            if evt.button == 4:
                registry["toolThickness"] += 1 if registry["toolThickness"] < 50 else 0
            elif evt.button == 5:
                registry["toolThickness"] -= 1 if registry["toolThickness"] > 1 else 0
            if canvasRect.collidepoint(mp[0], mp[1]):
                lock = True
        if evt.type == MOUSEBUTTONUP:
            if not canvasRect.collidepoint(mp[0], mp[1]):
                lock = False
    # Sync the colour showing rect's colour in the rectRegistry to the tool colour
    rectRegistry["colourDisplayRect"][1] = registry["toolColour"]

    # Draw rects

    for key, rectArray in rectRegistry.items():
        draw.rect(screen, rectArray[1], rectArray[0], rectArray[2])

    # Check if the cursor was drawing and did not release
    # Check if the cursor has clicking on a tool button
    #print(toolDelay - ptime.time())

    if mb[0] and not lock and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        # Set the toolFunc in the registry to be the tool that was chosen, and whether the starting pos will be
        # updated per tick
        #print("change")
        if rectRegistry["pencilRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = pencil
            registry["toolName"] = "Pencil"
            registry["toolArgs"]["updateOldPerTick"] = True
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["pencilRect"][1] = RED
        elif rectRegistry["eraserRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = eraser
            registry["toolName"] = "Eraser"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["eraserRect"][1] = RED
        elif rectRegistry["shapeRectRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeRect
            registry["toolName"] = "ShapeRect"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeRectRect"][1] = RED
        elif rectRegistry["shapeEllipseRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeEllipse
            registry["toolName"] = "ShapeEllipse"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["shapeEllipseRect"][1] = RED
        elif rectRegistry["lineRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = line
            registry["toolName"] = "Line"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["lineRect"][1] = RED
        elif rectRegistry["airbrushRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = airbrush
            registry["toolName"] = "airbrush"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["airbrushRect"][1] = RED
        elif rectRegistry["bucketRect"][0].collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = bucket
            registry["toolName"] = "bucket"
            registry["toolArgs"]["updateOldPerTick"] = False
            for key, value in rectRegistry.items():
                if not key == "colourDisplayRect":
                    rectRegistry[key][1] = GREEN
            rectRegistry["bucketRect"][1] = RED

    # Check if the mouse is over the colour wheel and a tool is currently not being used
    if mb[0] and not canvasRect.collidepoint(convertToGlobal(dragStart)[0], convertToGlobal(dragStart)[1]):
        if palRect.collidepoint(mp[0], mp[1]) and not lock and ((mp[0]-palRect.centerx)**2 + (mp[1]-palRect.centery)**2)**0.5 < 101:
            # Get the colour and the point
            registry["toolColour"] = screen.get_at((mp[0], mp[1]))

    # Check if the user clicked on left-click
    if mb[0]:
        # Prevent tools from drawing outside of canvas
        #screen.set_clip(canvasRect)

        # Execute the tool function unless it is the paint bucket
        if not registry["toolName"] == "bucket" or canvasRect.collidepoint(mp[0], mp[1]):
            registry["toolFunc"](convertToCanvas(mp), registry)
            screen.blit(canvasSurface, canvasLoc)
        toolDelay = ptime.time()

        # If the old position needs to be updated per tick, even when the tool is engaged (shadow), update it
        if registry["toolArgs"]["updateOldPerTick"]:
            lastTickLocation = convertToCanvas(mp)
        # Remove the screen clip so that other elements can be updated
        #screen.set_clip(None)
    else:
        # If the mouse is currently not being clicked, update the dragStart variable to keep track of where the cursor
        # was. So that we can get a start point for shape tools
        dragStart = convertToCanvas(mp)
        lastTickLocation = convertToCanvas(mp)

    # Update the display
    display.flip()

raise SystemExit
