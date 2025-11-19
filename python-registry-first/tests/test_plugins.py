# tests/test_plugins.py
import importlib
import pkgutil
import sys
from plugin_base import PluginMeta, available_plugins

def discover_for_tests():
    import plugins  # package
    for finder, name, ispkg in pkgutil.iter_modules(plugins.__path__):
        full = f"plugins.{name}"
        if full not in sys.modules:
            importlib.import_module(full)

def test_registry_population():
    discover_for_tests()
    assert "resize" in PluginMeta.registry
    assert "compress" in PluginMeta.registry
    assert "watermark" in PluginMeta.registry

def test_available_plugins_default():
    discover_for_tests()
    # default should include all unless plugin toggles default
    avail = available_plugins()
    assert "resize" in avail
    assert "compress" in avail

def test_simulated_run():
    discover_for_tests()
    cls = PluginMeta.registry["resize"]
    inst = cls({})
    res = inst.run("example.jpg", 100, 100)
    assert isinstance(res, dict)
    assert "status" in res
