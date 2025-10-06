_last = 0.0  # 필요시 rate limit 등에 사용

def on_joystick(angleDeg: float, strength: float, x: float, y: float, ts: float):
  # TODO: 여기에서 자주차 제어 명령을 보냄.
  # 전송주기 제한이 필요하면 _last와 ts를 비교해서 throttle 하면 됨.
  pass
