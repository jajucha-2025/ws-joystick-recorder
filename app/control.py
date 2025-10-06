def on_joystick(x: float, y: float):
  try:
    import jchm

    max_speed = 15
    dSteer = round(x * 10)
    dSpeed = round(y * max_speed)

    jchm.control.set_motor(dSteer, dSteer, dSpeed)
  except ModuleNotFoundError:
    pass
