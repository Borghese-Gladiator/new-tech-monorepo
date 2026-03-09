import math
import mujoco
from mujoco_helpers import run_gui_passive

MODEL_XML = """
<mujoco model="pendulum">
  <option timestep="0.005" gravity="0 0 -9.81"/>
  <worldbody>
    <body name="pivot" pos="0 0 1">
      <joint name="hinge" type="hinge" axis="0 1 0"/>
      <geom type="capsule" fromto="0 0 0 0 0 -0.6" size="0.04" mass="1" rgba="0.8 0.4 0.1 1"/>
    </body>
  </worldbody>
</mujoco>
"""

def controller(model, data, step):
    # At step 300, reset the pendulum to a new angle.
    if step == 300:
        data.qpos[0] = math.pi / 2
        data.qvel[0] = 0.0
        mujoco.mj_forward(model, data)

def logger(model, data, step):
    if step % 50 == 0:
        print(
            f"step={step:4d} time={data.time:.2f} "
            f"theta={data.qpos[0]:.3f} omega={data.qvel[0]:.3f}"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

data.qpos[0] = math.pi / 3
mujoco.mj_forward(model, data)

run_gui_passive(model, data, steps=1200, controller=controller, logger=logger)