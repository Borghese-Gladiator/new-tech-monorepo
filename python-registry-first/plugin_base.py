# plugin_base.py
from typing import Dict, Type, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PluginError(Exception):
    pass

class PluginMeta(type):
    """Central registry for plugins."""
    registry: Dict[str, Type["BasePlugin"]] = {}

    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)

        # marker to avoid registering the abstract base class
        if attrs.get("_is_base"):
            return cls

        plugin_name = attrs.get("PLUGIN_NAME") or name
        if plugin_name in mcls.registry:
            raise PluginError(
                f"Plugin name conflict: '{plugin_name}' already registered by {mcls.registry[plugin_name]!r}"
            )
        mcls.registry[plugin_name] = cls
        logger.debug("Registered plugin '%s' -> %s", plugin_name, cls)
        return cls

class BasePlugin(metaclass=PluginMeta):
    _is_base = True  # avoid registering the base class itself

    PLUGIN_NAME: str = "base"
    DESCRIPTION: str = "abstract plugin"
    VERSION: str = "0.0.0"
    ENABLED_BY_DEFAULT: bool = True

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def run(self, *args, **kwargs) -> Any:
        """Override in subclasses. Return result or raise."""
        raise NotImplementedError()

    @classmethod
    def info(cls) -> Dict[str, str]:
        return {
            "name": cls.PLUGIN_NAME,
            "description": getattr(cls, "DESCRIPTION", ""),
            "version": getattr(cls, "VERSION", ""),
            "class": cls.__name__,
        }

def available_plugins(enabled_filter: Optional[dict] = None):
    """
    Return dict of plugin_name -> class. Optionally pass a dict from config
    that can disable/enable plugins, e.g. {'resize': True, 'compress': False}
    """
    if not enabled_filter:
        return dict(PluginMeta.registry)
    out = {}
    for name, cls in PluginMeta.registry.items():
        # config can override ENABLED_BY_DEFAULT
        cfg_val = enabled_filter.get(name) if isinstance(enabled_filter, dict) else None
        if cfg_val is None:
            enabled = bool(getattr(cls, "ENABLED_BY_DEFAULT", True))
        else:
            enabled = bool(cfg_val)
        if enabled:
            out[name] = cls
    return out
