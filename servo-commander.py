#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Controlling FUTABA RS405CB
import array
import pprint
import time
#import locale
import serial
#from optparse import OptionParser

def get_checksum(data) :
    checksum = data[2]
    for value in data[3:] :
        checksum ^= value
    return checksum

def append_checksum(data) :
    checksum = data[2]
    for value in data[3:] :
        checksum ^= value
    data.append(checksum)
    return data

def recheck_checksum(data) :
    checksum = data[2]
    for value in data[3:-1] :
        checksum ^= value
        data[-1] = checksum
    return data

def ack(ser) :
    snd = array.array('B', [0xFA, 0xAF, 0x01, 0x01, 0xFF, 0x00, 0x00])
    snd = append_checksum(snd)
    ser.write(snd)
    rcv = ser.read()
    return rcv

def info00(ser) :
    snd = array.array('B', [0xFA, 0xAF, 0x01, 0x03, 0xFF, 0x00, 0x00])
    snd = append_checksum(snd)
    ser.write(snd)
    rcv = []
    for v in range(30) :
        rcv[v] = ser.read()
    return rcv

def recv_packet(data) :
    if (get_checksum(data[0:-1]) == data[-1]) :
        print "checksum ok"
        print "Header(FDDF):", pp.pprint(data[0:1])
        print "ID:", pp.pprint(data[2])
        print "Flags:", pp.pprint(data[3])
        print "Adress:", pp.pprint(data[4])
        print "Length:", pp.pprint(data[5])
        print "Count(1):", pp.pprint(data[6])
        print "Data:", pp.pprint(data[7:-2])
        print "Sum:", pp.pprint(data[-1])
    else :
        print "checksum ng"

def main() :
    pp = pprint.PrettyPrinter(indent=4)
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    pp.pprint ack(ser)  # ACK return '\x07'
    info = info00(ser)
    recv_packet(info)
    #
    #トルクON
    snd = array.array('B', [0xfa, 0xaf, 0x01, 0x00, 0x24, 0x01, 0x01, 0x01, 0x24])
    ser.write(snd)
    rcv = ser.read()
    pp.pprint(rcv)
    time.sleep(1)
    ##-90度
    snd = array.array('B', [0xfa, 0xaf, 0x01, 0x00, 0x1e, 0x02, 0x01, 0x7C, 0xFC])
    snd = append_checksum(snd)
    ser.write(snd)
    time.sleep(10)
    ##トルクOFF
    snd = array.array('B', [0xfa, 0xaf, 0x01, 0x00, 0x24, 0x01, 0x01, 0x00])
    snd = append_checksum(snd)
    ser.write(snd)
    rcv = ser.read()
    pp.pprint(rcv)
    time.sleep(1)
    ##
    ser.close()
#def main():
#    u"""main routine"""
#    console_encode = locale.getpreferredencoding()
#    # parse command line
#    opt_parser = OptionParser(usage=("%prog [options]"),
#                              version="%prog 0.01")
#    opt_parser.add_option("-p", "--port",
#                          dest="port",
#                          help=("specify port device."
#                                "(default is /dev/ttyUSB0)"),
#                          metavar="DEVICE")
#    (options, arguments) = opt_parser.parse_args()
#    ###########
#    snd = array.array('B', [0xFA, 0xAF, 0x01, 0x01, 0xFF, 0x00, 0x00])
#    cheksum = snd[2];
#    for value in snd[3:] :
#        checksum ^= value
#    snd.append(checksum)
#    #########
#    ser = serial.Serial('/dev/ttyUSB0', 9600,
#                        parity=serial.PARITY_NONE)
#    ser.write(snd)
#    rcv = ser.read(100)
#    print rcv
#
#
if __name__ == "__main__":
    main()
 
