import os
import pexpect
import re

from abc   import ABCMeta, abstractmethod
from array import array
from util  import *

verbose = False

class NrfBleDfuController(object):
    __metaclass__ = ABCMeta

    # Class instance variables
    ctrlpt_handle        = 0
    ctrlpt_cccd_handle   = 0
    data_handle          = 0

    pkt_receipt_interval = 10
    pkt_payload_size     = 20

    timeout = 10

    # --------------------------------------------------------------------------
    #  Start the firmware update process
    # --------------------------------------------------------------------------
    @abstractmethod
    def start(self):
        pass

    # --------------------------------------------------------------------------
    #  Check if the peripheral is running in bootloader (DFU) or application mode
    #  Returns True if the peripheral is in DFU mode
    # --------------------------------------------------------------------------
    @abstractmethod
    def check_DFU_mode(self):
        pass

    @abstractmethod
    # --------------------------------------------------------------------------
    #  Switch from application to bootloader (DFU)
    # --------------------------------------------------------------------------
    def switch_to_dfu_mode(self):
        pass

    # --------------------------------------------------------------------------
    #  Parse notification status results
    # --------------------------------------------------------------------------
    @abstractmethod
    def _dfu_parse_notify(self, notify):
        pass

    # --------------------------------------------------------------------------
    #  Wait for a notification and parse the response
    # --------------------------------------------------------------------------
    @abstractmethod
    def _wait_and_parse_notify(self):
        pass

    def __init__(self, target_mac, firmware_path, datfile_path):
        self.target_mac = target_mac

        self.firmware_path = firmware_path
        self.datfile_path = datfile_path

        self.ble_conn = pexpect.spawn(f"gatttool -b '{target_mac}' -t random --interactive")
        self.ble_conn.delaybeforesend = 0

    # --------------------------------------------------------------------------
    #  Start the firmware update process
    # --------------------------------------------------------------------------
    def start(self):
        (_, self.ctrlpt_handle, self.ctrlpt_cccd_handle) = self._get_handles(self.UUID_CONTROL_POINT)
        (_, self.data_handle, _) = self._get_handles(self.UUID_PACKET)

        if verbose:
            print(f'Control Point Handle: 0x{self.ctrlpt_handle:04x}, CCCD: 0x{self.ctrlpt_cccd_handle:04x}')
            print(f'Packet handle: 0x{self.data_handle:04x}')

        # Subscribe to notifications from Control Point characteristic
        self._enable_notifications(self.ctrlpt_cccd_handle)

        # Set the Packet Receipt Notification interval
        prn = uint16_to_bytes_le(self.pkt_receipt_interval)
        self._dfu_send_command(Procedures.SET_PRN, prn)

        self._dfu_send_init()

        self._dfu_send_image()

    # --------------------------------------------------------------------------
    # Initialize: 
    #    Hex: read and convert hexfile into bin_array 
    #    Bin: read binfile into bin_array
    # --------------------------------------------------------------------------
    def input_setup(self):
        print(f"Sending file {os.path.split(self.firmware_path)[1]} to {self.target_mac}")

        if self.firmware_path == None:
            raise Exception("input invalid")

        name, extent = os.path.splitext(self.firmware_path)

        if extent == ".bin":
            self.bin_array = array('B', open(self.firmware_path, 'rb').read())

            self.image_size = len(self.bin_array)
            print(f"Binary imge size: {self.image_size}")
            print(f"Binary CRC32: {crc32_unsigned(bytes(self.bin_array))}")

            return

        if extent == ".hex":
            intelhex = IntelHex(self.firmware_path)
            self.bin_array = intelhex.tobinarray()
            self.image_size = len(self.bin_array)
            print(f"bin array size: {self.image_size}")
            return

        raise Exception("input invalid")

    # --------------------------------------------------------------------------
    # Perform a scan and connect via gatttool.
    # Will return True if a connection was established, False otherwise
    # --------------------------------------------------------------------------
    def scan_and_connect(self):
        if verbose: print("scan_and_connect")

        print(f"Connecting to {self.target_mac}")

        try:
            self.ble_conn.expect('\[LE\]>.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            return False

        self.ble_conn.sendline('connect')

        try:
            res = self.ble_conn.expect('Connection successful.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            return False

        return True

    # --------------------------------------------------------------------------
    # Perform a reconnection via gatttool.
    # Will return True if a connection was established, False otherwise
    # --------------------------------------------------------------------------
    def reconnect(self):
        if verbose: print("reconnect")

        print(f"Reconnecting to {self.target_mac}")

        self.ble_conn.sendline('')

        try:
            self.ble_conn.expect('\[LE\]>.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            return False

        self.ble_conn.sendline('connect')

        try:
            self.ble_conn.expect('Connection successful.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            return False

        return True

    # --------------------------------------------------------------------------
    #  Disconnect from the peripheral and close the gatttool connection
    # --------------------------------------------------------------------------
    def disconnect(self):
        self.ble_conn.sendline('exit')
        self.ble_conn.close()

    def target_mac_increase(self, inc):
        self.target_mac = uint_to_mac_string(mac_string_to_uint(self.target_mac) + inc)

        # Re-start gatttool with the new address
        self.disconnect()
        self.ble_conn = pexpect.spawn(f"gatttool -b '{self.target_mac}' -t random --interactive")
        self.ble_conn.delaybeforesend = 0

    # --------------------------------------------------------------------------
    #  Fetch handles for a given UUID.
    #  Will return a three-tuple: (char handle, value handle, CCCD handle)
    #  Will raise an exception if the UUID is not found
    # --------------------------------------------------------------------------
    def _get_handles(self, uuid):
        self.ble_conn.before = ""
        self.ble_conn.sendline('characteristics')

        try:
            self.ble_conn.expect([uuid], timeout=self.timeout)
            handles = re.findall(b'.*handle: (0x....),.*char value handle: (0x....)', self.ble_conn.before)
            (handle, value_handle) = handles[-1]
        except pexpect.TIMEOUT as e:
            raise Exception(f"UUID not found: {uuid}")

        return (int(handle, 16), int(value_handle, 16), int(value_handle, 16)+1)

    # --------------------------------------------------------------------------
    #  Wait for notification to arrive.
    #  Example format: "Notification handle = 0x0019 value: 10 01 01"
    # --------------------------------------------------------------------------
    def _dfu_wait_for_notify(self):
        while True:
            if verbose: print("dfu_wait_for_notify")

            if not self.ble_conn.isalive():
                print("connection not alive")
                return None

            try:
                index = self.ble_conn.expect('Notification handle = .*? \r\n', timeout=self.timeout)

            except pexpect.TIMEOUT:
                #
                # The gatttool does not report link-lost directly.
                # The only way found to detect it is monitoring the prompt '[CON]'
                # and if it goes to '[   ]' this indicates the connection has
                # been broken.
                # In order to get a updated prompt string, issue an empty
                # sendline('').  If it contains the '[   ]' string, then
                # raise an exception. Otherwise, if not a link-lost condition,
                # continue to wait.
                #
                self.ble_conn.sendline('')
                if b'[   ]' in self.ble_conn.before:
                    print('Connection lost!')
                    raise Exception('Connection Lost')
                return None

            if index == 0:
                after = self.ble_conn.after
                hxstr = after.split()[3:]
                handle = int(hxstr[0], 16)
                return hxstr[2:]

            else:
                print(f"unexpeced index: {index}")
                return None

    # --------------------------------------------------------------------------
    #  Send a procedure + any parameters required
    # --------------------------------------------------------------------------
    def _dfu_send_command(self, procedure, params=[]):
        if verbose: print('$1')

        cmd = f'char-write-req 0x{self.ctrlpt_handle:04x} {procedure:02x}{bytes(params).hex()}'

        if verbose: print(cmd)

        self.ble_conn.sendline(cmd)

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('Characteristic value was written successfully.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            print("State timeout")

    # --------------------------------------------------------------------------
    #  Send an array of bytes
    # --------------------------------------------------------------------------
    def _dfu_send_data(self, data):
        cmd = f'char-write-cmd 0x{self.data_handle:04x} {bytes(data).hex()}'

        if verbose: print(cmd)

        self.ble_conn.sendline(cmd)

    # --------------------------------------------------------------------------
    #  Enable notifications from the Control Point Handle
    # --------------------------------------------------------------------------
    def _enable_notifications(self, cccd_handle):
        if verbose: print('_enable_notifications')

        cmd  = f'char-write-req 0x{cccd_handle:04x} 0100'

        if verbose: print(cmd)

        self.ble_conn.sendline(cmd)

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('Characteristic value was written successfully.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            print("State timeout")

    # --------------------------------------------------------------------------
    #  Enable indications from the Control Point Handle
    # --------------------------------------------------------------------------
    def _enable_indications(self, cccd_handle):
        if verbose: print('_enable_indications')

        cmd  = f'char-write-req 0x{cccd_handle:04x} 0200'

        if verbose: print(cmd)

        self.ble_conn.sendline(cmd)

        # Verify that command was successfully written
        try:
            res = self.ble_conn.expect('Characteristic value was written successfully.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            print("State timeout")
