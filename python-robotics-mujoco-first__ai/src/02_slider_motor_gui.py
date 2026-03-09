import math
import mujoco
from mujoco_helpers import run_gui_passive

MODEL_XML = """
<mujoco model="slider_motor">
  <option timestep="0.01"/>
  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1" rgba="0.9 0.9 0.9 1"/>
    <body name="cart" pos="0 0 0.1">
      <joint name="slide" type="slide" axis="1 0 0"/>
      <geom type="box" size="0.1 0.06 0.05" mass="1" rgba="0.2 0.5 0.9 1"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="cart_motor" joint="slide" gear="1"/>
  </actuator>
</mujoco>
"""

def controller(model, data, step):
    t = data.time
    data.ctrl[0] = 1.5 * math.sin(2.0 * t)

def logger(model, data, step):
    if step % 50 == 0:
        print(
            f"step={step:4d} time={data.time:.2f} "
            f"x={data.qpos[0]:.3f} vx={data.qvel[0]:.3f} ctrl={data.ctrl[0]:.3f}"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_gui_passive(model, data, steps=1500, controller=controller, logger=logger)