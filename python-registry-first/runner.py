# runner.py
import importlib
import pkgutil
import sys
import logging
import yaml
import click
from plugin_base import available_plugins, PluginMeta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "config.yaml"

def discover_plugins(package_name: str):
    """
    Import modules under the plugins package so classes register.
    """
    package = importlib.import_module(package_name)
    for finder, name, ispkg in pkgutil.iter_modules(package.__path__):
        full_name = f"{package_name}.{name}"
        if full_name not in sys.modules:
            importlib.import_module(full_name)

def load_config(path: str):
    try:
        with open(path, "r") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}

def _coerce_cli_val(val):
    # try int/bool fallback to string
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    try:
        return int(val)
    except Exception:
        return val

@click.group()
@click.option("--config", "-c", default=DEFAULT_CONFIG_FILE, help="Path to YAML config.")
@click.pass_context
def cli(ctx, config):
    cfg = load_config(config)
    ctx.obj = cfg
    discover_plugins("plugins")

@cli.command()
@click.pass_context
def list(ctx):
    cfg = ctx.obj or {}
    enabled_cfg = cfg.get("enabled_plugins", {})
    plugins = available_plugins(enabled_cfg)
    for name, cls in plugins.items():
        info = cls.info()
        print(f"{name} v{info['version']}: {info['description']} (class={info['class']})")

@cli.command()
@click.argument("plugin_name")
@click.argument("args", nargs=-1)
@click.option("--kw", "-k", multiple=True, help="key=value kwargs")
@click.pass_context
def run(ctx, plugin_name, args, kw):
    """Run a plugin by name. positional args are strings, convert inside plugin."""
    cfg = ctx.obj or {}
    enabled_cfg = cfg.get("enabled_plugins", {})
    plugins = available_plugins(enabled_cfg)
    cls = plugins.get(plugin_name)
    if not cls:
        print(f"No enabled plugin named '{plugin_name}'")
        sys.exit(2)

    # parse kwargs passed as key=value
    k = {}
    for kv in kw:
        if "=" in kv:
            key, val = kv.split("=", 1)
            k[key] = _coerce_cli_val(val)

    instance = cls(cfg.get("plugin_config", {}).get(plugin_name))
    # note: plugin decides how to coerce/parse args (string -> ints etc.)
    try:
        result = instance.run(*args, **k)
        print("Result:", result)
    except Exception as e:
        logger.exception("Plugin raised an exception")
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    cli()
