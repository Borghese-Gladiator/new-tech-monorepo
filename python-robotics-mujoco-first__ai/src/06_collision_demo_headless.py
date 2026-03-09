import math
import mujoco

MODEL_XML = """
<mujoco model="collision_demo">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1"/>

    <body name="ball" pos="0 0 1.2">
      <freejoint/>
      <geom name="ball_geom" type="sphere" size="0.08" mass="0.4"/>
    </body>

    <body name="striker" pos="-0.8 0 0.08">
      <joint name="slide_x" type="slide" axis="1 0 0"/>
      <geom name="striker_geom" type="box" size="0.12 0.12 0.08" mass="2.0"/>
    </body>
  </worldbody>

  <actuator>
    <motor name="striker_motor" joint="slide_x" gear="1"/>
  </actuator>
</mujoco>
"""


def controller(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    t = data.time
    target = 0.65 * math.sin(1.2 * t)

    x = data.qpos[7]
    v = data.qvel[6]

    kp = 40.0
    kd = 8.0
    data.ctrl[0] = kp * (target - x) - kd * v


def contact_pairs(model: mujoco.MjModel, data: mujoco.MjData) -> list[str]:
    pairs = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1)
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)
        pairs.append(f"{g1} <-> {g2}")
    return pairs


model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

collision_events = 0
was_in_contact = False

for step in range(2000):
    controller(model, data)
    mujoco.mj_step(model, data)

    if step % 20 == 0:
        ball_x = data.qpos[0]
        ball_y = data.qpos[1]
        ball_z = data.qpos[2]
        striker_x = data.qpos[7]

        print(
            f"step={step:4d} time={data.time:5.2f} "
            f"ball=({ball_x:+.3f}, {ball_y:+.3f}, {ball_z:+.3f}) "
            f"striker_x={striker_x:+.3f} contacts={data.ncon}"
        )

    in_contact = data.ncon > 0
    if in_contact and not was_in_contact:
        collision_events += 1
        print(f"\nCollision event #{collision_events} at time {data.time:.3f}")
        for pair in contact_pairs(model, data):
            print("  ", pair)
        print()

    was_in_contact = in_contact

print(f"Done. Total collision events detected: {collision_events}")