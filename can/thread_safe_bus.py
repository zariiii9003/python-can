from contextlib import nullcontext
from threading import RLock
from typing import TYPE_CHECKING, Any, Optional, cast

from wrapt import ObjectProxy

from can import typechecking
from can.bus import BusABC, BusState, CanProtocol
from can.message import Message

from .interface import Bus

if TYPE_CHECKING:
    from threading import Lock


class ThreadSafeBus(ObjectProxy):  # type: ignore[misc]  # pylint: disable=abstract-method
    """
    Contains a thread safe :class:`can.BusABC` implementation that
    wraps around an existing interface instance. All public methods
    of that base class are now safe to be called from multiple threads.
    The send and receive methods are synchronized separately.

    Use this as a drop-in replacement for :class:`~can.BusABC`.

    .. note::

        This approach assumes that both :meth:`~can.BusABC.send` and
        :meth:`~can.BusABC._recv_internal` of the underlying bus instance can be
        called simultaneously, and that the methods use :meth:`~can.BusABC._recv_internal`
        instead of :meth:`~can.BusABC.recv` directly.
    """

    __wrapped__: BusABC

    def __init__(
        self,
        channel: Optional[typechecking.Channel] = None,
        interface: Optional[str] = None,
        config_context: Optional[str] = None,
        ignore_config: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            Bus(
                channel=channel,
                interface=interface,
                config_context=config_context,
                ignore_config=ignore_config,
                **kwargs,
            )
        )

        # now, BusABC.send_periodic() does not need a lock anymore, but the
        # implementation still requires a context manager
        self.__wrapped__._lock_send_periodic = cast("Lock", nullcontext())

        # init locks for sending and receiving separately
        self._lock_send = RLock()
        self._lock_recv = RLock()

    def recv(self, timeout: Optional[float] = None) -> Optional[Message]:
        with self._lock_recv:
            return self.__wrapped__.recv(timeout=timeout)

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        with self._lock_send:
            return self.__wrapped__.send(msg=msg, timeout=timeout)

    # send_periodic does not need a lock, since the underlying
    # `send` method is already synchronized

    @property
    def filters(self) -> Optional[typechecking.CanFilters]:
        with self._lock_recv:
            return self.__wrapped__.filters

    @filters.setter
    def filters(self, filters: Optional[typechecking.CanFilters]) -> None:
        with self._lock_recv:
            self.__wrapped__.filters = filters

    def set_filters(self, filters: Optional[typechecking.CanFilters] = None) -> None:
        with self._lock_recv:
            return self.__wrapped__.set_filters(filters=filters)

    def flush_tx_buffer(self) -> None:
        with self._lock_send:
            return self.__wrapped__.flush_tx_buffer()

    def shutdown(self) -> None:
        with self._lock_send, self._lock_recv:
            return self.__wrapped__.shutdown()

    @property
    def state(self) -> BusState:
        with self._lock_send, self._lock_recv:
            return self.__wrapped__.state

    @state.setter
    def state(self, new_state: BusState) -> None:
        with self._lock_send, self._lock_recv:
            self.__wrapped__.state = new_state

    @property
    def protocol(self) -> CanProtocol:
        with self._lock_send, self._lock_recv:
            return self.__wrapped__.protocol
