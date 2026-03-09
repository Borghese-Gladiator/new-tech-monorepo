import mujoco
from mujoco_helpers import run_gui_passive

MODEL_XML = """
<mujoco model="falling_box">
  <option timestep="0.005" gravity="0 0 -9.81"/>
  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1" rgba="0.2 0.3 0.4 1"/>
    <body name="box" pos="0 0 1">
      <freejoint/>
      <geom type="box" size="0.06 0.06 0.06" mass="1" rgba="0.9 0.2 0.2 1"/>
    </body>
  </worldbody>
</mujoco>
"""

def logger(model, data, step):
    if step % 100 == 0:
        z = data.qpos[2]
        print(f"step={step:4d} time={data.time:.3f} z={z:.3f}")

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_gui_passive(model, data, steps=2000, logger=logger)