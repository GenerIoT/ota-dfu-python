import pexpect
import string
import time

from ble_secure_dfu_controller import BleDfuControllerSecure

class BleDfuControllerRuuvitag(BleDfuControllerSecure):
    # Class constants
    UUID_RUUVI_RX         = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
    UUID_RUUVI_TX         = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
    UUID_RUUVI_BUTTONLESS = '8ec90003-f315-4f60-9fb8-838830daea50'

    device_id = None

    def __init__(self, target_mac, firmware_path, datfile_path, device_id):
        super().__init__(target_mac, firmware_path, datfile_path)

        id_bytes = device_id.split(':')
        if len(id_bytes) != 8:
            raise ValueError('Ruuvitag device id is not in the format xx:xx:xx:xx:xx:xx:xx:xx')
        self.device_id = ''.join(id_bytes)

    # --------------------------------------------------------------------------
    #  Check if the peripheral is running in bootloader (DFU) or application mode
    #  Returns True if the peripheral is in DFU mode
    # --------------------------------------------------------------------------
    def check_DFU_mode(self):
        print("Checking DFU State...")

        self.ble_conn.sendline('characteristics')

        dfu_mode = False

        try:
            self.ble_conn.expect([self.UUID_RUUVI_TX], timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            dfu_mode = True

        return dfu_mode

    def send_and_wait(self, cmd, expected):
        self.ble_conn.sendline(cmd)

        try:
            self.ble_conn.expect(f'{expected}.*', timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            return False

        return True

    def switch_to_dfu_mode(self):
        self.ble_conn.sendline('characteristics')

        in_secure_mode = True
        try:
            self.ble_conn.expect([self.UUID_RUUVI_BUTTONLESS], timeout=self.timeout)
        except pexpect.TIMEOUT as e:
            in_secure_mode = False

        if not in_secure_mode:
            #(_, _, bl_tx_cccd_handle) = self._get_handles(self.UUID_RUUVI_TX)
            #self._enable_notifications(bl_tx_cccd_handle)
            if not self.send_and_wait('char-write-req 0x001c 0100', 'Characteristic value was written successfully'):
                return False

            #(_, bl_rx_handle, _) = self._get_handles(self.UUID_RUUVI_RX)
            #self.ble_conn.sendline(f'char-write-req 0x{bl_rx_handle:04x} 2a2a09{self.device_id}')
            #if not self.send_and_wait(f'char-write-req 0x0019 2a2a09{self.device_id}', 'Invalid file descriptor'):
            #    return False

            self.ble_conn.sendline(f'char-write-req 0x0019 2a2a09{self.device_id}')

            time.sleep(10)

            self.target_mac_increase(0)
            if not self.scan_and_connect():
                return False

        #(_, bl_buttonless_handle, bl_buttonless_cccd_handle) = self._get_handles(self.UUID_RUUVI_BUTTONLESS)
        #self._enable_indications(bl_buttonless_cccd_handle)
        if not self.send_and_wait('char-write-req 0x0011 0200', 'Characteristic value was written successfully'):
            return False

        #self.ble_conn.sendline(f'char-write-req 0x{bl_buttonless_handle:04x} 01')
        if not self.send_and_wait('char-write-req 0x0010 01', 'Characteristic value was written successfully'):
            return False

        # Wait some time for board to reboot
        time.sleep(1)

        # Increase the mac address by one and reconnect
        self.target_mac_increase(1)
        return self.scan_and_connect()
