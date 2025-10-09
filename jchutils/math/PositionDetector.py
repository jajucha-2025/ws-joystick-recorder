import math


### -----------------------------------
### state: (x, y, theta)
### v: rear-wheel linear speed (cm/s)
### delta: steering angle (rad)
### L: wheelbase (cm)
### dt: time step (s)
### -----------------------------------


def _deriv(state, v, deltaL, deltaR, L):
    x, y, theta = state
    ctheta = theta + math.pi/2
    R = L/2 * (1/math.tan(deltaL) + 1/math.tan(deltaR))
    
    dx = v * math.cos(ctheta)
    dy = v * math.sin(ctheta)
    dtheta = v / R

    return dx, dy, dtheta

def pd_euler(state, v, deltaL, deltaR, L, dt):
    x, y, theta = state

    dx, dy, dtheta = _deriv(state, v, deltaL, deltaR, L)

    x += dx * dt
    y += dy * dt
    theta += dtheta * dt

    theta = (theta + math.pi) % (2*math.pi) - math.pi
    return (x, y, theta)


def pd_rk2(state, v, deltaL, deltaR, L, dt):
    x, y, theta = state

    k1 = _deriv((x, y, theta)
        , v, deltaL, deltaR, L)
    k2 = _deriv((x + 0.5*dt*k1[0], y + 0.5*dt*k1[1], theta + 0.5*dt*k1[2])
        , v, deltaL, deltaR, L)
    
    x_next = x + dt*k2[0]
    y_next = y + dt*k2[1]
    theta_next = theta + dt*k2[2]

    theta_next = (theta_next + math.pi) % (2*math.pi) - math.pi
    return (x_next, y_next, theta_next)


def pd_rk4(state, v, deltaL, deltaR, L, dt):
    x, y, theta = state

    k1 = _deriv((x, y, theta)
        , v, deltaL, deltaR, L)
    k2 = _deriv((x + 0.5*dt*k1[0], y + 0.5*dt*k1[1], theta + 0.5*dt*k1[2])
        , v, deltaL, deltaR, L)
    k3 = _deriv((x + 0.5*dt*k2[0], y + 0.5*dt*k2[1], theta + 0.5*dt*k2[2])
        , v, deltaL, deltaR, L)
    k4 = _deriv((x + dt*k3[0], y + dt*k3[1], theta + dt*k3[2])
        , v, deltaL, deltaR, L)

    x_next = x + (dt/6.0)*(k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
    y_next = y + (dt/6.0)*(k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
    theta_next = theta + (dt/6.0)*(k1[2] + 2*k2[2] + 2*k3[2] + k4[2])

    theta_next = (theta_next + math.pi) % (2*math.pi) - math.pi
    return (x_next, y_next, theta_next)