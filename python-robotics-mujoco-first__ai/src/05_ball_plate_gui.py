import math
import mujoco
from mujoco_helpers import run_gui_passive

MODEL_XML = """
<mujoco model="ball_plate">
  <option timestep="0.005" gravity="0 0 -9.81"/>

  <worldbody>
    <body name="plate_base" pos="0 0 0.5">
      <joint name="tilt_x" type="hinge" axis="1 0 0"/>
      <joint name="tilt_y" type="hinge" axis="0 1 0"/>
      <geom name="plate" type="box" size="0.5 0.5 0.02" mass="3" rgba="0.6 0.6 0.7 1"/>
    </body>

    <body name="ball" pos="0 0 1.0">
      <freejoint/>
      <geom name="ball_geom" type="sphere" size="0.04" mass="0.2" rgba="0.9 0.2 0.2 1"/>
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
    # Gentle, time-varying tilts
    data.ctrl[0] = 0.15 * math.sin(1.2 * t)
    data.ctrl[1] = 0.12 * math.cos(0.8 * t)

def logger(model, data, step):
    if step % 100 == 0:
        bx = data.qpos[2]
        by = data.qpos[3]
        bz = data.qpos[4]
        print(
            f"step={step:4d} time={data.time:.2f} "
            f"tilt=({data.qpos[0]:.3f}, {data.qpos[1]:.3f}) "
            f"ball=({bx:.3f}, {by:.3f}, {bz:.3f})"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_gui_passive(model, data, steps=4000, controller=controller, logger=logger)