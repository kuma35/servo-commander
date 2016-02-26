#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Controlling FUTABA RS405CB
import array
import pprint
import time
#import locale
import serial
import argparse

class CmdServoException(object) :
    """ CmdServo and sub class exception. """

    pass

class CmdServo(object) :
    """ Base class for servo commands. """
    
    def __init__(self) :
        self.packet = []
        self.recv = []

    def get_checksum(self, data) :
        """ calculate checksum byte from array. """
        
        checksum = data[2]
        for value in data[3:] :
            checksum ^= value
        return checksum

    def prepare(self) :
        pass

    def execute(self) :
        if self.packet is None:
            raise CmdServoException("no prepare packet. coll prepare() before execute.");

    def print(self, pp) :
        """ pretty print recieve packet. """
        pass

class CmdAck(CmdServo) :
    """ ACK command. """

    def prepare(self, servo_id) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x01, 0xFF, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        CmdServo.execute()
        ser.write(self.packet)
        self.recv.append(ser.read())
        return self.recv

    def info(self, pp, data) :
        print('ACK(\\x07):', end='')
        pp.pprint(data)

class CmdInfo00(CmdServo) :
    """ get servo infomation memory addr.0- """

    def prepare(self, servo_id) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x03, 0xFF, 0x00, 0x00])
        cheksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        ser.write(self.packet)
        sleep(10)
        for v in range(30) :
            self.recv.append(ser.read())
        return recv

    def info(self, pp, data) :
        if (self.get_checksum(data[2:-1]) == data[-1]) :
            print("checksum ok")
            print("Header(FDDF):", pp.pprint(data[0:1]))
            print("ID:", pp.pprint(data[2]))
            print("Flags:", pp.pprint(data[3]))
            print("Adress:", pp.pprint(data[4]))
            print("Length:", pp.pprint(data[5]))
            print("Count(1):", pp.pprint(data[6]))
            print("Data:", pp.pprint(data[7:-2]))
            print("Checksum:", pp.pprint(data[-1]))
        else :
            print("invalid checksum.")
            print("recive packet:", end='')
            pp.pprint(data)

def main() :
    parser = argparse.ArgumentParser(description='Manupirate FUTABA command servo RS405CB.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.0')
    parser.add_argument('-p', '--port',
                         dest='port',
                         default='/dev/ttyUSB0',
                         metavar='DEVICE')
    parser.add_argument('-b', '--baud',
                         dest='baud',
                         default=115200)
    parser.add_argument('-i', '--id',
                         dest='servo_id',
                         default=1)
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='no port open, no execute.')
    parser.add_argument('command')
    args = parser.parse_args() # コマンドラインの引数を解釈します
    if args.command == 'ack' :
        cmd = CmdAck()
        cmd.prepare(args.servo_id)
    else :
        pass
    pp = pprint.PrettyPrinter(indent=4)
    if args.dryrun :
        print("====== DRY RUN. NOT EXECUTING =====")
        print("generate packet:", end= '')
        pp.pprint(cmd.packet)
    else :
        ser = serial.Serial(args.port, args.baud, timeout=1)
        cmd.execute(ser)
        cmd.info(pp)
        ser.close()

if __name__ == '__main__':
    main()
 
