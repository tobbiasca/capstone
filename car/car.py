from pynput import keyboard
from adafruit_motorkit import MotorKit
import time

# Initialize HAT
kit = MotorKit(address=0x60)

# Motors
leftMotor = kit.motor1
rightMotor = kit.motor2

def off():
    leftMotor.throttle = None
    rightMotor.throttle = None

import atexit
atexit.register(off)

# Movement functions (/ = throttle from -1 to 1)
def forward(speed=1.0):
    leftMotor.throttle = speed
    rightMotor.throttle = speed

def backward(speed=1.0):
    leftMotor.throttle = -speed
    rightMotor.throttle = -speed

def left(speed=1.0):
    leftMotor.throttle = speed * 0.3
    rightMotor.throttle = speed

def right(speed=1.0):
    leftMotor.throttle = speed
    rightMotor.throttle = speed * 0.3

def stop():
    leftMotor.throttle = 0
    rightMotor.throttle = 0

# Holds pressed keys
pressed = set()

def on_press(key):
    try:
        pressed.add(key.char.lower())
    except:
        pass

def on_release(key):
    try:
        pressed.remove(key.char.lower())
    except:
        pass

    if key == keyboard.Key.esc:
        return False

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Hold W/A/S/D to move. ESC to exit.")

try:
    while True:
        if "w" in pressed:
            forward()
        elif "s" in pressed:
            backward()
        elif "a" in pressed:
            left()
        elif "d" in pressed:
            right()
        else:
            stop()

        time.sleep(0.03)

except KeyboardInterrupt:
    stop()


