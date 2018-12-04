# Copyright (C) 2018 David Hui. All rights reserved.
# Permission is hereby granted to modify and redistribute this file for educational purposes with attribution.
from pygame import *


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
oldscreen = None
lock = False
shapeFilled = False


# Placeholder function for no tool (startup)
def nothing(mpos, lregistry):
    return


# Pencil tool
# Draw many lines so that we get a continuous line, like a pencil
def pencil(mpos, lregistry):
    draw.line(screen, lregistry["toolColour"], dragStart, mpos, lregistry["toolThickness"])


# Rectangle shape tool
def dShapeRect(mpos, lregistry):
    global shapeFilled
    # Restore old version of screen so that we don't get overlap
    screen.blit(oldscreen, (0,0))

    # Very sketchy way of changing the rectangle depending on a negative width and/or height

    # Positive width and height
    rectString = "Rect(dragStart[0]-i, dragStart[1]-i, mpos[0] - (dragStart[0] - i*2), mpos[1] - (dragStart[1] - i*2))"

    # Negative height
    if dragStart[0] < mp[0] and dragStart[1] > mp[1]:
        rectString = "Rect(dragStart[0]+i, dragStart[1]-i, mpos[0] - (dragStart[0] + i*2)," \
                     " mpos[1] - (dragStart[1] - i*2))"

    # Negative width
    elif dragStart[0] > mp[0] and dragStart[1] < mp[1]:
        rectString = "Rect(dragStart[0]-i, dragStart[1]+i, mpos[0] - (dragStart[0] - i*2), " \
                     "mpos[1] - (dragStart[1] + i*2))"

    # Negative width and height
    elif dragStart[0] < mp[0] and dragStart[1] < mp[1]:
        rectString = "Rect(dragStart[0]+i, dragStart[1]+i, mpos[0] - (dragStart[0] + i*2), " \
                     "mpos[1] - (dragStart[1] + i*2))"

    # Draw a smooth rectangle (only for unfilled), unless the thickness is greater than the size of the rectangle
    # In that case, always draw a filled rectangle with the specified size
    if lregistry["toolThickness"] * 2 < min(abs(mp[0] - dragStart[0]), abs(mp[1] - dragStart[1])) and not shapeFilled:
        for i in range(lregistry["toolThickness"]):
            tempRect = eval(rectString)
            tempRect.normalize()
            draw.rect(screen, lregistry["toolColour"], tempRect, 1)
    else:
        draw.rect(screen, lregistry["toolColour"], (dragStart[0], dragStart[1], mp[0]-dragStart[0],
                                                    mp[1]-dragStart[1]), 0)


def eraser(mpos, lregistry):
    # Draw a white circle to "erase"
    draw.circle(screen, WHITE, mpos, lregistry["toolThickness"])


# Function that draws lines
def line(mpos, lregistry):
    # Restore the copy of the screen before the tool was clicked so that we don't get overlapping lines
    screen.blit(oldscreen, (0, 0))

    # Draw a line from the start of the click to the current position
    draw.line(screen, GREEN, dragStart, mp)


# Initialize the registry
registry = {"toolName": "Nothing", "toolFunc": nothing, "toolArgs": {"updateOldPerTick": False},
            "toolColour": (255, 255, 255), "toolThickness": 2}

# Initialize the rectangles
pencilRect = Rect(20, 80, 40, 40)
eraserRect = Rect(70, 80, 40, 40)
shapeRect = Rect(20, 170, 40, 40)
canvasRect = Rect(150, 80, 700, 500)
palRect = Rect(865, 80, 200, 200)
colorDisplayRect = Rect(865, 300, 50, 50)

draw.rect(screen, WHITE, canvasRect)

# Local ALL images before the while loop
palPic = image.load("images/colpal.png")
screen.blit(palPic, (865, 80))

while running:
    mb = mouse.get_pressed()
    mp = mouse.get_pos()
    for evt in event.get():
        if evt.type == QUIT:
            running = False
        if evt.type == MOUSEBUTTONDOWN:
            oldscreen = screen.copy()
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

    # Draw rects
    draw.rect(screen, GREEN, pencilRect, 2)
    draw.rect(screen, GREEN, eraserRect, 2)
    draw.rect(screen, GREEN, shapeRect, 2)
    draw.rect(screen, registry["toolColour"], colorDisplayRect)

    # Check if the cursor was drawing and did not release
    # Check if the cursor has clicking on a tool button
    if mb[0] and not lock:
        # Set the toolFunc in the registry to be the tool that was chosen, and whether the starting pos will be
        # updated per tick
        if pencilRect.collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = pencil
            registry["toolName"] = "Pencil"
            registry["toolArgs"]["updateOldPerTick"] = True
        elif eraserRect.collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = eraser
            registry["toolName"] = "Eraser"
            registry["toolArgs"]["updateOldPerTick"] = False
        elif shapeRect.collidepoint(mp[0], mp[1]):
            registry["toolFunc"] = dShapeRect
            registry["toolName"] = "Shape"
            registry["toolArgs"]["updateOldPerTick"] = False

    # Check if the cursor is over the canvas, and the user clicked
    if mb[0]:
        if canvasRect.collidepoint(mp[0], mp[1]):
            # Prevent eraser from drawing outside of canvas
            screen.set_clip(canvasRect)

            # Execute the tool function
            registry["toolFunc"](mp, registry)

            # If the old position needs to be updated per tick, even when the tool is engaged (shadow), update it
            if registry["toolArgs"]["updateOldPerTick"]:
                dragStart = mp
            # Remove the screen clip so that other elements can be updated
            screen.set_clip(None)

    # Check if the mouse is over the colour wheel and a tool is currently not beingused
    if mb[0]:
        if palRect.collidepoint(mp[0], mp[1]) and not lock:
            # Get the colour and the point
            registry["toolColour"] = screen.get_at((mp[0], mp[1]))
    else:
        # If the mouse is currently not being clicked, update the dragStart variable to keep track of where the cursor
        # was. So that we can get a start point for shape tools
        dragStart = mp

    # Update the display
    display.flip()

raise SystemExit
