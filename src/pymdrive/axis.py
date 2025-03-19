from serial import Serial
import asyncio
from warnings import warn


class Axis:
    TERMCHAR = "\r\n"

    def __init__(self, port: str):
        self.serial = Serial(port, baudrate=9600, bytesize=8, stopbits=1, timeout=3)

    def __del__(self):
        self.serial.close()

    def _send_command(self, command: str) -> None:
        self.serial.write(f"{command}{self.TERMCHAR}".encode("ascii"))
        self.serial.flush()

    async def _check_echo(self, command: str) -> None:
        await asyncio.sleep(0.05)
        command_echo = self.serial.readline().decode("ascii").strip("\n").strip("\r")
        if command_echo != command:
            warn(f"Command echo mismatch: {command} -> {command_echo}")

    async def _write(self, command: str):
        self._send_command(command)
        await self._check_echo(command)
        self.serial.read_all()

    async def _write_read(self, command: str) -> str:
        self._send_command(command)
        await self._check_echo(command)
        await asyncio.sleep(0.1)
        _ = self.serial.readline()
        response = self.serial.readline().decode("ascii").strip("\n").strip("\r")
        self.serial.read_all()
        return response

    @property
    async def is_moving(self) -> bool:
        response = await self._write_read("MV")
        return bool(int(response))

    async def read_all_parameters(self) -> list:
        command = "PR AL"
        self._send_command(command)
        await self._check_echo(command)
        _ = self.serial.readline()

        responses = []
        while (line := self.serial.readline().decode("ascii")) != self.TERMCHAR:
            responses.append(line.strip("\n").strip("\r"))
            await asyncio.sleep(0.005)
        self.serial.read_all()
        return responses

    async def set_position(self, position: int) -> None:
        assert isinstance(position, int)
        self._write(f"P={position}")

    async def set_velocity(self, velocity: int) -> None:
        assert isinstance(velocity, int)
        self._write(f"VM={velocity}")

    async def set_acceleration(self, acceleration: int) -> None:
        assert isinstance(acceleration, int)
        self._write(f"AC={acceleration}")

    async def move_absolute(self, position: int) -> None:
        assert isinstance(position, int)
        self._write(f"MA {position}")

    async def move_relative(self, movement: int) -> None:
        assert isinstance(movement, int)
        self._write(f"MR {movement}")

    async def home_negative(self) -> None:
        self._write("HM 1")

    async def home_positive(self) -> None:
        self._write("HM 3")
