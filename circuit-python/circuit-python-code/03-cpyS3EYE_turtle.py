#https://coxxect.blogspot.com/2023/10/my-dev-board-yd-esp32-s3-eye.html
# Turtle Exercise run on ESP32-S3-EYE/CircuitPython
# ref: https://learn.adafruit.com/circuitpython-turtle-graphics

import board
from adafruit_turtle import Color, turtle
import os, sys

display = board.DISPLAY
turtle = turtle(board.DISPLAY)

info = os.uname()[4] + "\n" + \
       sys.implementation[0] + " " + os.uname()[3] + "\n" + \
       "board.DISPLAY: " + str(display.width) + "x" + str(display.height)
print("=======================================")
print(info)
print("=======================================")
print("Turtle Exercise run on ESP32-S3-EYE/CircuitPython")

def drawSquare(t,size,angle):
    t.left(angle)
    halfsize = size * .5
    t.pu()
    t.setpos(0,0)
    t.backward(halfsize)
    t.left(90)
    t.backward(halfsize)
    t.right(90)
    t.pd()

    for i in range(0,4):
        t.fd(size)
        t.left(90)

def drawSquarePattern(t):
    t.pencolor(Color.WHITE)
    drawSquare(t,240,0)
    for i in range(0,20):
        size = 240 * pow(1/1.2,i+1)
        drawSquare(t,size,12.5)
    t.ht()

drawSquarePattern(turtle)
print("~ bye ~")
