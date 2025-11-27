import pygame
from adafruit_motorkit import MotorKit

kit = MotorKit()

LOW = 0.6
TURN = 0.4
MAX = 1.0

pygame.init()
screen = pygame.display.set_mode((200, 200))
pygame.display.set_caption("RC Car Keyboard Control")

running = True
keys = {"w": False, "s": False, "a": False, "d": False}

def clamp_motor(value):
    if value > 0:
        return max(LOW, min(MAX, value))
    elif value < 0:
        return min(-LOW, max(-MAX, value))
    else:
        return 0

def update_motors():
    motor1 = 0
    motor2 = 0

    if keys["w"]:
        motor1 = LOW + 0.04
        motor2 = LOW
    elif keys["s"]:
        motor1 = -LOW
        motor2 = -LOW

    if keys["a"]:
        motor1 -= TURN
        motor2 += TURN
    if keys["d"]:
        motor1 += TURN
        motor2 -= TURN

    kit.motor1.throttle = clamp_motor(motor1)
    kit.motor2.throttle = clamp_motor(motor2)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                keys["w"] = True
            elif event.key == pygame.K_s:
                keys["s"] = True
            elif event.key == pygame.K_a:
                keys["a"] = True
            elif event.key == pygame.K_d:
                keys["d"] = True
            elif event.key == pygame.K_q:
                running = False

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                keys["w"] = False
            elif event.key == pygame.K_s:
                keys["s"] = False
            elif event.key == pygame.K_a:
                keys["a"] = False
            elif event.key == pygame.K_d:
                keys["d"] = False

    update_motors()
    pygame.time.delay(20)

# stop motors when quitting
kit.motor1.throttle = 0
kit.motor2.throttle = 0
pygame.quit()
