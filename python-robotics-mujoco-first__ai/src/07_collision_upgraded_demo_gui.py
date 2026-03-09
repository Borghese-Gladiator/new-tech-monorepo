import math
import time
import numpy as np
import mujoco
import mujoco.viewer

MODEL_XML = """
<mujoco model="collision_upgraded_gui">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <visual>
    <map force="0.2"/>
  </visual>

  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1" rgba="0.2 0.3 0.4 1"
          solref="0.003 1" solimp="0.95 0.99 0.001"/>

    <!-- NEW: multiple falling bodies, not just one ball -->
    <body name="ball1" pos="-0.15 0 1.3">
      <freejoint/>
      <!-- CHANGED: contact params tuned for a snappier bounce -->
      <geom name="ball1_geom" type="sphere" size="0.08" mass="0.35"
            rgba="0.9 0.2 0.2 1"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>
    </body>

    <body name="ball2" pos="0.18 0 1.6">
      <freejoint/>
      <geom name="ball2_geom" type="sphere" size="0.06" mass="0.20"
            rgba="0.9 0.6 0.1 1"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>
    </body>

    <!-- NEW: fixed obstacle to create richer collision patterns -->
    <body name="obstacle" pos="0.45 0 0.16">
      <geom name="obstacle_geom" type="box" size="0.08 0.20 0.16"
            mass="5.0" rgba="0.3 0.8 0.3 1"/>
    </body>

    <!-- Sliding striker -->
    <body name="striker" pos="-0.95 0 0.09">
      <joint name="slide_x" type="slide" axis="1 0 0"/>
      <geom name="striker_geom" type="box" size="0.14 0.14 0.09" mass="2.0"
            rgba="0.2 0.6 0.9 1"
            solref="0.003 1" solimp="0.95 0.99 0.001"/>

      <!-- NEW: touch sensor needs a site -->
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


def controller(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    # Same PD idea as before, but slightly more aggressive.
    t = data.time
    target = 0.75 * math.sin(1.35 * t)

    # qpos layout:
    # ball1 freejoint -> qpos[0:7]
    # ball2 freejoint -> qpos[7:14]
    # striker slide joint -> qpos[14]
    x = data.qpos[14]
    v = data.qvel[12]  # ball1 6 + ball2 6 + striker 1 => striker vel index 12

    kp = 55.0
    kd = 10.0
    data.ctrl[0] = kp * (target - x) - kd * v


def contact_pairs_with_force(model: mujoco.MjModel, data: mujoco.MjData):
    rows = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)

        # NEW: read contact wrench
        wrench = np.zeros(6, dtype=np.float64)
        mujoco.mj_contactForce(model, data, i, wrench)

        normal_force = abs(wrench[0])
        tangential_force = float(np.linalg.norm(wrench[1:3]))
        rows.append((g1, g2, normal_force, tangential_force))
    return rows


model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

# NEW: show contact points and contact forces in the GUI
with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
    viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = True

    last_tick = -1
    last_collision_count = 0

    while viewer.is_running() and data.time < 12.0:
        controller(model, data)
        mujoco.mj_step(model, data)

        tick = int(data.time * 10)
        if tick != last_tick:
            last_tick = tick

            # ball1 xyz
            b1x, b1y, b1z = data.qpos[0], data.qpos[1], data.qpos[2]
            # ball2 xyz
            b2x, b2y, b2z = data.qpos[7], data.qpos[8], data.qpos[9]
            striker_x = data.qpos[14]

            # NEW: touch sensor is in sensordata[0]
            touch_value = data.sensordata[0]

            print(
                f"time={data.time:5.2f}  "
                f"ball1=({b1x:+.3f},{b1y:+.3f},{b1z:+.3f})  "
                f"ball2=({b2x:+.3f},{b2y:+.3f},{b2z:+.3f})  "
                f"striker_x={striker_x:+.3f}  "
                f"touch={touch_value:.4f}  "
                f"contacts={data.ncon}"
            )

            # NEW: detailed contact force reporting
            rows = contact_pairs_with_force(model, data)
            for g1, g2, fn, ft in rows[:6]:
                print(f"   {g1} <-> {g2}   normal={fn:8.3f}   tangent={ft:8.3f}")

            if data.ncon > last_collision_count:
                print("   NEW COLLISION(S) DETECTED")

            last_collision_count = data.ncon

        viewer.sync()
        time.sleep(model.opt.timestep)