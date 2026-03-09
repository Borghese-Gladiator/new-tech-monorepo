import math
import time
import mujoco
import mujoco.viewer

MODEL_XML = """
<mujoco model="collision_demo">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <visual>
    <map force="0.1"/>
  </visual>

  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1" rgba="0.2 0.3 0.4 1"/>

    <!-- Falling ball -->
    <body name="ball" pos="0 0 1.2">
      <freejoint/>
      <geom name="ball_geom" type="sphere" size="0.08" mass="0.4" rgba="0.9 0.2 0.2 1"/>
    </body>

    <!-- Sliding striker -->
    <body name="striker" pos="-0.8 0 0.08">
      <joint name="slide_x" type="slide" axis="1 0 0"/>
      <geom name="striker_geom" type="box" size="0.12 0.12 0.08" mass="2.0" rgba="0.2 0.6 0.9 1"/>
    </body>
  </worldbody>

  <actuator>
    <motor name="striker_motor" joint="slide_x" gear="1"/>
  </actuator>
</mujoco>
"""


def contact_pairs(model: mujoco.MjModel, data: mujoco.MjData) -> list[str]:
    pairs = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)
        pairs.append(f"{g1} <-> {g2}")
    return pairs


def controller(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    # Drive the striker left/right so it can hit the ball after it lands.
    t = data.time
    target = 0.65 * math.sin(1.2 * t)

    x = data.qpos[7]   # striker slide joint position
    v = data.qvel[6]   # striker joint velocity

    kp = 40.0
    kd = 8.0
    data.ctrl[0] = kp * (target - x) - kd * v


model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

with mujoco.viewer.launch_passive(model, data) as viewer:
    last_print = -1

    while viewer.is_running() and data.time < 10.0:
        controller(model, data)
        mujoco.mj_step(model, data)

        # Print state every 0.1s
        tick = int(data.time * 10)
        if tick != last_print:
            last_print = tick

            # qpos layout:
            # ball freejoint = 7 entries: x y z qw qx qy qz
            ball_x = data.qpos[0]
            ball_y = data.qpos[1]
            ball_z = data.qpos[2]
            striker_x = data.qpos[7]

            print(
                f"time={data.time:5.2f}  "
                f"ball=({ball_x:+.3f}, {ball_y:+.3f}, {ball_z:+.3f})  "
                f"striker_x={striker_x:+.3f}  "
                f"contacts={data.ncon}"
            )

            if data.ncon > 0:
                for pair in contact_pairs(model, data):
                    print("   ", pair)

        viewer.sync()
        time.sleep(model.opt.timestep)