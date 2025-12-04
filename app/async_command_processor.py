import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any, Coroutine, Optional

from app.builtin import process_builtin
from app.command import CommandFull, CommandOne
from app.exceptions import NotBuildinError
from app.service_functions import writeln
from app.types import CommandResult, CommandResultAsyncIterator

ProcessCoroutine = Coroutine[Any, Any, asyncio.subprocess.Process]


class ProcessBundle(ABC):
    """ProcessBundle"""

    def __init__(self) -> None:
        super().__init__()
        self.stdout_task: Optional[asyncio.Task[bytes]] = None
        self.stderr_task: Optional[asyncio.Task[bytes]] = None

    def is_stdout(self, task: asyncio.Task[bytes]) -> bool:
        return task == self.stdout_task

    @classmethod
    def from_command(cls, command: CommandOne) -> "ProcessBundle":
        try:
            stdout_str, stderr_str = process_builtin(command)
        except NotBuildinError:
            return ExecProcessBundle(command)
        else:
            return BuiltinProcessBundle(stdout_str, stderr_str)

    @abstractmethod
    async def activate(self) -> None: ...
    @abstractmethod
    async def write_stdin(self, line: bytes) -> None: ...
    @abstractmethod
    async def close_stdin(self) -> None: ...
    @abstractmethod
    def recreate(self, is_stdout: bool) -> asyncio.Task[bytes]: ...


class BuiltinProcessBundle(ProcessBundle):
    def __init__(self, stdout_str: Optional[str], stderr_str: Optional[str]) -> None:
        super().__init__()
        self.stdout_str = stdout_str
        if stdout_str is not None:
            self.stdout_task = asyncio.create_task(asyncio.sleep(0, stdout_str.encode()))
        self.stderr_str = stderr_str
        if stderr_str is not None:
            self.stderr_task = asyncio.create_task(asyncio.sleep(0, stderr_str.encode()))

    async def activate(self) -> None: ...
    async def write_stdin(self, line: bytes) -> None: ...
    async def close_stdin(self) -> None: ...

    def recreate(self, is_stdout: bool) -> asyncio.Task[bytes]:
        task = asyncio.create_task(asyncio.sleep(0, b""))
        if is_stdout:
            self.stdout_task = task
        else:
            self.stderr_task = task
        return task


class ExecProcessBundle(ProcessBundle):
    def __init__(self, command: CommandOne) -> None:
        super().__init__()
        self.coroutine: ProcessCoroutine = asyncio.create_subprocess_shell(
            command.text,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def activate(self) -> None:
        self.process = await self.coroutine
        self.process_task = asyncio.create_task(self.process.wait())
        self.stdout_task = (
            asyncio.create_task(self.process.stdout.readline()) if self.process.stdout else None
        )
        self.stderr_task = (
            asyncio.create_task(self.process.stderr.readline()) if self.process.stderr else None
        )

    def recreate(self, is_stdout: bool) -> asyncio.Task[bytes]:
        if is_stdout:
            if self.process.stdout is None:
                raise NotImplementedError
            self.stdout_task = asyncio.create_task(self.process.stdout.readline())
            return self.stdout_task
        if self.process.stderr is None:
            raise NotImplementedError
        self.stderr_task = asyncio.create_task(self.process.stderr.readline())
        return self.stderr_task

    async def write_stdin(self, line: bytes) -> None:
        if self.process.stdin:
            self.process.stdin.write(line)
            with suppress(ConnectionError):
                await self.process.stdin.drain()

    async def close_stdin(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
            await self.process.stdin.wait_closed()


class ProcessTaskGroup:
    def __init__(self) -> None:
        self.int_to_pb: list[ProcessBundle] = []
        self.pb_to_int: dict[ProcessBundle, int] = dict()
        self.stdout_to_pb: dict[asyncio.Task[bytes], ProcessBundle] = dict()
        self.stderr_to_pb: dict[asyncio.Task[bytes], ProcessBundle] = dict()

    def __len__(self) -> int:
        return len(self.int_to_pb)

    async def add_process(self, command: CommandOne) -> None:
        process_bundle = ProcessBundle.from_command(command)
        await process_bundle.activate()
        index = len(self.int_to_pb)
        self.pb_to_int[process_bundle] = index
        if process_bundle.stdout_task is not None:
            self.stdout_to_pb[process_bundle.stdout_task] = process_bundle
        if process_bundle.stderr_task is not None:
            self.stderr_to_pb[process_bundle.stderr_task] = process_bundle
        self.int_to_pb.append(process_bundle)

    def get_readline_tasks(self) -> set[asyncio.Task[bytes]]:
        result: set[asyncio.Task[bytes]] = set()
        for pb in self.int_to_pb:
            if pb.stdout_task:
                result.add(pb.stdout_task)
            if pb.stderr_task:
                result.add(pb.stderr_task)
        return result

    async def do_the_needful(  # noqa: WPS210
        self, task: asyncio.Task[bytes], result: bytes
    ) -> tuple[Optional[CommandResult], asyncio.Task[bytes]]:
        bundle = self.stdout_to_pb.pop(task, None)
        is_stdout: bool = True
        if bundle is None:
            bundle = self.stderr_to_pb.pop(task, None)
            is_stdout = False
            if bundle is None:
                raise KeyError
        new_task = bundle.recreate(is_stdout)
        if is_stdout:
            self.stdout_to_pb[new_task] = bundle
        else:
            self.stderr_to_pb[new_task] = bundle
        index: int = self.pb_to_int[bundle]
        if index == len(self) - 1:
            if is_stdout:
                to_yield: CommandResult = result.decode(), None
            else:
                to_yield = None, result.decode()
            return to_yield, new_task
        if is_stdout:
            next_bundle: ProcessBundle = self.int_to_pb[index + 1]
            await next_bundle.write_stdin(result)
        else:
            writeln(result.decode(), False, None)
        return None, new_task

    async def close_next_input(self, task: asyncio.Task[bytes]) -> None:
        bundle = self.stdout_to_pb.pop(task, None)
        if bundle is None:
            self.stderr_to_pb.pop(task, None)
            return
        index: int = self.pb_to_int[bundle]
        if index == len(self) - 1:
            return
        next_bundle: ProcessBundle = self.int_to_pb[index + 1]
        await next_bundle.close_stdin()


async def _process_done_task(
    done_task: asyncio.Task[bytes],
    task_group: ProcessTaskGroup,
    readline_tasks: set[asyncio.Task[bytes]],
) -> Optional[CommandResult]:
    if done_task.cancelled() or done_task.exception() is not None:
        raise NotImplementedError
    result = done_task.result()
    if len(result) > 0:
        to_yield, new_task = await task_group.do_the_needful(done_task, result)  # noqa: WPS476
        readline_tasks.add(new_task)
        return to_yield
    await task_group.close_next_input(done_task)
    return None


async def process_full(command_full: CommandFull) -> CommandResultAsyncIterator:  # noqa: WPS210
    task_group = ProcessTaskGroup()
    for command in command_full.commands:
        await task_group.add_process(command)  # noqa: WPS476
    readline_tasks: set[asyncio.Task[bytes]] = task_group.get_readline_tasks()
    while len(readline_tasks) > 0:
        done, readline_tasks = await asyncio.wait(
            readline_tasks, return_when=asyncio.FIRST_COMPLETED
        )
        for done_task in done:
            to_yield = await _process_done_task(  # noqa: WPS476
                done_task, task_group, readline_tasks
            )
            if to_yield:
                yield to_yield
