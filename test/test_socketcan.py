#!/usr/bin/env python

"""
Test functions in `can.interfaces.socketcan.socketcan`.
"""
import unittest
import ctypes

from can.interfaces.socketcan.socketcan import (
    build_bcm_header,
    build_bcm_tx_delete_header,
    build_bcm_transmit_header,
    build_bcm_update_header,
    BcmMsgHead,
)
from can.interfaces.socketcan.constants import (
    CAN_BCM_TX_DELETE,
    CAN_BCM_TX_SETUP,
    SETTIMER,
    STARTTIMER,
    TX_COUNTEVT,
)
from can.util import little_endian_to_native


class SocketCANTest(unittest.TestCase):
    @unittest.skipIf(
        not all(
            [
                ctypes.sizeof(ctypes.c_long) == 4,
                ctypes.sizeof(ctypes.c_longlong) == 8,
                ctypes.alignment(ctypes.c_long) == 4,
                ctypes.alignment(ctypes.c_longlong) == 4,
            ]
        ),
        "Incorrect size or alignment",
    )
    def test_bcm_header_factory_32_bit_sizeof_long_4_alignof_long_4(self):
        """This tests a 32-bit platform (ex. Debian Stretch on i386), where:

        * sizeof(long) == 4
        * sizeof(long long) == 8
        * alignof(long) == 4
        * alignof(long long) == 4
        """

        assert BcmMsgHead.opcode.offset == 0
        assert BcmMsgHead.flags.offset == 4
        assert BcmMsgHead.count.offset == 8
        assert BcmMsgHead.ival1_tv_sec.offset == 12
        assert BcmMsgHead.ival1_tv_usec.offset == 16
        assert BcmMsgHead.ival2_tv_sec.offset == 20
        assert BcmMsgHead.ival2_tv_usec.offset == 24
        assert BcmMsgHead.can_id.offset == 28
        assert BcmMsgHead.nframes.offset == 32
        assert BcmMsgHead.frames.offset == 40
        assert ctypes.sizeof(BcmMsgHead) == 40

    @unittest.skipIf(
        not all(
            [
                ctypes.sizeof(ctypes.c_long) == 4,
                ctypes.sizeof(ctypes.c_longlong) == 8,
                ctypes.alignment(ctypes.c_long) == 4,
                ctypes.alignment(ctypes.c_longlong) == 8,
            ]
        ),
        "Incorrect size or alignment",
    )
    def test_bcm_header_factory_32_bit_sizeof_long_4_alignof_long_long_8(self):
        """This tests a 32-bit platform (ex. Raspbian Stretch on armv7l), where:

        * sizeof(long) == 4
        * sizeof(long long) == 8
        * alignof(long) == 4
        * alignof(long long) == 8
        """

        assert BcmMsgHead.opcode.offset == 0
        assert BcmMsgHead.flags.offset == 4
        assert BcmMsgHead.count.offset == 8
        assert BcmMsgHead.ival1_tv_sec.offset == 12
        assert BcmMsgHead.ival1_tv_usec.offset == 16
        assert BcmMsgHead.ival2_tv_sec.offset == 20
        assert BcmMsgHead.ival2_tv_usec.offset == 24
        assert BcmMsgHead.can_id.offset == 28
        assert BcmMsgHead.nframes.offset == 32
        assert BcmMsgHead.frames.offset == 40
        assert ctypes.sizeof(BcmMsgHead) == 40

    @unittest.skipIf(
        not all(
            [
                ctypes.sizeof(ctypes.c_long) == 8,
                ctypes.sizeof(ctypes.c_longlong) == 8,
                ctypes.alignment(ctypes.c_long) == 8,
                ctypes.alignment(ctypes.c_longlong) == 8,
            ]
        ),
        "Incorrect size or alignment",
    )
    def test_bcm_header_factory_64_bit_sizeof_long_8_alignof_long_8(self):
        """This tests a 64-bit platform (ex. Ubuntu 18.04 on x86_64), where:

        * sizeof(long) == 8
        * sizeof(long long) == 8
        * alignof(long) == 8
        * alignof(long long) == 8
        """

        assert BcmMsgHead.opcode.offset == 0
        assert BcmMsgHead.flags.offset == 4
        assert BcmMsgHead.count.offset == 8
        assert BcmMsgHead.ival1_tv_sec.offset == 16
        assert BcmMsgHead.ival1_tv_usec.offset == 24
        assert BcmMsgHead.ival2_tv_sec.offset == 32
        assert BcmMsgHead.ival2_tv_usec.offset == 40
        assert BcmMsgHead.can_id.offset == 48
        assert BcmMsgHead.nframes.offset == 52
        assert BcmMsgHead.frames.offset == 56
        assert ctypes.sizeof(BcmMsgHead) == 56

    def test_build_bcm_header(self):
        # little_endian_to_native should return a correctly aligned
        # bytes object for the current system
        expected_result = little_endian_to_native(
            b"\x02\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x01\x04\x00\x00"
            b"\x01\x00\x00\x00",
            fmt="<IIIllllII",
        )

        # pad to 8byte alignment
        expected_result += b"\x00" * ((8 - len(expected_result) % 8) % 8)

        self.assertEqual(
            expected_result,
            build_bcm_header(
                opcode=CAN_BCM_TX_DELETE,
                flags=0,
                count=0,
                ival1_seconds=0,
                ival1_usec=0,
                ival2_seconds=0,
                ival2_usec=0,
                can_id=0x401,
                nframes=1,
            ),
        )

    def test_build_bcm_tx_delete_header(self):
        can_id = 0x401
        flags = 0
        bcm_buffer = build_bcm_tx_delete_header(can_id=can_id, flags=flags)
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_DELETE, result.opcode)
        self.assertEqual(flags, result.flags)
        self.assertEqual(0, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(0, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_transmit_header_initial_period_0(self):
        can_id = 0x401
        flags = 0
        count = 42
        bcm_buffer = build_bcm_transmit_header(
            can_id=can_id,
            count=count,
            initial_period=0,
            subsequent_period=2,
            msg_flags=flags,
        )
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        # SETTIMER and STARTTIMER should be added to the initial flags
        self.assertEqual(flags | SETTIMER | STARTTIMER, result.flags)
        self.assertEqual(count, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(2, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_transmit_header_initial_period_1_24(self):
        can_id = 0x401
        flags = 0
        count = 42
        bcm_buffer = build_bcm_transmit_header(
            can_id=can_id,
            count=count,
            initial_period=1.24,
            subsequent_period=2,
            msg_flags=flags,
        )
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        # SETTIMER, STARTTIMER, TX_COUNTEVT should be added to the initial flags
        self.assertEqual(flags | SETTIMER | STARTTIMER | TX_COUNTEVT, result.flags)
        self.assertEqual(count, result.count)
        self.assertEqual(1, result.ival1_tv_sec)
        self.assertEqual(240000, result.ival1_tv_usec)
        self.assertEqual(2, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_update_header(self):
        can_id = 0x401
        flags = 0
        bcm_buffer = build_bcm_update_header(can_id=can_id, msg_flags=flags)
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        self.assertEqual(flags, result.flags)
        self.assertEqual(0, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(0, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)


if __name__ == "__main__":
    unittest.main()
