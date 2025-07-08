#!/usr/bin/env python3
"""
------------------------------------------------------------------------------
 DFU Server for Nordic nRF51 based systems.
 Conforms to nRF51_SDK 11.0 BLE_DFU requirements.
------------------------------------------------------------------------------
"""
import os, re
import sys
import optparse
import time
import math
import traceback

from unpacker import Unpacker

from ble_secure_dfu_controller import BleDfuControllerSecure
from ble_legacy_dfu_controller import BleDfuControllerLegacy
from ble_ruuvitag_dfu_controller import BleDfuControllerRuuvitag

def main():

    init_msg =  """
    ================================
    ==                            ==
    ==         DFU Server         ==
    ==                            ==
    ================================
    """

    # print("DFU Server start")
    print(init_msg)

    try:
        parser = optparse.OptionParser(usage='%prog -f <hex_file> -a <dfu_target_address>\n\nExample:\n\tdfu.py -f application.hex -d application.dat -a cd:e3:4a:47:1c:e4',
                                       version='0.5')

        parser.add_option('-a', '--address',
                  action='store',
                  dest="address",
                  type="string",
                  default=None,
                  help='DFU target address.'
                  )

        parser.add_option('-f', '--file',
                  action='store',
                  dest="hexfile",
                  type="string",
                  default=None,
                  help='hex file to be uploaded.'
                  )

        parser.add_option('-d', '--dat',
                  action='store',
                  dest="datfile",
                  type="string",
                  default=None,
                  help='dat file to be uploaded.'
                  )

        parser.add_option('-z', '--zip',
                  action='store',
                  dest="zipfile",
                  type="string",
                  default=None,
                  help='zip file to be used.'
                  )

        parser.add_option('--ruuvitag',
                  action='store',
                  dest='ruuvitag',
                  default=None,
                  help='ruuvitag device ID'
                  )

        parser.add_option('--secure',
                  action='store_true',
                  dest='secure_dfu',
                  default=True,
                  help='Use secure bootloader (Nordic SDK > 12)'
                  )

        parser.add_option('--legacy',
                  action='store_false',
                  dest='secure_dfu',
                  help='Use secure bootloader (Nordic SDK < 12)'
                  )

        options, args = parser.parse_args()

    except Exception as e:
        print(e)
        print("For help use --help")
        sys.exit(2)

    try:

        ''' Validate input parameters '''

        if not options.address:
            parser.print_help()
            sys.exit(2)

        unpacker = None
        hexfile  = None
        datfile  = None

        if options.zipfile != None:

            if (options.hexfile != None) or (options.datfile != None):
                print("Conflicting input directives")
                sys.exit(2)

            try:
                unpacker = Unpacker()
                hexfile, datfile = unpacker.unpack_zipfile(options.zipfile)	
            except Exception as e:
                print(f"Failed to unpack zip: {e}")
                sys.exit(2)
                pass

        else:
            if (not options.hexfile) or (not options.datfile):
                parser.print_help()
                sys.exit(2)

            if not os.path.isfile(options.hexfile):
                print("Error: Hex file doesn't exist")
                sys.exit(2)

            if not os.path.isfile(options.datfile):
                print("Error: DAT file doesn't exist")
                sys.exit(2)

            hexfile = options.hexfile
            datfile = options.datfile


        ''' Start of Device Firmware Update processing '''

        if options.ruuvitag is not None:
            ble_dfu = BleDfuControllerRuuvitag(options.address.upper(), hexfile, datfile, options.ruuvitag)
        elif options.secure_dfu:
            ble_dfu = BleDfuControllerSecure(options.address.upper(), hexfile, datfile)
        else:
            ble_dfu = BleDfuControllerLegacy(options.address.upper(), hexfile, datfile)

        # Initialize inputs
        ble_dfu.input_setup()

        # Connect to peer device. Assume application mode.
        if ble_dfu.scan_and_connect():
            if not ble_dfu.check_DFU_mode():
                print("Need to switch to DFU mode")
                if not ble_dfu.switch_to_dfu_mode():
                    raise Exception("Failed to switch to DFU mode")
        else:
            # The device might already be in DFU mode (MAC + 1)
            ble_dfu.target_mac_increase(1)

            # Try connection with new address
            print("Couldn't connect, will try DFU MAC")
            if not ble_dfu.scan_and_connect():
                raise Exception("Can't connect to device")

        ble_dfu.start()

        # Disconnect from peer device if not done already and clean up.
        ble_dfu.disconnect()

    except Exception as e:
        # print(traceback.format_exc())
        print(f"Exception at line {sys.exc_info()[2].tb_lineno}: {e}")
        sys.exit(2)

    # If Unpacker for zipfile used then delete Unpacker
    if unpacker != None:
       unpacker.delete()

    print("DFU Server done")

"""
------------------------------------------------------------------------------

------------------------------------------------------------------------------
"""
if __name__ == '__main__':

    # Do not litter the world with broken .pyc files.
    sys.dont_write_bytecode = True

    main()
