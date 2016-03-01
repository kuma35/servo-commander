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
        self.label_fmt = '{0:>30}'

    def get_checksum(self, packet) :
        """ calculate checksum byte from packet. """
        
        checksum = packet[2]
        for value in packet[3:] :
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
        super(CmdAck, self).execute()
        ser.write(self.packet)
        self.recv.append(ser.read())
        return self.recv

    def info(self, pp) :
        print('ACK(\\x07):', end='')
        pp.pprint(self.recv)

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
        self.recv.extend(list(ser.read(7)))
        #self.recv.append(ser.read()) # header 0xFD(253) 
        #self.recv.append(ser.read()) # header 0xDF(223)
        #self.recv.append(ser.read()) # servo id
        #self.recv.append(ser.read()) # flag
        #self.recv.append(ser.read()) # addr
        #self.recv.append(ser.read()) # length
        #self.recv.append(ser.read()) # count == 1
        #for i in range(0, ord(self.recv[5])) :
        #    self.recv.append(ser.read())
        self.recv.extend(list(ser.read(self.recv[5])))
        self.recv.append(ser.read()) # checksum
        return self.recv

    def info(self, pp) :
        print('Returned packet:')
        
        sum = self.recv[2]
        for value in self.recv[3:-1] :
            sum ^= value
        print('calculate checksum:{0}'.format(sum))
        print('recv checksum:{0}'.format(self.recv[-1]))
        if sum == ord(self.recv[-1]) :
            print('checksum OK')
        else :
            print('checksum NG')
        print((self.label_fmt+':{1:#x},{2:#x}').format('Header', self.recv[0], self.recv[1]))
        print((self.label_fmt+':{1}').format('ID', self.recv[2]))
        print((self.label_fmt+':{1:#010b}').format('Flags', self.recv[3]))        # 08b -> #010b :-)
        print((self.label_fmt+':{1:#x}').format('Address', self.recv[4]))
        print((self.label_fmt+':{1}').format('Length', self.recv[5]))
        print((self.label_fmt+':{1}').format('Count(1)', self.recv[6]))

        if self.section == 3:
            memory = self.recv[7:-1]

            print((self.label_fmt+':{1:#x},{2:#x}').format('Model Number L,H', memory[0], memory[1]))
            print((self.label_fmt+':{1}').format('Firmware Version', memory[2]))
            print((self.label_fmt+':{1}').format('Servo ID', memory[4]))
            print((self.label_fmt+':{1}').format('Reverse', memory[5]))
            print((self.label_fmt+':{1:#x}').format('Baud Rate', memory[6]))
            print((self.label_fmt+':{1}').format('Return Delay', memory[7]))
            print((self.label_fmt+':{1:5}({2:#x},{3:#x})').format('CW Angle Limit L,H',
                                                        int.from_bytes(list(memory[8:10]), 'little', signed=True),
                                                        memory[8], memory[9]))
            print((self.label_fmt+':{1:5}({2:#x},{3:#x})').format('CCW Angle Limit L,H',
                                                        int.from_bytes(list(memory[10:12]), 'little', signed=True),
                                                        memory[10], memory[11]))
            print((self.label_fmt+':{1:5}({2:#x},{3:#x})').format('Temperture Limit L,H',
                                                        int.from_bytes(list(memory[14:16]),'little', signed=True),
                                                        memory[14], memory[15]))
            print((self.label_fmt+':{1}').format('Damper', memory[20]))
            print((self.label_fmt+':{1}').format('Torque in Silence', memory[22]))
            print((self.label_fmt+':{1}').format('Warm-up Time',memory[23]))
            print((self.label_fmt+':{1}').format('CW Compliance Margin', memory[24]))
            print((self.label_fmt+':{1}').format('CCW Compliance Margin', memory[25]))
            print((self.label_fmt+':{1}').format('CW Compliance Slope', memory[26]))
            print((self.label_fmt+':{1}').format('CCW Compliance Slope', memory[27]))
            print((self.label_fmt+':{1:5}({2:#x},{3:#x})').format('Punch L,H',
                                                        int.from_bytes(list(memory[28:30]), 'little', signed=True),
                                                        memory[28], memory[29]))
        else:
            print("Data:", end='')
            pp.pprint(self.recv[7:-2])
        print((self.label_fmt+':{1:#x}').format('Checksum', ord(self.recv[-1])))

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
 
