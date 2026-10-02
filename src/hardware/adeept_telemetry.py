"""Adapter for the Adeept PiCar Pro system telemetry module."""


class AdeeptTelemetry:
    def __init__(self, info_module=None):
        if info_module is None:
            import Info as info_module
        self._info = info_module

    def read(self):
        return {
            "cpu_percent": float(self._info.get_cpu_use()),
            "memory_percent": float(self._info.get_ram_info()),
            "temperature_c": float(self._info.get_cpu_tempfunc()),
        }