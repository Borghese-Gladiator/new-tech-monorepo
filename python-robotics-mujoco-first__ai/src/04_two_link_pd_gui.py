import math
import numpy as np
import mujoco
from mujoco_helpers import run_gui_passive

MODEL_XML = """
<mujoco model="two_link_arm">
  <option timestep="0.005" gravity="0 0 0"/>
  <worldbody>
    <body name="base" pos="0 0 0">
      <joint name="joint1" type="hinge" axis="0 0 1"/>
      <geom type="capsule" fromto="0 0 0 0.5 0 0" size="0.04" mass="1" rgba="0.8 0.2 0.2 1"/>

      <body name="link2" pos="0.5 0 0">
        <joint name="joint2" type="hinge" axis="0 0 1"/>
        <geom type="capsule" fromto="0 0 0 0.4 0 0" size="0.035" mass="0.8" rgba="0.2 0.6 0.9 1"/>
      </body>
    </body>
  </worldbody>

  <actuator>
    <motor joint="joint1" gear="1"/>
    <motor joint="joint2" gear="1"/>
  </actuator>
</mujoco>
"""

KP = np.array([20.0, 15.0])
KD = np.array([5.0, 4.0])

def controller(model, data, step):
    t = data.time
    q_des = np.array([
        0.8 * math.sin(1.0 * t),
        0.5 * math.sin(2.0 * t),
    ])
    q = data.qpos[:2].copy()
    dq = data.qvel[:2].copy()

    tau = KP * (q_des - q) - KD * dq
    data.ctrl[:] = tau

def logger(model, data, step):
    if step % 100 == 0:
        print(
            f"step={step:4d} t={data.time:.2f} "
            f"q=({data.qpos[0]:.3f}, {data.qpos[1]:.3f}) "
            f"dq=({data.qvel[0]:.3f}, {data.qvel[1]:.3f})"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_gui_passive(model, data, steps=3000, controller=controller, logger=logger)