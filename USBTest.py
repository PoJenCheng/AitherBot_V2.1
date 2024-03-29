import usb.util
import sys

devs = usb.core.find(idVendor=0x2341,idProduct=0x0043)
print(devs)