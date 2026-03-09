import math
import mujoco
from mujoco_helpers import run_headless

MODEL_XML = """
<mujoco model="ball_plate">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <worldbody>
    <body name="plate_base" pos="0 0 0.5">
      <joint name="tilt_x" type="hinge" axis="1 0 0"/>
      <joint name="tilt_y" type="hinge" axis="0 1 0"/>
      <geom name="plate" type="box" size="0.5 0.5 0.02" mass="3"/>
    </body>

    <body name="ball" pos="0 0 1.0">
      <freejoint/>
      <geom type="sphere" size="0.04" mass="0.2"/>
    </body>
  </worldbody>

  <actuator>
    <motor joint="tilt_x" gear="20"/>
    <motor joint="tilt_y" gear="20"/>
  </actuator>
</mujoco>
"""

def controller(model, data, step):
    t = data.time
    data.ctrl[0] = 0.1 * math.sin(1.0 * t)
    data.ctrl[1] = 0.1 * math.cos(1.3 * t)

def logger(model, data, step):
    if step % 100 == 0:
        # Plate joints occupy qpos[0], qpos[1]
        # Ball freejoint starts after that: qpos[2:9], with xyz at [2], [3], [4]
        bx = data.qpos[2]
        by = data.qpos[3]
        bz = data.qpos[4]
        print(
            f"step={step:4d} t={data.time:.2f} "
            f"ball=({bx:.3f}, {by:.3f}, {bz:.3f}) "
            f"tilt=({data.qpos[0]:.3f}, {data.qpos[1]:.3f})"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_headless(model, data, steps=4000, controller=controller, logger=logger)