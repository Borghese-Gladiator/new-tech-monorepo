import mujoco
from mujoco_helpers import run_headless

MODEL_XML = """
<mujoco model="falling_box">
  <option timestep="0.005" gravity="0 0 -9.81"/>
  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.1"/>
    <body name="box" pos="0 0 1">
      <freejoint/>
      <geom type="box" size="0.06 0.06 0.06" mass="1"/>
    </body>
  </worldbody>
</mujoco>
"""

def logger(model, data, step):
    if step % 100 == 0:
        print(
            f"step={step:4d} "
            f"time={data.time:.3f} "
            f"pos=({data.qpos[0]:.3f}, {data.qpos[1]:.3f}, {data.qpos[2]:.3f})"
        )

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

run_headless(model, data, steps=2000, logger=logger)