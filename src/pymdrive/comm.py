from serial import Serial
import asyncio
from warnings import warn

__all__ = ["MdriveComm"]


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
        command_echo = self.serial.readline().decode("ascii").strip(">?\n\r")
        if command_echo != command:
            warn(f"Command echo mismatch: {command} -> {command_echo}")

    def _synchronous_write(self, command: str):
        self._send_command(command)
        self.serial.read_until()

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

    async def _write_read_multiline(self, command: str) -> list:
        self._send_command(command)
        await self._check_echo(command)
        _ = self.serial.readline()

        responses = []
        while (line := self.serial.readline().decode("ascii")) != self.TERMCHAR:
            responses.append(line.strip("\n").strip("\r"))
            await asyncio.sleep(0.005)
        self.serial.read_all()
        return responses

    async def reboot(self) -> None:
        await self._write("^C")
