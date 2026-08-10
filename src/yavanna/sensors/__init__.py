"""Sensor drivers.

Each concrete sensor wraps an injected hardware *device* object so the read
logic is unit-testable with a fake. The real hardware libraries (Blinka,
w1thermsensor, gpiozero) are imported lazily — only in ``factory.build_sensors``
— so importing this package never requires a Raspberry Pi.
"""
