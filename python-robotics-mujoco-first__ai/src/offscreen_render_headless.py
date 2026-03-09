import math
import mujoco
from mujoco_helpers import save_offscreen_video_frames

MODEL_XML = """
<mujoco model="offscreen_demo">
  <option timestep="0.01" gravity="0 0 -9.81"/>
  <worldbody>
    <geom type="plane" size="3 3 0.1"/>
    <body name="box" pos="0 0 1">
      <freejoint/>
      <geom type="box" size="0.07 0.07 0.07" mass="1"/>
    </body>
  </worldbody>
</mujoco>
"""

def controller(model, data, step):
    pass

model = mujoco.MjModel.from_xml_string(MODEL_XML)
data = mujoco.MjData(model)

save_offscreen_video_frames(
    model,
    data,
    steps=500,
    out_dir="frames_offscreen",
    controller=controller,
    width=640,
    height=480,
    fps_div=5,
)

print("Saved frames to frames_offscreen/")