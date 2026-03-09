from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

import mujoco


@dataclass
class SimConfig:
    steps: int = 1000
    realtime: bool = True
    render_every: int = 1
    title: str = "MuJoCo Demo"


def run_headless(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    steps: int,
    controller: Optional[Callable[[mujoco.MjModel, mujoco.MjData, int], None]] = None,
    logger: Optional[Callable[[mujoco.MjModel, mujoco.MjData, int], None]] = None,
) -> None:
    """Run a simulation without a GUI."""
    for step in range(steps):
        if controller is not None:
            controller(model, data, step)
        mujoco.mj_step(model, data)
        if logger is not None:
            logger(model, data, step)


def run_gui_passive(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    steps: int,
    controller: Optional[Callable[[mujoco.MjModel, mujoco.MjData, int], None]] = None,
    logger: Optional[Callable[[mujoco.MjModel, mujoco.MjData, int], None]] = None,
    realtime: bool = True,
) -> None:
    """
    Run with passive viewer.

    macOS note:
      Use `mjpython your_script.py` instead of plain `python` when calling
      mujoco.viewer.launch_passive(...).
    """
    import mujoco.viewer

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running() and data.time < steps * model.opt.timestep:
            step = int(round(data.time / model.opt.timestep))

            if controller is not None:
                controller(model, data, step)

            mujoco.mj_step(model, data)

            if logger is not None:
                logger(model, data, step)

            viewer.sync()

            if realtime:
                time.sleep(model.opt.timestep)


def save_offscreen_video_frames(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    steps: int,
    out_dir: str,
    controller: Optional[Callable[[mujoco.MjModel, mujoco.MjData, int], None]] = None,
    width: int = 640,
    height: int = 480,
    fps_div: int = 5,
) -> None:
    """
    Save PNG frames using MuJoCo's offscreen renderer.

    This is useful for 'headless but visual' workflows.
    """
    from pathlib import Path
    import imageio.v3 as iio

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    renderer = mujoco.Renderer(model, height=height, width=width)

    for step in range(steps):
        if controller is not None:
            controller(model, data, step)

        mujoco.mj_step(model, data)

        if step % fps_div == 0:
            renderer.update_scene(data)
            pixels = renderer.render()
            frame_path = Path(out_dir) / f"frame_{step:05d}.png"
            iio.imwrite(frame_path, pixels)

    renderer.close()