import logging
import os
import sys
from ctypes import byref
from ctypes import c_wchar_p as LPWSTR

from can.exceptions import CanInterfaceNotImplementedError

from . import constants, exceptions, structures

log = logging.getLogger("can.systec")


def check_valid_rx_can_msg(result):
    """
    Checks if function :meth:`UcanServer.read_can_msg` returns a valid CAN message.

    :param ReturnCode result: Error code of the function.
    :return: True if a valid CAN messages was received, otherwise False.
    :rtype: bool
    """
    return (result.value == exceptions.ReturnCode.SUCCESSFUL) or (
        result.value > exceptions.ReturnCode.WARNING
    )


def check_tx_ok(result):
    """
    Checks if function :meth:`UcanServer.write_can_msg` successfully wrote CAN message(s).

    While using :meth:`UcanServer.write_can_msg_ex` the number of sent CAN messages can be less than
    the number of CAN messages which should be sent.

    :param ReturnCode result: Error code of the function.
    :return: True if CAN message(s) was(were) written successfully, otherwise False.
    :rtype: bool

    .. :seealso: :const:`exceptions.ReturnCode.WARN_TXLIMIT`
    """
    return (result.value == exceptions.ReturnCode.SUCCESSFUL) or (
        result.value > exceptions.ReturnCode.WARNING
    )


def check_tx_success(result):
    """
    Checks if function :meth:`UcanServer.write_can_msg_ex` successfully wrote all CAN message(s).

    :param ReturnCode result: Error code of the function.
    :return: True if CAN message(s) was(were) written successfully, otherwise False.
    :rtype: bool
    """
    return result.value == exceptions.ReturnCode.SUCCESSFUL


def check_tx_not_all(result):
    """
    Checks if function :meth:`UcanServer.write_can_msg_ex` did not sent all CAN messages.

    :param ReturnCode result: Error code of the function.
    :return: True if not all CAN messages were written, otherwise False.
    :rtype: bool
    """
    return result.value == exceptions.ReturnCode.WARN_TXLIMIT


def check_warning(result):
    """
    Checks if any function returns a warning.

    :param ReturnCode result: Error code of the function.
    :return: True if a function returned warning, otherwise False.
    :rtype: bool
    """
    return result.value >= exceptions.ReturnCode.WARNING


def check_error(result):
    """
    Checks if any function returns an error from USB-CAN-library.

    :param ReturnCode result: Error code of the function.
    :return: True if a function returned error, otherwise False.
    :rtype: bool
    """
    return (result.value != exceptions.ReturnCode.SUCCESSFUL) and (
        result.value < exceptions.ReturnCode.WARNING
    )


def check_error_cmd(result):
    """
    Checks if any function returns an error from firmware in USB-CANmodul.

    :param ReturnCode result: Error code of the function.
    :return: True if a function returned error from firmware, otherwise False.
    :rtype: bool
    """
    return (result.value >= exceptions.ReturnCode.ERRCMD) and (
        result.value < exceptions.ReturnCode.WARNING
    )


def check_result(result, func, arguments):
    if check_warning(result) and (result.value != exceptions.ReturnCode.WARN_NODATA):
        log.warning(exceptions.UcanWarning(result, func, arguments))
    elif check_error(result):
        if check_error_cmd(result):
            raise exceptions.UcanCmdError(result, func, arguments)
        else:
            raise exceptions.UcanError(result, func, arguments)
    return result


_UCAN_INITIALIZED = False
if os.name != "nt":
    log.warning("SYSTEC ucan library does not work on %s platform.", sys.platform)
else:
    from ctypes import WinDLL

    try:
        # Select the proper dll architecture
        lib = WinDLL("usbcan64.dll" if sys.maxsize > 2**32 else "usbcan32.dll")

        # BOOL PUBLIC UcanSetDebugMode (DWORD dwDbgLevel_p, _TCHAR* pszFilePathName_p, DWORD dwFlags_p);
        UcanSetDebugMode = lib.UcanSetDebugMode
        UcanSetDebugMode.restype = structures.BOOL
        UcanSetDebugMode.argtypes = [structures.DWORD, LPWSTR, structures.DWORD]

        # DWORD PUBLIC UcanGetVersionEx (VersionType VerType_p);
        UcanGetVersionEx = lib.UcanGetVersionEx
        UcanGetVersionEx.restype = structures.DWORD
        UcanGetVersionEx.argtypes = [constants.VersionType]

        # DWORD PUBLIC UcanGetFwVersion (Handle UcanHandle_p);
        UcanGetFwVersion = lib.UcanGetFwVersion
        UcanGetFwVersion.restype = structures.DWORD
        UcanGetFwVersion.argtypes = [structures.Handle]

        # BYTE PUBLIC UcanInitHwConnectControlEx (ConnectControlFktEx fpConnectControlFktEx_p, void* pCallbackArg_p);
        UcanInitHwConnectControlEx = lib.UcanInitHwConnectControlEx
        UcanInitHwConnectControlEx.restype = exceptions.ReturnCode
        UcanInitHwConnectControlEx.argtypes = [
            structures.ConnectControlFktEx,
            structures.LPVOID,
        ]
        UcanInitHwConnectControlEx.errcheck = check_result

        # BYTE PUBLIC UcanDeinitHwConnectControl (void)
        UcanDeinitHwConnectControl = lib.UcanDeinitHwConnectControl
        UcanDeinitHwConnectControl.restype = exceptions.ReturnCode
        UcanDeinitHwConnectControl.argtypes = []
        UcanDeinitHwConnectControl.errcheck = check_result

        # DWORD PUBLIC UcanEnumerateHardware (EnumCallback fpCallback_p, void* pCallbackArg_p,
        #    BOOL  fEnumUsedDevs_p,
        #    BYTE  bDeviceNrLow_p,     BYTE  bDeviceNrHigh_p,
        #    DWORD dwSerialNrLow_p,    DWORD dwSerialNrHigh_p,
        #    DWORD dwProductCodeLow_p, DWORD dwProductCodeHigh_p);
        UcanEnumerateHardware = lib.UcanEnumerateHardware
        UcanEnumerateHardware.restype = structures.DWORD
        UcanEnumerateHardware.argtypes = [
            structures.EnumCallback,
            structures.LPVOID,
            structures.BOOL,
            structures.BYTE,
            structures.BYTE,
            structures.DWORD,
            structures.DWORD,
            structures.DWORD,
            structures.DWORD,
        ]

        # BYTE PUBLIC UcanInitHardwareEx (Handle* pUcanHandle_p, BYTE bDeviceNr_p,
        #   CallbackFktEx fpCallbackFktEx_p, void* pCallbackArg_p);
        UcanInitHardwareEx = lib.UcanInitHardwareEx
        UcanInitHardwareEx.restype = exceptions.ReturnCode
        UcanInitHardwareEx.argtypes = [
            structures.POINTER(structures.Handle),
            structures.BYTE,
            structures.CallbackFktEx,
            structures.LPVOID,
        ]
        UcanInitHardwareEx.errcheck = check_result

        # BYTE PUBLIC UcanInitHardwareEx2 (Handle* pUcanHandle_p, DWORD dwSerialNr_p,
        #   CallbackFktEx fpCallbackFktEx_p, void* pCallbackArg_p);
        UcanInitHardwareEx2 = lib.UcanInitHardwareEx2
        UcanInitHardwareEx2.restype = exceptions.ReturnCode
        UcanInitHardwareEx2.argtypes = [
            structures.POINTER(structures.Handle),
            structures.DWORD,
            structures.CallbackFktEx,
            structures.LPVOID,
        ]
        UcanInitHardwareEx2.errcheck = check_result

        # BYTE PUBLIC UcanGetModuleTime (Handle UcanHandle_p, DWORD* pdwTime_p);
        UcanGetModuleTime = lib.UcanGetModuleTime
        UcanGetModuleTime.restype = exceptions.ReturnCode
        UcanGetModuleTime.argtypes = [
            structures.Handle,
            structures.POINTER(structures.DWORD),
        ]
        UcanGetModuleTime.errcheck = check_result

        # BYTE PUBLIC UcanGetHardwareInfoEx2 (Handle UcanHandle_p,
        #   HardwareInfoEx* pHwInfo_p,
        #   ChannelInfo* pCanInfoCh0_p, ChannelInfo* pCanInfoCh1_p);
        UcanGetHardwareInfoEx2 = lib.UcanGetHardwareInfoEx2
        UcanGetHardwareInfoEx2.restype = exceptions.ReturnCode
        UcanGetHardwareInfoEx2.argtypes = [
            structures.Handle,
            structures.POINTER(structures.HardwareInfoEx),
            structures.POINTER(structures.ChannelInfo),
            structures.POINTER(structures.ChannelInfo),
        ]
        UcanGetHardwareInfoEx2.errcheck = check_result

        # BYTE PUBLIC UcanInitCanEx2 (Handle UcanHandle_p, BYTE bChannel_p, tUcaninit_canParam* pinit_canParam_p);
        UcanInitCanEx2 = lib.UcanInitCanEx2
        UcanInitCanEx2.restype = exceptions.ReturnCode
        UcanInitCanEx2.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.InitCanParam),
        ]
        UcanInitCanEx2.errcheck = check_result

        # BYTE PUBLIC UcanSetBaudrateEx (Handle UcanHandle_p,
        #   BYTE bChannel_p, BYTE bBTR0_p, BYTE bBTR1_p, DWORD dwBaudrate_p);
        UcanSetBaudrateEx = lib.UcanSetBaudrateEx
        UcanSetBaudrateEx.restype = exceptions.ReturnCode
        UcanSetBaudrateEx.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.BYTE,
            structures.BYTE,
            structures.DWORD,
        ]
        UcanSetBaudrateEx.errcheck = check_result

        # BYTE PUBLIC UcanSetAcceptanceEx (Handle UcanHandle_p, BYTE bChannel_p,
        #   DWORD dwAMR_p, DWORD dwACR_p);
        UcanSetAcceptanceEx = lib.UcanSetAcceptanceEx
        UcanSetAcceptanceEx.restype = exceptions.ReturnCode
        UcanSetAcceptanceEx.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.DWORD,
            structures.DWORD,
        ]
        UcanSetAcceptanceEx.errcheck = check_result

        # BYTE PUBLIC UcanResetCanEx (Handle UcanHandle_p, BYTE bChannel_p, DWORD dwResetFlags_p);
        UcanResetCanEx = lib.UcanResetCanEx
        UcanResetCanEx.restype = exceptions.ReturnCode
        UcanResetCanEx.argtypes = [structures.Handle, structures.BYTE, structures.DWORD]
        UcanResetCanEx.errcheck = check_result

        # BYTE PUBLIC UcanReadCanMsgEx (Handle UcanHandle_p, BYTE* pbChannel_p,
        #   CanMsg* pCanMsg_p, DWORD* pdwCount_p);
        UcanReadCanMsgEx = lib.UcanReadCanMsgEx
        UcanReadCanMsgEx.restype = exceptions.ReturnCode
        UcanReadCanMsgEx.argtypes = [
            structures.Handle,
            structures.POINTER(structures.BYTE),
            structures.POINTER(structures.CanMsg),
            structures.POINTER(structures.DWORD),
        ]
        UcanReadCanMsgEx.errcheck = check_result

        # BYTE PUBLIC UcanWriteCanMsgEx (Handle UcanHandle_p, BYTE bChannel_p,
        #   CanMsg* pCanMsg_p, DWORD* pdwCount_p);
        UcanWriteCanMsgEx = lib.UcanWriteCanMsgEx
        UcanWriteCanMsgEx.restype = exceptions.ReturnCode
        UcanWriteCanMsgEx.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.CanMsg),
            structures.POINTER(structures.DWORD),
        ]
        UcanWriteCanMsgEx.errcheck = check_result

        # BYTE PUBLIC UcanGetStatusEx (Handle UcanHandle_p, BYTE bChannel_p, Status* pStatus_p);
        UcanGetStatusEx = lib.UcanGetStatusEx
        UcanGetStatusEx.restype = exceptions.ReturnCode
        UcanGetStatusEx.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.Status),
        ]
        UcanGetStatusEx.errcheck = check_result

        # BYTE PUBLIC UcanGetMsgCountInfoEx (Handle UcanHandle_p, BYTE bChannel_p,
        #   MsgCountInfo* pMsgCountInfo_p);
        UcanGetMsgCountInfoEx = lib.UcanGetMsgCountInfoEx
        UcanGetMsgCountInfoEx.restype = exceptions.ReturnCode
        UcanGetMsgCountInfoEx.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.MsgCountInfo),
        ]
        UcanGetMsgCountInfoEx.errcheck = check_result

        # BYTE PUBLIC UcanGetMsgPending (Handle UcanHandle_p,
        #   BYTE bChannel_p, DWORD dwFlags_p, DWORD* pdwPendingCount_p);
        UcanGetMsgPending = lib.UcanGetMsgPending
        UcanGetMsgPending.restype = exceptions.ReturnCode
        UcanGetMsgPending.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.DWORD,
            structures.POINTER(structures.DWORD),
        ]
        UcanGetMsgPending.errcheck = check_result

        # BYTE PUBLIC UcanGetCanErrorCounter (Handle UcanHandle_p,
        #   BYTE bChannel_p, DWORD* pdwTxErrorCounter_p, DWORD* pdwRxErrorCounter_p);
        UcanGetCanErrorCounter = lib.UcanGetCanErrorCounter
        UcanGetCanErrorCounter.restype = exceptions.ReturnCode
        UcanGetCanErrorCounter.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.DWORD),
            structures.POINTER(structures.DWORD),
        ]
        UcanGetCanErrorCounter.errcheck = check_result

        # BYTE PUBLIC UcanSetTxTimeout (Handle UcanHandle_p,
        #   BYTE bChannel_p, DWORD dwTxTimeout_p);
        UcanSetTxTimeout = lib.UcanSetTxTimeout
        UcanSetTxTimeout.restype = exceptions.ReturnCode
        UcanSetTxTimeout.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.DWORD,
        ]
        UcanSetTxTimeout.errcheck = check_result

        # BYTE PUBLIC UcanDeinitCanEx (Handle UcanHandle_p, BYTE bChannel_p);
        UcanDeinitCanEx = lib.UcanDeinitCanEx
        UcanDeinitCanEx.restype = exceptions.ReturnCode
        UcanDeinitCanEx.argtypes = [structures.Handle, structures.BYTE]
        UcanDeinitCanEx.errcheck = check_result

        # BYTE PUBLIC UcanDeinitHardware (Handle UcanHandle_p);
        UcanDeinitHardware = lib.UcanDeinitHardware
        UcanDeinitHardware.restype = exceptions.ReturnCode
        UcanDeinitHardware.argtypes = [structures.Handle]
        UcanDeinitHardware.errcheck = check_result

        # BYTE PUBLIC UcanDefineCyclicCanMsg (Handle UcanHandle_p,
        #   BYTE bChannel_p, CanMsg* pCanMsgList_p, DWORD dwCount_p);
        UcanDefineCyclicCanMsg = lib.UcanDefineCyclicCanMsg
        UcanDefineCyclicCanMsg.restype = exceptions.ReturnCode
        UcanDefineCyclicCanMsg.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.CanMsg),
            structures.DWORD,
        ]
        UcanDefineCyclicCanMsg.errcheck = check_result

        # BYTE PUBLIC UcanReadCyclicCanMsg (Handle UcanHandle_p,
        #   BYTE bChannel_p, CanMsg* pCanMsgList_p, DWORD* pdwCount_p);
        UcanReadCyclicCanMsg = lib.UcanReadCyclicCanMsg
        UcanReadCyclicCanMsg.restype = exceptions.ReturnCode
        UcanReadCyclicCanMsg.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.POINTER(structures.CanMsg),
            structures.POINTER(structures.DWORD),
        ]
        UcanReadCyclicCanMsg.errcheck = check_result

        # BYTE PUBLIC UcanEnableCyclicCanMsg (Handle UcanHandle_p,
        #   BYTE bChannel_p, DWORD dwFlags_p);
        UcanEnableCyclicCanMsg = lib.UcanEnableCyclicCanMsg
        UcanEnableCyclicCanMsg.restype = exceptions.ReturnCode
        UcanEnableCyclicCanMsg.argtypes = [
            structures.Handle,
            structures.BYTE,
            structures.DWORD,
        ]
        UcanEnableCyclicCanMsg.errcheck = check_result

        _UCAN_INITIALIZED = True

    except Exception as ex:
        log.warning("Cannot load SYSTEC ucan library: %s.", ex)


class UcanServer:
    """
    UcanServer is a Python wrapper class for using the usbcan32.dll / usbcan64.dll.
    """

    _modules_found = []
    _connect_control_ref = None

    def __init__(self):
        if not _UCAN_INITIALIZED:
            raise CanInterfaceNotImplementedError(
                "The interface could not be loaded on the current platform"
            )

        self._handle = structures.Handle(constants.INVALID_HANDLE)
        self._is_initialized = False
        self._hw_is_initialized = False
        self._ch_is_initialized = {
            constants.Channel.CHANNEL_CH0: False,
            constants.Channel.CHANNEL_CH1: False,
        }
        self._callback_ref = structures.CallbackFktEx(self._callback)
        if self._connect_control_ref is None:
            self._connect_control_ref = structures.ConnectControlFktEx(
                self._connect_control
            )
            UcanInitHwConnectControlEx(self._connect_control_ref, None)

    @property
    def is_initialized(self):
        """
        Returns whether hardware interface is initialized.

        :return: True if initialized, otherwise False.
        :rtype: bool
        """
        return self._is_initialized

    @property
    def is_can0_initialized(self):
        """
        Returns whether CAN interface for channel 0 is initialized.

        :return: True if initialized, otherwise False.
        :rtype: bool
        """
        return self._ch_is_initialized[constants.Channel.CHANNEL_CH0]

    @property
    def is_can1_initialized(self):
        """
        Returns whether CAN interface for channel 1 is initialized.

        :return: True if initialized, otherwise False.
        :rtype: bool
        """
        return self._ch_is_initialized[constants.Channel.CHANNEL_CH1]

    @classmethod
    def _enum_callback(cls, index, is_used, hw_info_ex, init_info, arg):
        cls._modules_found.append(
            (index, structures.BOOL(is_used), hw_info_ex.contents, init_info.contents)
        )

    @classmethod
    def enumerate_hardware(
        cls,
        device_number_low=0,
        device_number_high=-1,
        serial_low=0,
        serial_high=-1,
        product_code_low=0,
        product_code_high=-1,
        enum_used_devices=False,
    ):
        cls._modules_found = []
        UcanEnumerateHardware(
            cls._enum_callback_ref,
            None,
            enum_used_devices,
            device_number_low,
            device_number_high,
            serial_low,
            serial_high,
            product_code_low,
            product_code_high,
        )
        return cls._modules_found

    def init_hardware(self, serial=None, device_number=constants.ANY_MODULE):
        """
        Initializes the device with the corresponding serial or device number.

        :param int or None serial: Serial number of the USB-CANmodul.
        :param int device_number: Device number (0 – 254, or :const:`ANY_MODULE` for the first device).
        """
        if not self._hw_is_initialized:
            # initialize hardware either by device number or serial
            if serial is None:
                UcanInitHardwareEx(
                    byref(self._handle), device_number, self._callback_ref, None
                )
            else:
                UcanInitHardwareEx2(
                    byref(self._handle), serial, self._callback_ref, None
                )
            self._hw_is_initialized = True

    def init_can(
        self,
        channel=constants.Channel.CHANNEL_CH0,
        BTR=constants.Baudrate.BAUD_1MBit,
        baudrate=constants.BaudrateEx.BAUDEX_USE_BTR01,
        AMR=constants.AMR_ALL,
        ACR=constants.ACR_ALL,
        mode=constants.Mode.MODE_NORMAL,
        OCR=constants.OutputControl.OCR_DEFAULT,
        rx_buffer_entries=constants.DEFAULT_BUFFER_ENTRIES,
        tx_buffer_entries=constants.DEFAULT_BUFFER_ENTRIES,
    ):
        """
        Initializes a specific CAN channel of a device.

        :param int channel: CAN channel to be initialized (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int BTR:
            Baud rate register BTR0 as high byte, baud rate register BTR1 as low byte (see enum :class:`Baudrate`).
        :param int baudrate: Baud rate register for all systec USB-CANmoduls (see enum :class:`BaudrateEx`).
        :param int AMR: Acceptance filter mask (see method :meth:`set_acceptance`).
        :param int ACR: Acceptance filter code (see method :meth:`set_acceptance`).
        :param int mode: Transmission mode of CAN channel (see enum :class:`Mode`).
        :param int OCR: Output Control Register (see enum :class:`OutputControl`).
        :param int rx_buffer_entries: The number of maximum entries in the receive buffer.
        :param int tx_buffer_entries: The number of maximum entries in the transmit buffer.
        """
        if not self._ch_is_initialized.get(channel, False):
            init_param = structures.InitCanParam(
                mode, BTR, OCR, AMR, ACR, baudrate, rx_buffer_entries, tx_buffer_entries
            )
            UcanInitCanEx2(self._handle, channel, init_param)
            self._ch_is_initialized[channel] = True

    def read_can_msg(self, channel, count):
        """
        Reads one or more CAN-messages from the buffer of the specified CAN channel.

        :param int channel:
            CAN channel to read from (:data:`Channel.CHANNEL_CH0`, :data:`Channel.CHANNEL_CH1`,
            :data:`Channel.CHANNEL_ANY`).
        :param int count: The number of CAN messages to be received.
        :return: Tuple with list of CAN message/s received and the CAN channel where the read CAN messages came from.
        :rtype: tuple(list(CanMsg), int)
        """
        c_channel = structures.BYTE(channel)
        c_can_msg = (structures.CanMsg * count)()
        c_count = structures.DWORD(count)
        UcanReadCanMsgEx(self._handle, byref(c_channel), c_can_msg, byref(c_count))
        return c_can_msg[: c_count.value], c_channel.value

    def write_can_msg(self, channel, can_msg):
        """
        Transmits one ore more CAN messages through the specified CAN channel of the device.

        :param int channel:
            CAN channel, which is to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param list(CanMsg) can_msg: List of CAN message structure (see structure :class:`CanMsg`).
        :return: The number of successfully transmitted CAN messages.
        :rtype: int
        """
        c_can_msg = (structures.CanMsg * len(can_msg))(*can_msg)
        c_count = structures.DWORD(len(can_msg))
        UcanWriteCanMsgEx(self._handle, channel, c_can_msg, c_count)
        return c_count

    def set_baudrate(self, channel, BTR, baudarate):
        """
        This function is used to configure the baud rate of specific CAN channel of a device.

        :param int channel:
            CAN channel, which is to be configured (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int BTR:
            Baud rate register BTR0 as high byte, baud rate register BTR1 as low byte (see enum :class:`Baudrate`).
        :param int baudarate: Baud rate register for all systec USB-CANmoduls (see enum :class:`BaudrateEx`>).
        """
        UcanSetBaudrateEx(self._handle, channel, BTR >> 8, BTR, baudarate)

    def set_acceptance(
        self,
        channel=constants.Channel.CHANNEL_CH0,
        AMR=constants.AMR_ALL,
        ACR=constants.ACR_ALL,
    ):
        """
        This function is used to change the acceptance filter values for a specific CAN channel on a device.

        :param int channel:
            CAN channel, which is to be configured (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int AMR: Acceptance filter mask (AMR).
        :param int ACR: Acceptance filter code (ACR).
        """
        UcanSetAcceptanceEx(self._handle, channel, AMR, ACR)

    def get_status(self, channel=constants.Channel.CHANNEL_CH0):
        """
        Returns the error status of a specific CAN channel.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :return: Tuple with CAN and USB status (see structure :class:`Status`).
        :rtype: tuple(int, int)
        """
        status = structures.Status()
        UcanGetStatusEx(self._handle, channel, byref(status))
        return status.can_status, status.usb_status

    def get_msg_count_info(self, channel=constants.Channel.CHANNEL_CH0):
        """
        Reads the message counters of the specified CAN channel.

        :param int channel:
            CAN channel, which is to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :return: Tuple with number of CAN messages sent and received.
        :rtype: tuple(int, int)
        """
        msg_count_info = structures.MsgCountInfo()
        UcanGetMsgCountInfoEx(self._handle, channel, byref(msg_count_info))
        return msg_count_info.sent_msg_count, msg_count_info.recv_msg_count

    def reset_can(
        self,
        channel=constants.Channel.CHANNEL_CH0,
        flags=constants.ResetFlags.RESET_ALL,
    ):
        """
        Resets a CAN channel of a device (hardware reset, empty buffer, and so on).

        :param int channel: CAN channel, to be reset (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int flags: Flags defines what should be reset (see enum :class:`ResetFlags`).
        """
        UcanResetCanEx(self._handle, channel, flags)

    def get_hardware_info(self):
        """
        Returns the extended hardware information of a device. With multi-channel USB-CANmoduls the information for
        both CAN channels are returned separately.

        :return:
            Tuple with extended hardware information structure (see structure :class:`HardwareInfoEx`) and
            structures with information of CAN channel 0 and 1 (see structure :class:`ChannelInfo`).
        :rtype: tuple(HardwareInfoEx, ChannelInfo, ChannelInfo)
        """
        hw_info_ex = structures.HardwareInfoEx()
        can_info_ch0, can_info_ch1 = structures.ChannelInfo(), structures.ChannelInfo()
        UcanGetHardwareInfoEx2(
            self._handle, byref(hw_info_ex), byref(can_info_ch0), byref(can_info_ch1)
        )
        return hw_info_ex, can_info_ch0, can_info_ch1

    def get_fw_version(self):
        """
        Returns the firmware version number of the device.

        :return: Firmware version number.
        :rtype: int
        """
        return UcanGetFwVersion(self._handle)

    def define_cyclic_can_msg(self, channel, can_msg=None):
        """
        Defines a list of CAN messages for automatic transmission.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param list(CanMsg) can_msg:
            List of CAN messages (up to 16, see structure :class:`CanMsg`), or None to delete an older list.
        """
        if can_msg is not None:
            c_can_msg = (structures.CanMsg * len(can_msg))(*can_msg)
            c_count = structures.DWORD(len(can_msg))
        else:
            c_can_msg = structures.CanMsg()
            c_count = 0
        UcanDefineCyclicCanMsg(self._handle, channel, c_can_msg, c_count)

    def read_cyclic_can_msg(self, channel, count):
        """
        Reads back the list of CAN messages for automatically sending.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int count: The number of cyclic CAN messages to be received.
        :return: List of received CAN messages (up to 16, see structure :class:`CanMsg`).
        :rtype: list(CanMsg)
        """
        c_channel = structures.BYTE(channel)
        c_can_msg = (structures.CanMsg * count)()
        c_count = structures.DWORD(count)
        UcanReadCyclicCanMsg(self._handle, byref(c_channel), c_can_msg, c_count)
        return c_can_msg[: c_count.value]

    def enable_cyclic_can_msg(self, channel, flags):
        """
        Enables or disables the automatically sending.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int flags: Flags for enabling or disabling (see enum :class:`CyclicFlags`).
        """
        UcanEnableCyclicCanMsg(self._handle, channel, flags)

    def get_msg_pending(self, channel, flags):
        """
        Returns the number of pending CAN messages.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param int flags: Flags specifies which buffers should be checked (see enum :class:`PendingFlags`).
        :return: The number of pending messages.
        :rtype: int
        """
        count = structures.DWORD(0)
        UcanGetMsgPending(self._handle, channel, flags, byref(count))
        return count.value

    def get_can_error_counter(self, channel):
        """
        Reads the current value of the error counters within the CAN controller.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :return: Tuple with the TX and RX error counter.
        :rtype: tuple(int, int)

        .. note:: Only available for systec USB-CANmoduls (NOT for GW-001 and GW-002 !!!).
        """
        tx_error_counter = structures.DWORD(0)
        rx_error_counter = structures.DWORD(0)
        UcanGetCanErrorCounter(
            self._handle, channel, byref(tx_error_counter), byref(rx_error_counter)
        )
        return tx_error_counter, rx_error_counter

    def set_tx_timeout(self, channel, timeout):
        """
        Sets the transmission timeout.

        :param int channel: CAN channel, to be used (:data:`Channel.CHANNEL_CH0` or :data:`Channel.CHANNEL_CH1`).
        :param float timeout: Transmit timeout in seconds (value 0 disables this feature).
        """
        UcanSetTxTimeout(self._handle, channel, int(timeout * 1000))

    def shutdown(self, channel=constants.Channel.CHANNEL_ALL, shutdown_hardware=True):
        """
        Shuts down all CAN interfaces and/or the hardware interface.

        :param int channel:
            CAN channel, to be used (:data:`Channel.CHANNEL_CH0`, :data:`Channel.CHANNEL_CH1` or
            :data:`Channel.CHANNEL_ALL`)
        :param bool shutdown_hardware: If true then the hardware interface will be closed too.
        """
        # shutdown each channel if it's initialized
        for _channel, is_initialized in self._ch_is_initialized.items():
            if is_initialized and (
                _channel == channel
                or channel == constants.Channel.CHANNEL_ALL
                or shutdown_hardware
            ):
                UcanDeinitCanEx(self._handle, _channel)
                self._ch_is_initialized[_channel] = False

        # shutdown hardware
        if self._hw_is_initialized and shutdown_hardware:
            UcanDeinitHardware(self._handle)
            self._hw_is_initialized = False
            self._handle = structures.Handle(constants.INVALID_HANDLE)

    @staticmethod
    def get_user_dll_version():
        """
        Returns the version number of the USBCAN-library.

        :return: Software version number.
        :rtype: int
        """
        return UcanGetVersionEx(constants.VersionType.VER_TYPE_USER_DLL)

    @staticmethod
    def set_debug_mode(level, filename, flags=0):
        """
        This function enables the creation of a debug log file out of the USBCAN-library. If this
        feature has already been activated via the USB-CANmodul Control, the content of the
        “old” log file will be copied to the new file. Further debug information will be appended to
        the new file.

        :param int level: Debug level (bit format).
        :param str filename: File path to debug log file.
        :param int flags: Additional flags (bit0: file append mode).
        :return: False if logfile not created otherwise True.
        :rtype: bool
        """
        return UcanSetDebugMode(level, filename, flags)

    @staticmethod
    def get_can_status_message(can_status):
        """
        Converts a given CAN status value to the appropriate message string.

        :param can_status: CAN status value from method :meth:`get_status` (see enum :class:`CanStatus`)
        :return: Status message string.
        :rtype: str
        """
        status_msgs = {
            constants.CanStatus.CANERR_TXMSGLOST: "Transmit message lost",
            constants.CanStatus.CANERR_MEMTEST: "Memory test failed",
            constants.CanStatus.CANERR_REGTEST: "Register test failed",
            constants.CanStatus.CANERR_QXMTFULL: "Transmit queue is full",
            constants.CanStatus.CANERR_QOVERRUN: "Receive queue overrun",
            constants.CanStatus.CANERR_QRCVEMPTY: "Receive queue is empty",
            constants.CanStatus.CANERR_BUSOFF: "Bus Off",
            constants.CanStatus.CANERR_BUSHEAVY: "Error Passive",
            constants.CanStatus.CANERR_BUSLIGHT: "Warning Limit",
            constants.CanStatus.CANERR_OVERRUN: "Rx-buffer is full",
            constants.CanStatus.CANERR_XMTFULL: "Tx-buffer is full",
        }
        return (
            "OK"
            if can_status == constants.CanStatus.CANERR_OK
            else ", ".join(
                msg for status, msg in status_msgs.items() if can_status & status
            )
        )

    @staticmethod
    def get_baudrate_message(baudrate):
        """
        Converts a given baud rate value for GW-001/GW-002 to the appropriate message string.

        :param Baudrate baudrate:
            Bus Timing Registers, BTR0 in high order byte and BTR1 in low order byte
            (see enum :class:`Baudrate`)
        :return: Baud rate message string.
        :rtype: str
        """
        baudrate_msgs = {
            constants.Baudrate.BAUD_AUTO: "auto baudrate",
            constants.Baudrate.BAUD_10kBit: "10 kBit/sec",
            constants.Baudrate.BAUD_20kBit: "20 kBit/sec",
            constants.Baudrate.BAUD_50kBit: "50 kBit/sec",
            constants.Baudrate.BAUD_100kBit: "100 kBit/sec",
            constants.Baudrate.BAUD_125kBit: "125 kBit/sec",
            constants.Baudrate.BAUD_250kBit: "250 kBit/sec",
            constants.Baudrate.BAUD_500kBit: "500 kBit/sec",
            constants.Baudrate.BAUD_800kBit: "800 kBit/sec",
            constants.Baudrate.BAUD_1MBit: "1 MBit/s",
            constants.Baudrate.BAUD_USE_BTREX: "BTR Ext is used",
        }
        return baudrate_msgs.get(baudrate, "BTR is unknown (user specific)")

    @staticmethod
    def get_baudrate_ex_message(baudrate_ex):
        """
        Converts a given baud rate value for systec USB-CANmoduls to the appropriate message string.

        :param BaudrateEx baudrate_ex: Bus Timing Registers (see enum :class:`BaudrateEx`)
        :return: Baud rate message string.
        :rtype: str
        """
        baudrate_ex_msgs = {
            constants.BaudrateEx.BAUDEX_AUTO: "auto baudrate",
            constants.BaudrateEx.BAUDEX_10kBit: "10 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_10kBit: "10 kBit/sec",
            constants.BaudrateEx.BAUDEX_20kBit: "20 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_20kBit: "20 kBit/sec",
            constants.BaudrateEx.BAUDEX_50kBit: "50 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_50kBit: "50 kBit/sec",
            constants.BaudrateEx.BAUDEX_100kBit: "100 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_100kBit: "100 kBit/sec",
            constants.BaudrateEx.BAUDEX_125kBit: "125 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_125kBit: "125 kBit/sec",
            constants.BaudrateEx.BAUDEX_250kBit: "250 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_250kBit: "250 kBit/sec",
            constants.BaudrateEx.BAUDEX_500kBit: "500 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_500kBit: "500 kBit/sec",
            constants.BaudrateEx.BAUDEX_800kBit: "800 kBit/sec",
            constants.BaudrateEx.BAUDEX_SP2_800kBit: "800 kBit/sec",
            constants.BaudrateEx.BAUDEX_1MBit: "1 MBit/s",
            constants.BaudrateEx.BAUDEX_SP2_1MBit: "1 MBit/s",
            constants.BaudrateEx.BAUDEX_USE_BTR01: "BTR0/BTR1 is used",
        }
        return baudrate_ex_msgs.get(baudrate_ex, "BTR is unknown (user specific)")

    @staticmethod
    def get_product_code_message(product_code):
        product_code_msgs = {
            constants.ProductCode.PRODCODE_PID_GW001: "GW-001",
            constants.ProductCode.PRODCODE_PID_GW002: "GW-002",
            constants.ProductCode.PRODCODE_PID_MULTIPORT: "Multiport CAN-to-USB G3",
            constants.ProductCode.PRODCODE_PID_BASIC: "USB-CANmodul1 G3",
            constants.ProductCode.PRODCODE_PID_ADVANCED: "USB-CANmodul2 G3",
            constants.ProductCode.PRODCODE_PID_USBCAN8: "USB-CANmodul8 G3",
            constants.ProductCode.PRODCODE_PID_USBCAN16: "USB-CANmodul16 G3",
            constants.ProductCode.PRODCODE_PID_RESERVED3: "Reserved",
            constants.ProductCode.PRODCODE_PID_ADVANCED_G4: "USB-CANmodul2 G4",
            constants.ProductCode.PRODCODE_PID_BASIC_G4: "USB-CANmodul1 G4",
            constants.ProductCode.PRODCODE_PID_RESERVED1: "Reserved",
            constants.ProductCode.PRODCODE_PID_RESERVED2: "Reserved",
        }
        return product_code_msgs.get(
            product_code & constants.PRODCODE_MASK_PID, "Product code is unknown"
        )

    @classmethod
    def convert_to_major_ver(cls, version):
        """
        Converts the a version number into the major version.

        :param int version: Version number to be converted.
        :return: Major version.
        :rtype: int
        """
        return version & 0xFF

    @classmethod
    def convert_to_minor_ver(cls, version):
        """
        Converts the a version number into the minor version.

        :param int version: Version number to be converted.
        :return: Minor version.
        :rtype: int
        """
        return (version & 0xFF00) >> 8

    @classmethod
    def convert_to_release_ver(cls, version):
        """
        Converts the a version number into the release version.

        :param int version: Version number to be converted.
        :return: Release version.
        :rtype: int
        """
        return (version & 0xFFFF0000) >> 16

    @classmethod
    def check_version_is_equal_or_higher(cls, version, cmp_major, cmp_minor):
        """
        Checks if the version is equal or higher than a specified value.

        :param int version: Version number to be checked.
        :param int cmp_major: Major version to be compared with.
        :param int cmp_minor: Minor version to be compared with.
        :return: True if equal or higher, otherwise False.
        :rtype: bool
        """
        return (cls.convert_to_major_ver(version) > cmp_major) or (
            cls.convert_to_major_ver(version) == cmp_major
            and cls.convert_to_minor_ver(version) >= cmp_minor
        )

    @classmethod
    def check_is_systec(cls, hw_info_ex):
        """
        Checks whether the module is a systec USB-CANmodul.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module is a systec USB-CANmodul, otherwise False.
        :rtype: bool
        """
        return (
            hw_info_ex.m_dwProductCode & constants.PRODCODE_MASK_PID
        ) >= constants.ProductCode.PRODCODE_PID_MULTIPORT

    @classmethod
    def check_is_G4(cls, hw_info_ex):
        """
        Checks whether the module is a USB-CANmodul of fourth generation (G4).

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module is a USB-CANmodul G4, otherwise False.
        :rtype: bool
        """
        return hw_info_ex.m_dwProductCode & constants.PRODCODE_PID_G4

    @classmethod
    def check_is_G3(cls, hw_info_ex):
        """
        Checks whether the module is a USB-CANmodul of third generation (G3).

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module is a USB-CANmodul G3, otherwise False.
        :rtype: bool
        """
        return cls.check_is_systec(hw_info_ex) and not cls.check_is_G4(hw_info_ex)

    @classmethod
    def check_support_cyclic_msg(cls, hw_info_ex):
        """
        Checks whether the module supports automatically transmission of cyclic CAN messages.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module does support cyclic CAN messages, otherwise False.
        :rtype: bool
        """
        return cls.check_is_systec(hw_info_ex) and cls.check_version_is_equal_or_higher(
            hw_info_ex.m_dwFwVersionEx, 3, 6
        )

    @classmethod
    def check_support_two_channel(cls, hw_info_ex):
        """
        Checks whether the module supports two CAN channels (at logical device).

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module (logical device) does support two CAN channels, otherwise False.
        :rtype: bool
        """
        return cls.check_is_systec(hw_info_ex) and (
            hw_info_ex.m_dwProductCode & constants.PRODCODE_PID_TWO_CHA
        )

    @classmethod
    def check_support_term_resistor(cls, hw_info_ex):
        """
        Checks whether the module supports a termination resistor at the CAN bus.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module does support a termination resistor.
        :rtype: bool
        """
        return hw_info_ex.m_dwProductCode & constants.PRODCODE_PID_TERM

    @classmethod
    def check_support_user_port(cls, hw_info_ex):
        """
        Checks whether the module supports a user I/O port.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module supports a user I/O port, otherwise False.
        :rtype: bool
        """
        return (
            (
                (hw_info_ex.m_dwProductCode & constants.PRODCODE_MASK_PID)
                != constants.ProductCode.PRODCODE_PID_BASIC
            )
            and (
                (hw_info_ex.m_dwProductCode & constants.PRODCODE_MASK_PID)
                != constants.ProductCode.PRODCODE_PID_RESERVED1
            )
            and cls.check_version_is_equal_or_higher(hw_info_ex.m_dwFwVersionEx, 2, 16)
        )

    @classmethod
    def check_support_rb_user_port(cls, hw_info_ex):
        """
        Checks whether the module supports a user I/O port including read back feature.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module does support a user I/O port including the read back feature, otherwise False.
        :rtype: bool
        """
        return hw_info_ex.m_dwProductCode & constants.PRODCODE_PID_RBUSER

    @classmethod
    def check_support_rb_can_port(cls, hw_info_ex):
        """
        Checks whether the module supports a CAN I/O port including read back feature.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module does support a CAN I/O port including the read back feature, otherwise False.
        :rtype: bool
        """
        return hw_info_ex.m_dwProductCode & constants.PRODCODE_PID_RBCAN

    @classmethod
    def check_support_ucannet(cls, hw_info_ex):
        """
        Checks whether the module supports the usage of USB-CANnetwork driver.

        :param HardwareInfoEx hw_info_ex:
            Extended hardware information structure (see method :meth:`get_hardware_info`).
        :return: True when the module does support the usage of the USB-CANnetwork driver, otherwise False.
        :rtype: bool
        """
        return cls.check_is_systec(hw_info_ex) and cls.check_version_is_equal_or_higher(
            hw_info_ex.m_dwFwVersionEx, 3, 8
        )

    @classmethod
    def calculate_amr(cls, is_extended, from_id, to_id, rtr_only=False, rtr_too=True):
        """
        Calculates AMR using CAN-ID range as parameter.

        :param bool is_extended: If True parameters from_id and to_id contains 29-bit CAN-ID.
        :param int from_id: First CAN-ID which should be received.
        :param int to_id: Last CAN-ID which should be received.
        :param bool rtr_only: If True only RTR-Messages should be received, and rtr_too will be ignored.
        :param bool rtr_too: If True CAN data frames and RTR-Messages should be received.
        :return: Value for AMR.
        :rtype: int
        """
        return (
            (((from_id ^ to_id) << 3) | (0x7 if rtr_too and not rtr_only else 0x3))
            if is_extended
            else (
                ((from_id ^ to_id) << 21)
                | (0x1FFFFF if rtr_too and not rtr_only else 0xFFFFF)
            )
        )

    @classmethod
    def calculate_acr(cls, is_extended, from_id, to_id, rtr_only=False, rtr_too=True):
        """
        Calculates ACR using CAN-ID range as parameter.

        :param bool is_extended: If True parameters from_id and to_id contains 29-bit CAN-ID.
        :param int from_id: First CAN-ID which should be received.
        :param int to_id: Last CAN-ID which should be received.
        :param bool rtr_only: If True only RTR-Messages should be received, and rtr_too will be ignored.
        :param bool rtr_too: If True CAN data frames and RTR-Messages should be received.
        :return: Value for ACR.
        :rtype: int
        """
        return (
            (((from_id & to_id) << 3) | (0x04 if rtr_only else 0))
            if is_extended
            else (((from_id & to_id) << 21) | (0x100000 if rtr_only else 0))
        )

    def _connect_control(self, event, param, arg):
        """
        Is the actual callback function for :meth:`init_hw_connect_control_ex`.

        :param event:
            Event (:data:`constants.CbEvent.EVENT_CONNECT`, :data:`constants.CbEvent.EVENT_DISCONNECT` or
            :data:`constants.CbEvent.EVENT_FATALDISCON`).
        :param param: Additional parameter depending on the event.
        - constants.CbEvent.EVENT_CONNECT: always 0
        - constants.CbEvent.EVENT_DISCONNECT: always 0
        - constants.CbEvent.EVENT_FATALDISCON: USB-CAN-Handle of the disconnected module
        :param arg: Additional parameter defined with :meth:`init_hardware_ex` (not used in this wrapper class).
        """
        log.debug("Event: %s, Param: %s", event, param)

        if event == constants.CbEvent.EVENT_FATALDISCON:
            self.fatal_disconnect_event(param)
        elif event == constants.CbEvent.EVENT_CONNECT:
            self.connect_event()
        elif event == constants.CbEvent.EVENT_DISCONNECT:
            self.disconnect_event()

    def _callback(self, Handle, event, channel, arg):
        """
        Is called if a working event occurred.

        :param int handle: USB-CAN-Handle returned by the function :meth:`init_hardware`.
        :param int event: Event type.
        :param int channel:
            CAN channel (:data:`Channel.CHANNEL_CH0`, :data:`Channel.CHANNEL_CH1` or :data:`Channel.CHANNEL_ANY`).
        :param arg: Additional parameter defined with :meth:`init_hardware_ex`.
        """
        log.debug(
            "Handle: %s, Event: %s, Channel: %s", structures.Handle, event, channel
        )

        if event == constants.CbEvent.EVENT_INITHW:
            self.init_hw_event()
        elif event == constants.CbEvent.EVENT_init_can:
            self.init_can_event(channel)
        elif event == constants.CbEvent.EVENT_RECEIVE:
            self.can_msg_received_event(channel)
        elif event == constants.CbEvent.EVENT_STATUS:
            self.status_event(channel)
        elif event == constants.CbEvent.EVENT_DEINIT_CAN:
            self.deinit_can_event(channel)
        elif event == constants.CbEvent.EVENT_DEINITHW:
            self.deinit_hw_event()

    def init_hw_event(self):
        """
        Event occurs when a USB-CANmodul has been initialized (see method :meth:`init_hardware`).

        .. note:: To be overridden by subclassing.
        """

    def init_can_event(self, channel):
        """
        Event occurs when a CAN interface of a USB-CANmodul has been initialized.

        :param int channel: Specifies the CAN channel which was initialized (see method :meth:`init_can`).

        .. note:: To be overridden by subclassing.
        """

    def can_msg_received_event(self, channel):
        """
        Event occurs when at leas one CAN message has been received.

        Call the method :meth:`read_can_msg` to receive the CAN messages.

        :param int channel: Specifies the CAN channel which received CAN messages.

        .. note:: To be overridden by subclassing.
        """

    def status_event(self, channel):
        """
        Event occurs when the error status of a module has been changed.

        Call the method :meth:`get_status` to receive the error status.

        :param int channel: Specifies the CAN channel which status has been changed.

        .. note:: To be overridden by subclassing.
        """

    def deinit_can_event(self, channel):
        """
        Event occurs when a CAN interface has been deinitialized (see method :meth:`shutdown`).

        :param int channel: Specifies the CAN channel which status has been changed.

        .. note:: To be overridden by subclassing.
        """

    def deinit_hw_event(self):
        """
        Event occurs when a USB-CANmodul has been deinitialized (see method :meth:`shutdown`).

        .. note:: To be overridden by subclassing.
        """

    def connect_event(self):
        """
        Event occurs when a new USB-CANmodul has been connected to the host.

        .. note:: To be overridden by subclassing.
        """

    def disconnect_event(self):
        """
        Event occurs when a USB-CANmodul has been disconnected from the host.

        .. note:: To be overridden by subclassing.
        """

    def fatal_disconnect_event(self, device_number):
        """
        Event occurs when a USB-CANmodul has been disconnected from the host which was currently initialized.

        No method can be called for this module.

        :param int device_number: The device number which was disconnected.

        .. note:: To be overridden by subclassing.
        """


UcanServer._enum_callback_ref = structures.EnumCallback(UcanServer._enum_callback)
