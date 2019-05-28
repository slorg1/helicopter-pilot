import itertools
import logging
import time

from Controller import Controller

logging.basicConfig(format='%(asctime)s %(levelname)-6s %(name)s %(message)s', level=logging.DEBUG)

controller = Controller()

logging.getLogger(__name__).info("Let's do a ceilling plant!")

crescendo = tuple(range(30, Controller.MAX_THROTTLE - 30, 10))
for throttle in itertools.chain(crescendo, reversed(crescendo)):
    controller.throttle = throttle
    controller.send()

    time.sleep(0.2)  # there is a built-in delay in send right now

time.sleep(3)
#     print('tilt LEFT!')
#     h.trim = Helicopter.DEF_TRIM / 2
#     p.send()
#     time.sleep(2)
#
#     print('tilt RIGHT!')
#     h.trim = Helicopter.MAX_TRIM
#     p.send()
#     time.sleep(2)
# #     h.yaw = Helicopter.MAX_PITCH
# #     p.send()
#     time.sleep(1)
#     print('Turn LEFT!')
#     h.yaw = Helicopter.DEF_YAW * 2
#     p.send()
#     time.sleep(1)
#     time.sleep(1)
#     print("DON'T TURN")
#     h.yaw = Helicopter.DEF_YAW
#     p.send()
#     h.throttle = Helicopter.MAX_THROTTLE / 2
#     p.send()
#     time.sleep(10)
#     time.sleep(20)
logging.getLogger(__name__).info("Let's land this bucket!")
controller.land()
