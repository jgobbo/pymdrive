from serial import Serial
import asyncio
from warnings import warn

__all__ = ["MdriveComm"]

ENCODER = "latin-1"

# TODO add a queue so overlapping calls don't cause an issue


class MdriveComm:
    TERMCHAR = "\r\n"

    def __init__(self, port: str):
        self.serial = Serial(port, baudrate=9600, bytesize=8, stopbits=1, timeout=3)
        self.queue = asyncio.Queue()

    def __del__(self):
        self.serial.close()
        super().__del__()

    def _send_command(self, command: str) -> None:
        self.serial.write(f"{command}{self.TERMCHAR}".encode(ENCODER))
        self.serial.flush()

    async def _check_echo(self, command: str) -> None:
        await asyncio.sleep(0.05)
        line = self.serial.readline()
        command_echo = line.decode(ENCODER).strip(">?\n\r")
        if command_echo != command:
            warn(f"Command echo mismatch: sent '{command}' received '{command_echo}'")

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
        response = self.serial.readline().decode(ENCODER).strip("\n").strip("\r")
        self.serial.read_all()
        return response

    async def _write_read_multiline(self, command: str) -> list:
        self._send_command(command)
        await self._check_echo(command)
        _ = self.serial.readline()

        responses = []
        while (line := self.serial.readline().decode(ENCODER)) != self.TERMCHAR:
            responses.append(line.strip("\n").strip("\r"))
            await asyncio.sleep(0.005)
        self.serial.read_all()
        return responses

    async def reboot(self) -> None:
        await self._write("^C")
