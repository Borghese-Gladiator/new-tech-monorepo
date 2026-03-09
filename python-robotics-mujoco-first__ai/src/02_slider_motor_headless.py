import math
import mujoco
from mujoco_helpers import run_headless

MODEL_XML = """
<mujoco model="slider_motor">
  <option timestep="0.01"/>
  <worldbody>
    <body name="cart" pos="0 0 0">
      <joint name="slide" type="slide" axis="1 0 0"/>
      <geom type="box" size="0.1 0.06 0.05" mass="1"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="cart_motor" joint="slide" gear="1"/>
  </actuator>
</mujoco>
"""

def controller(model, data, step):
    data.ctrl[0] = 2.0 * math.sin(1.5 * data.time)

def logger(model, data, step):
    if step % 50 == 0:
        print(
            f"step={step:4d} time={data.time:.2f} "
            f"x={data.qpos[0]:.3f} vx={data.qvel[0]:.3f}"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_headless(model, data, steps=1000, controller=controller, logger=logger)