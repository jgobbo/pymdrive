import asyncio

from .comm import MdriveComm

__all__ = [
    "MdriveAxis",
    "emergency_stop",
]

COMM = MdriveComm("COM3")


class MdriveAxis:
    def __init__(self, name: str):
        self.comm = COMM
        self.name = name

    def __del__(self):
        self.abort_move()
        super().__del__()

    async def _write(self, command: str) -> None:
        await self.comm._write(f"{self.name}{command}")

    async def _write_read(self, command: str) -> str:
        return await self.comm._write_read(f"{self.name}{command}")

    @property
    async def is_moving(self) -> bool:
        response = await self._write_read("MV")
        return bool(int(response))

    async def wait_for_motion_done(self) -> None:
        while await self.is_moving:
            await asyncio.sleep(0.25)

    # async def read_all_parameters(self) -> list:
    #     command = "PR AL"
    #     self._send_command(command)
    #     await self._check_echo(command)
    #     _ = self.serial.readline()

    #     responses = []
    #     while (line := self.serial.readline().decode("ascii")) != self.TERMCHAR:
    #         responses.append(line.strip("\n").strip("\r"))
    #         await asyncio.sleep(0.005)
    #     self.serial.read_all()
    #     return responses

    async def set_position(self, position: int) -> None:
        assert isinstance(position, int)
        await self._write(f"P={position}")

    async def get_position(self) -> int:
        response = await self._write_read("PR P")
        return int(response)

    async def set_velocity(self, velocity: int) -> None:
        assert isinstance(velocity, int)
        await self._write(f"VM={velocity}")

    async def set_acceleration(self, acceleration: int) -> None:
        assert isinstance(acceleration, int)
        await self._write(f"AC={acceleration}")

    async def move_absolute(self, position: int) -> None:
        assert isinstance(position, int)
        if self.is_moving:
            await self.wait_for_motion_done()
        await self._write(f"MA {position}")

    async def move_relative(self, movement: int) -> None:
        assert isinstance(movement, int)
        if self.is_moving:
            await self.wait_for_motion_done()
        await self._write(f"MR {movement}")

    async def abort_move(self) -> None:
        """Abort the current move command."""
        await self._write("SL 0")

    async def home_negative(self) -> None:
        await self._write("HM 1")
        await self.wait_for_motion_done()

    async def home_positive(self) -> None:
        await self._write("HM 3")
        await self.wait_for_motion_done()


def emergency_stop() -> None:
    """Stop all axes immediately."""
    COMM._write(chr(27))
