from .state import get_pos, set_car, _car
import jchm
import sys
import time


v = 6.57 # 확정
d = 2.129 # 구해야 함

def on_joystick(x: float, y: float, dt: float):
  max_speed = 15
  #dSteerL = round(x * 10)
  #dSteerR = round(x * 10)
  #dSpeed = round(y * max_speed)
  dSteerL = -5
  dSteerR = -5
  dSpeed = 0

  pos = get_pos(_car["wheelbase"], dt, _car["pos"], dSteerL*d, dSteerR*d, dSpeed*v)
  set_car(_car["wheelbase"], _car["trackspacing"], pos)

  # theta
  '''if _car["isFirst"] == True:
    jchm.control.set_motor(dSteer, dSteer, dSpeed)
    if pos[2] < 0:
      _car["isFirst"] = False
  else:
    if pos[2] >= 0:
      jchm.control.set_motor(0, 0, 0)'''

  try:
    jchm.control.set_motor(dSteerL, dSteerR, dSpeed)
    # jchm.control.set_motor(10, 10, 30)
    # jchm.control.set_motor(0, 0, 0)
  except:
    pass
