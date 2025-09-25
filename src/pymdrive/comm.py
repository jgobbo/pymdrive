from asyncio import (
    Queue,
    Future,
    create_task,
    wait_for,
    TimeoutError,
    CancelledError,
    sleep,
)
from functools import partial
from warnings import warn
from logging import warning
from typing import Callable

from serial import Serial

__all__ = ["MdriveComm"]

ENCODER = "latin-1"


class MdriveComm:
    running: bool
    TERMCHAR: str = "\r\n"

    def __init__(self, port: str):
        self.serial = Serial(port, baudrate=9600, bytesize=8, stopbits=1, timeout=3)
        self.queue = Queue()
        self.running = False

    def __del__(self):
        if self.serial.is_open:
            self.serial.close()
        super().__del__()

    async def start(self):
        if self.running:
            return

        self.running = True
        self.processor = create_task(self.queue_processor())

    async def stop(self):
        self.running = False
        self.processor.cancel()
        await self.processor

        self.serial.close()

    async def submit(self, task: Callable, timeout: float | None = None):
        """Submit function to queue."""
        future = Future()
        await self.queue.put((task, future))

        if timeout is None:
            return await future
        else:
            try:
                return await wait_for(future, timeout=timeout)
            except TimeoutError:
                future.cancel()
                warn(
                    f"""
Task {task} timed out after {timeout}s.
Possible causes are :
- you didn't start the comm
- the motor is off/disconnected
- you queued too many commands with too short a timeout
                    """
                )
                return None

    async def queue_processor(self):
        while self.running:
            try:
                task: Callable
                future: Future | None
                task, future = await self.queue.get()

                if future is None:
                    await task()
                else:
                    try:
                        result = await task()
                        if not future.cancelled():
                            future.set_result(result)
                    except Exception as e:
                        if not future.cancelled():
                            future.set_exception(e)

                self.queue.task_done()
            except TimeoutError:
                continue
            except CancelledError:
                break

    def _send_command(self, command: str) -> None:
        self.serial.write(f"{command}{self.TERMCHAR}".encode(ENCODER))
        self.serial.flush()

    async def _check_echo(self, command: str) -> None:
        await sleep(0.05)
        command_echo = self.serial.readline().decode("ascii").strip(">?\n\r")
        if command_echo != command:
            warning(
                "Command echo mismatch: "
                f"sent - '{command}', received - '{command_echo}'"
            )

    def synchronous_write(self, command: str) -> None:
        self._send_command(command)
        self.serial.read_until()

    async def _write(self, command: str) -> None:
        self._send_command(command)
        await self._check_echo(command)
        self.serial.read_all()
        return True

    async def write(self, command: str, timeout: float | None = None):
        return await self.submit(partial(self._write, command), timeout)

    async def _write_read(self, command: str) -> str:
        self._send_command(command)
        await self._check_echo(command)
        await sleep(0.1)
        response = self.serial.readline().decode(ENCODER).strip("\n").strip("\r")
        self.serial.read_all()
        return response

    async def write_read(self, command: str, timeout: float | None = None) -> str:
        return await self.submit(partial(self._write_read, command), timeout)

    async def _write_read_multiline(self, command: str) -> list[str]:
        self._send_command(command)
        await self._check_echo(command)
        _ = self.serial.readline()

        responses = []
        while (line := self.serial.readline().decode(ENCODER)) != self.TERMCHAR:
            responses.append(line.strip("\n").strip("\r"))
            await sleep(0.005)
        self.serial.read_all()
        return responses

    async def write_read_multiline(
        self, command: str, timeout: float | None = None
    ) -> list[str]:
        """Write and read commands with multiline responses (e.g. 'PR AL')."""
        return await self.submit(partial(self._write_read_multiline, command), timeout)

    async def reboot(self) -> None:
        await self._write("^C")
