
from clusto.drivers.base import Device, ResourceManagerMixin
from clusto.drivers.devices.common import PortMixin

class BasicPowerStrip(PortMixin, Device):
    """
    Basic power strip Driver.
    """

    _clustoType = "powerstrip"
    _driverName = "basicpowerstrip"
    

    _properties = { 'maxport': 20,
                    'minport': 1 }
    