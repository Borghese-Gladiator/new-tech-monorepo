import math
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import mujoco

MODEL_XML = """
<mujoco model="collision_upgraded_headless">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <visual>
    <map force="0.2"/>
  </visual>

  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1"
          solref="0.003 1" solimp="0.95 0.99 0.001"/>

    <!-- NEW: two balls -->
    <body name="ball1" pos="-0.15 0 1.3">
      <freejoint/>
      <geom name="ball1_geom" type="sphere" size="0.08" mass="0.35"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>
    </body>

    <body name="ball2" pos="0.18 0 1.6">
      <freejoint/>
      <geom name="ball2_geom" type="sphere" size="0.06" mass="0.20"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>
    </body>

    <!-- NEW: extra obstacle -->
    <body name="obstacle" pos="0.45 0 0.16">
      <geom name="obstacle_geom" type="box" size="0.08 0.20 0.16" mass="5.0"/>
    </body>

    <body name="striker" pos="-0.95 0 0.09">
      <joint name="slide_x" type="slide" axis="1 0 0"/>
      <geom name="striker_geom" type="box" size="0.14 0.14 0.09" mass="2.0"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>

      <!-- NEW: site for touch sensor -->
      <site name="striker_touch_site" pos="0.14 0 0" size="0.04"/>
    </body>
  </worldbody>

  <actuator>
    <motor name="striker_motor" joint="slide_x" gear="1"/>
  </actuator>

  <!-- NEW: touch sensor -->
  <sensor>
    <touch name="striker_touch" site="striker_touch_site"/>
  </sensor>
</mujoco>
"""

SAVE_FRAMES = True          # NEW: headless rendering option
FRAME_DIR = "collision_frames"
TOTAL_STEPS = 2400
FRAME_EVERY = 8


def controller(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    t = data.time
    target = 0.75 * math.sin(1.35 * t)

    x = data.qpos[14]
    v = data.qvel[12]

    kp = 55.0
    kd = 10.0
    data.ctrl[0] = kp * (target - x) - kd * v


def contact_rows(model: mujoco.MjModel, data: mujoco.MjData):
    rows = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)

        # NEW: per-contact force
        wrench = np.zeros(6, dtype=np.float64)
        mujoco.mj_contactForce(model, data, i, wrench)

        fn = abs(wrench[0])
        ft = float(np.linalg.norm(wrench[1:3]))
        rows.append((g1, g2, fn, ft))
    return rows


model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

# NEW: offscreen renderer for headless output
renderer = None
if SAVE_FRAMES:
    Path(FRAME_DIR).mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, width=640, height=480)

collision_events = 0
previous_in_contact = False

for step in range(TOTAL_STEPS):
    controller(model, data)
    mujoco.mj_step(model, data)

    if step % 20 == 0:
        b1x, b1y, b1z = data.qpos[0], data.qpos[1], data.qpos[2]
        b2x, b2y, b2z = data.qpos[7], data.qpos[8], data.qpos[9]
        striker_x = data.qpos[14]
        touch_value = data.sensordata[0]

        print(
            f"step={step:4d} time={data.time:5.2f} "
            f"ball1=({b1x:+.3f},{b1y:+.3f},{b1z:+.3f}) "
            f"ball2=({b2x:+.3f},{b2y:+.3f},{b2z:+.3f}) "
            f"striker_x={striker_x:+.3f} "
            f"touch={touch_value:.4f} "
            f"contacts={data.ncon}"
        )

        for g1, g2, fn, ft in contact_rows(model, data)[:6]:
            print(f"   {g1} <-> {g2}   normal={fn:8.3f}   tangent={ft:8.3f}")

    in_contact = data.ncon > 0
    if in_contact and not previous_in_contact:
        collision_events += 1
        print(f"\nCollision event #{collision_events} at time {data.time:.4f}\n")

    previous_in_contact = in_contact

    # NEW: save offscreen frames
    if renderer is not None and step % FRAME_EVERY == 0:
        renderer.update_scene(data)
        pixels = renderer.render()
        iio.imwrite(f"{FRAME_DIR}/frame_{step:05d}.png", pixels)

if renderer is not None:
    renderer.close()

print(f"\nDone. Total collision events detected: {collision_events}")
if SAVE_FRAMES:
    print(f"Saved frames to: {FRAME_DIR}/")