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

class CmdInfo(CmdServo) :
    """ get servo infomation memory. """

    def __init__(self) :
        super(CmdInfo, self).__init__()
        self.section_range = { 3:range(0, 30),
                               5:range(30, 60),
                               7:range(20, 30),
                               9:range(42, 60),
                               11:range(30, 42),
                               13:range(60, 128), }

    def prepare(self, servo_id, section, addr, length) :
        self.section = section
        if section in [3, 5, 7, 9, 11, 13] :
            self.packet = array.array('B',
                                      [0xFA, 0xAF, servo_id, section, 0xFF, 0x00, 0x00])
        elif section == 15 :
            self.addr = addr
            self.length = length
            self.packet = array.array('B',
                                      [0xFA, 0xAF, servo_id, section, addr, length, 0x00])
        else:
            raise CommandServoException("invalid section value")
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        ser.write(self.packet)
        sleep(1)
        self.recv.append(ser.read()) # header 0xFD(253) 
        self.recv.append(ser.read()) # header 0xDF(223)
        self.recv.append(ser.read()) # servo id
        self.recv.append(ser.read()) # flag
        self.recv.append(ser.read()) # addr
        self.recv.append(ser.read()) # length
        self.recv.append(ser.read()) # count == 1
        for i in range(i, i+self.recv[5]) :
            recv[i] = ser.read()
        self.recv[i] = ser.read() # checksum
        return self.recv

    def info(self, pp, data) :
        if (self.get_checksum(data[2:-1]) == data[-1]) :
            print("checksum ok")
            print("Header(0xFD(253),0xDF(223)):", pp.pprint(data[0:1]))
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
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='no port open, no execute.')
    subparsers = parser.add_subparsers(dest='subparser_name')
    subparser1 = subparsers.add_parser('ack',
                                       help='return ACK(\\x07)')
    subparser1.add_argument('-i', '--id',
                            dest='servo_id',
                            default=1,
                            help='specify servo id. default is %(default)s')
    subparser2 = subparsers.add_parser('info',
                                       help='read memory')
    subparser2.add_argument('-i', '--id',
                            dest='servo_id',
                            default=1,
                            help='specify servo id. default is %(default)s')
    subparser2.add_argument('-s', '--section',
                            dest='section',
                            type=int,
                            choices=[3, 5, 7, 9, 11, 13, 15],
                            default=3,
                            help='read memory 3:00-29, 5:30-59, 7:20-29, 9:42-59, 11:30-41, 13:60-127, 15:specify addr and length')
    subparser2.add_argument('--addr',
                            type=int,
                            help='section is 15, use --addr .')
    subparser2.add_argument('--length',
                            type=int,
                            help='section is 15, use --length .')
   
    args = parser.parse_args()
    
    if args.subparser_name == 'ack' :
        cmd = CmdAck()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'info' :
        cmd = CmdInfo()
        cmd.prepare(args.servo_id, args.section, args.addr, args.length)
    else :
        parser.exit(0, 'no specifiy command, nothing to do.\n')
    
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
 
