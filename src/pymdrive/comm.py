from serial import Serial
import asyncio
from warnings import warn


class MdriveComm:
    TERMCHAR = "\r\n"

    def __init__(self, port: str):
        self.serial = Serial(port, baudrate=9600, bytesize=8, stopbits=1, timeout=3)

    def __del__(self):
        self.serial.close()
        super().__del__()

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
        response = self.serial.readline().decode("ascii").strip("\n").strip("\r")
        self.serial.read_all()
        return response

    async def reboot(self) -> None:
        await self._write("^C")
