import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .comm import MdriveComm

__all__ = [
    "MdriveAxis",
    "emergency_stop",
]


class MdriveAxis:
    """
    Mdrive controller for a single axis

    To control multiple axes, initialize an `MdriveComm` and pass it to all axes. The
    name of each axis must match name on the device, `DN`.
    """

    _homing_register: str = "R1"

    def __init__(self, comm: "MdriveComm", name: str):
        self.comm = comm
        self.name = name

    def _synchronous_write(self, command: str) -> None:
        self.comm._synchronous_write(f"{self.name}{command}")

    async def _write(self, command: str) -> None:
        await self.comm._write(f"{self.name}{command}")

    async def _write_read(self, command: str) -> str:
        return await self.comm._write_read(f"{self.name}{command}")

    async def _write_read_multiline(self, command: str) -> str:
        return await self.comm._write_read_multiline(f"{self.name}{command}")

    def enable(self) -> None:
        self._synchronous_write("DE=1")

    def disable(self) -> None:
        self._synchronous_write("DE=0")

    async def is_moving(self) -> bool:
        response = await self._write_read("PR MV")
        return bool(int(response))

    async def wait_for_motion_done(self) -> None:
        while await self.is_moving() is True:
            await asyncio.sleep(0.25)

    async def read_all_parameters(self) -> list:
        return await self._write_read_multiline("PR AL")

    async def set_position(self, position: int) -> None:
        assert isinstance(position, int)
        await self._write(f"P={position}")

    async def get_position(self) -> int:
        response = await self._write_read("PR P")
        return int(response)

    def set_velocity(self, velocity: int) -> None:
        assert isinstance(velocity, int)
        self._synchronous_write(f"VM={velocity}")

    async def get_velocity(self) -> int:
        response = await self._write_read("PR VM")
        return int(response)

    async def set_acceleration(self, acceleration: int) -> None:
        assert isinstance(acceleration, int)
        await self._write(f"A={acceleration}")

    async def get_acceleration(self) -> int:
        response = await self._write_read("PR A")
        return int(response)

    async def move_absolute(self, position: int) -> None:
        assert isinstance(position, int)
        await self._write(f"MA {position}")

    async def move_relative(self, movement: int) -> None:
        assert isinstance(movement, int)
        await self._write(f"MR {movement}")

    async def abort_move(self) -> None:
        """Abort the current move command."""
        await self._write("SL 0")

    async def _home(self, velocity: int) -> None:
        await self._write(f"SL {velocity}")
        await self.wait_for_motion_done()

        await self.set_position(0)
        await self._write(f"{self._homing_register}=1")

    async def home_negative(self) -> None:
        velocity = await self.get_velocity()
        await self._home(-velocity)

    async def home_positive(self) -> None:
        velocity = await self.get_velocity()
        await self._home(velocity)

    async def is_homed(self) -> bool:
        response = await self._write_read(f"PR {self._homing_register}")
        return response == "1"


def emergency_stop(comm: "MdriveComm") -> None:
    """Stop all axes immediately."""
    comm._synchronous_write(chr(27))
