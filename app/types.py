from typing import AsyncIterator, Optional

CommandResult = tuple[Optional[str], Optional[str]]
CommandResultAsyncIterator = AsyncIterator[CommandResult]
