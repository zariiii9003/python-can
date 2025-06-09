"""Contains generic base classes for file IO."""

import locale
import os
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import AbstractContextManager
from io import BufferedIOBase, TextIOWrapper
from pathlib import Path
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generic,
    Literal,
    Optional,
    TextIO,
    TypeVar,
    Union,
)

from typing_extensions import Self

from ..listener import Listener
from ..message import Message
from ..typechecking import FileLike, StringPathLike

if TYPE_CHECKING:
    from _typeshed import (
        OpenBinaryModeReading,
        OpenBinaryModeUpdating,
        OpenBinaryModeWriting,
        OpenTextModeReading,
        OpenTextModeUpdating,
        OpenTextModeWriting,
    )


_IoTypeVar = TypeVar("_IoTypeVar", bound=FileLike)


class MessageWriter(AbstractContextManager["MessageWriter"], Listener, ABC):
    """The base class for all writers."""

    @abstractmethod
    def __init__(self, file: StringPathLike, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.stop()
        return False


class SizedMessageWriter(MessageWriter, ABC):
    @abstractmethod
    def file_size(self) -> int:
        pass


class FileIOMessageWriter(SizedMessageWriter, Generic[_IoTypeVar]):
    """A specialized base class for all writers with file descriptors."""

    file: _IoTypeVar

    @abstractmethod
    def __init__(self, file: Union[StringPathLike, _IoTypeVar], **kwargs: Any) -> None:
        pass

    def stop(self) -> None:
        self.file.close()

    def file_size(self) -> int:
        return self.file.tell()


class TextIOMessageWriter(FileIOMessageWriter[Union[TextIO, TextIOWrapper]], ABC):
    def __init__(
        self,
        file: Union[StringPathLike, TextIO, TextIOWrapper],
        mode: "Union[OpenTextModeUpdating, OpenTextModeWriting]" = "w",
        **kwargs: Any,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            encoding: str = kwargs.get("encoding", locale.getpreferredencoding(False))
            # pylint: disable=consider-using-with
            self.file = Path(file).open(mode=mode, encoding=encoding)
        else:
            self.file = file


class BinaryIOMessageWriter(FileIOMessageWriter[Union[BinaryIO, BufferedIOBase]], ABC):
    def __init__(
        self,
        file: Union[StringPathLike, BinaryIO, BufferedIOBase],
        mode: "Union[OpenBinaryModeUpdating, OpenBinaryModeWriting]" = "wb",
        **kwargs: Any,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            # pylint: disable=consider-using-with,unspecified-encoding
            self.file = Path(file).open(mode=mode)
        else:
            self.file = file


class MessageReader(AbstractContextManager["MessageReader"], Iterable[Message], ABC):
    """The base class for all readers."""

    @abstractmethod
    def __init__(self, file: StringPathLike, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.stop()
        return False


class FileIOMessageReader(MessageReader, Generic[_IoTypeVar]):
    """A specialized base class for all readers with file descriptors."""

    file: _IoTypeVar

    @abstractmethod
    def __init__(self, file: Union[StringPathLike, _IoTypeVar], **kwargs: Any) -> None:
        pass

    def stop(self) -> None:
        self.file.close()


class TextIOMessageReader(FileIOMessageReader[Union[TextIO, TextIOWrapper]], ABC):
    def __init__(
        self,
        file: Union[StringPathLike, TextIO, TextIOWrapper],
        mode: "OpenTextModeReading" = "r",
        **kwargs: Any,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            encoding: str = kwargs.get("encoding", locale.getpreferredencoding(False))
            # pylint: disable=consider-using-with
            self.file = Path(file).open(mode=mode, encoding=encoding)
        else:
            self.file = file


class BinaryIOMessageReader(FileIOMessageReader[Union[BinaryIO, BufferedIOBase]], ABC):
    def __init__(
        self,
        file: Union[StringPathLike, BinaryIO, BufferedIOBase],
        mode: "OpenBinaryModeReading" = "rb",
        **kwargs: Any,
    ) -> None:
        if isinstance(file, (str, os.PathLike)):
            # pylint: disable=consider-using-with,unspecified-encoding
            self.file = Path(file).open(mode=mode)
        else:
            self.file = file
