#https://deborahrfowler.com/MathForVSFX/RotatedSquares.html
# Turtle Exercise run on Desktop/Python 3

import turtle

print("Turtle Exercise run on Desktop/Python 3")

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
    t.color("black")
    drawSquare(t,240,0)
    for i in range(0,20):
        size = 240 * pow(1/1.2,i+1)
        drawSquare(t,size,12.5)
    t.ht()

def main():
    turtle.setup(750,750)
    turtle.title("Rotated Squares")
    t = turtle.Pen()
    t.width(2)
    t.speed(0)
    drawSquarePattern(t)
    turtle.exitonclick()

main()
