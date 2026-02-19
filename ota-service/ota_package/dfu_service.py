from ota_package.unpacker import Unpacker
from ota_package.ble_ruuvitag_dfu_controller import BleDfuControllerRuuvitag


def run_dfu(address, zipfile, ruuvitag):

    unpacker = None
    ble_dfu = None

    try:
        unpacker = Unpacker()
        hexfile, datfile = unpacker.unpack_zipfile(zipfile)

        ble_dfu = BleDfuControllerRuuvitag(
            address.upper(), hexfile, datfile, ruuvitag
        )

        ble_dfu.input_setup()

        errc = 0

        for i in range(5):
            print(f"Trying {i+1}/5")

            if ble_dfu.scan_and_connect():
                if not ble_dfu.check_DFU_mode():
                    print("Need to switch to DFU mode")
                    if not ble_dfu.switch_to_dfu_mode():
                        print("Failed to switch to DFU mode")
                        errc += 1
                    else:
                        break
                else:
                    break
            else:
                # The device might already be in DFU mode (MAC + 1)
                ble_dfu.target_mac_increase(1)
                print("Couldn't connect, will try DFU MAC")

                if not ble_dfu.scan_and_connect():
                    errc += 1
                else:
                    break

                ble_dfu.target_mac_increase(-1)

        if errc == 5:
            raise Exception("Error limit reached. Can't connect to device")

        ble_dfu.start()

        return True

    finally:
        if ble_dfu:
            try:
                ble_dfu.disconnect()
            except Exception:
                pass

        if unpacker:
            try:
                unpacker.delete()
            except Exception:
                pass