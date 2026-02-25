import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# =============================
# Simulation Parameters
# =============================
dt = 0.05
wheel_base = 0.4
base_speed = 1.0
Kp = 2.0
follow_distance = 0.8

world_size = 10

# =============================
# Robot State
# =============================
robot = {
    "x": 0.0,
    "y": 0.0,
    "theta": 0.0,
    "v_l": 0.0,
    "v_r": 0.0
}

# =============================
# Phone Path (Target)
# =============================
def phone_position(t):
    # Circular motion
    radius = 3
    speed = 0.4
    angle = speed * t
    return np.array([radius * np.cos(angle),
                     radius * np.sin(angle)])

# =============================
# Helper Functions
# =============================
def wrap_angle(a):
    return (a + np.pi) % (2 * np.pi) - np.pi

def update_robot():
    v_l = robot["v_l"]
    v_r = robot["v_r"]

    v = (v_r + v_l) / 2
    omega = (v_r - v_l) / wheel_base

    robot["x"] += v * np.cos(robot["theta"]) * dt
    robot["y"] += v * np.sin(robot["theta"]) * dt
    robot["theta"] += omega * dt

# =============================
# Control Logic
# =============================
def follow_controller(target):
    dx = target[0] - robot["x"]
    dy = target[1] - robot["y"]

    distance = np.sqrt(dx**2 + dy**2)
    desired_heading = np.arctan2(dy, dx)
    angle_error = wrap_angle(desired_heading - robot["theta"])

    if distance < follow_distance:
        robot["v_l"] = 0
        robot["v_r"] = 0
        return

    robot["v_l"] = base_speed - Kp * angle_error
    robot["v_r"] = base_speed + Kp * angle_error

# =============================
# Visualization Setup
# =============================
fig, ax = plt.subplots()
ax.set_xlim(-world_size, world_size)
ax.set_ylim(-world_size, world_size)
ax.set_aspect('equal') # Keeps the circle from looking like an oval

robot_dot, = ax.plot([], [], 'ro', label="Robot")
phone_dot, = ax.plot([], [], 'bo', label="Target")
heading_line, = ax.plot([], [], 'r-')
trail_line, = ax.plot([], [], 'r--', linewidth=0.5) # Pre-define the trail

trail_x = []
trail_y = []
time = 0

# =============================
# Animation Loop
# =============================
def animate(frame):
    global time
    time += dt

    target = phone_position(time)
    follow_controller(target)
    update_robot()

    trail_x.append(robot["x"])
    trail_y.append(robot["y"])

    # FIX 1: Pass data as lists [val] to satisfy "must be a sequence"
    robot_dot.set_data([robot["x"]], [robot["y"]])
    phone_dot.set_data([target[0]], [target[1]])
    
    heading_line.set_data(
        [robot["x"], robot["x"] + 0.5 * np.cos(robot["theta"])],
        [robot["y"], robot["y"] + 0.5 * np.sin(robot["theta"])]
    )

    # FIX 2: Update the existing trail line instead of creating new plots
    trail_line.set_data(trail_x, trail_y)

    return robot_dot, phone_dot, heading_line, trail_line

# FIX 3: Added cache_frame_data=False to stop the warning
ani = FuncAnimation(fig, animate, interval=dt*1000, cache_frame_data=False)
plt.title("Robotics Follow Simulation")
plt.legend()
plt.show()