from .state import get_pos, set_car, _car

def on_joystick(x: float, y: float, dt: float):
  print(dt)
  max_speed = 15
  dSteer = round(x * 10)
  dSpeed = round(y * max_speed)

  pos = get_pos(_car["wheelbase"], dt, _car["pos"], dSteer*2, dSpeed)
  set_car(_car["wheelbase"], pos)

  try:
    import jchm
    jchm.control.set_motor(dSteer, dSteer, dSpeed)
  except:
    pass
