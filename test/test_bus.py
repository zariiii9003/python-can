import importlib
import inspect
from unittest.mock import patch

import can


def test_bus_channel_arg():
    """Ensure that all available bus classes can be imported and
    that ``channel`` is always the first argument."""
    for module_name, class_name in can.interface.BACKENDS.values():
        module = importlib.import_module(module_name)
        bus_class = getattr(module, class_name)
        signature = inspect.signature(bus_class)
        assert next(signature.parameters.__iter__()) == "channel"


def test_bus_ignore_config():
    with patch.object(
        target=can.util, attribute="load_config", side_effect=can.util.load_config
    ):
        _ = can.Bus(interface="virtual", ignore_config=True)
        assert not can.util.load_config.called

        _ = can.Bus(interface="virtual")
        assert can.util.load_config.called
