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
        self.recv.append(ser.read()) # header 0xFD(253) 
        self.recv.append(ser.read()) # header 0xDF(223)
        self.recv.append(ser.read()) # servo id
        self.recv.append(ser.read()) # flag
        self.recv.append(ser.read()) # addr
        self.recv.append(ser.read()) # length
        self.recv.append(ser.read()) # count == 1
        for i in range(0, int.from_bytes(self.recv[5], 'big')) :
            self.recv.append(ser.read())
        self.recv.append(ser.read()) # checksum
        return self.recv

    def info(self, pp) :
        #print("sum,sum")
        #pp.pprint(self.get_checksum(self.packet[0:-1]))
        #pp.pprint(self.recv[-1])
        #recv = self.recv[:-1]
        #checksum = self.get_checksum(recv)
        #print('checksum:{0}'.format(checksum))
        #print("checksum ok")
        sum = ord(self.recv[2])
        for value in self.recv[3:-1] :
            sum ^= ord(value)
        print('calculate checksum:{0}'.format(sum))
        print('recv checksum:{0}'.format(ord(self.recv[-1])))
        if sum == ord(self.recv[-1]) :
            print('checksum OK')
        else :
            print('checksum NG')
        print("Header(0xFD(253),0xDF(223)):", end='')
        pp.pprint(self.recv[0:2])
        
        print("ID:", end='')
        pp.pprint(self.recv[2])
        
        print("Flags:", end='')
        pp.pprint(self.recv[3])
        
        print("Address:", end='')
        pp.pprint(self.recv[4])
        
        print("Length:", end='')
        pp.pprint(self.recv[5])
        
        print("Count(1):", end='')
        pp.pprint(self.recv[6])

        if self.section == 3:
            memory = self.recv[7:-1]

            print("Model Number L,H(50H,40H):", end='')
            pp.pprint(memory[0:2])

            print("Firmware Version:", end='')
            pp.pprint(memory[2])

            print("Servo ID:", end='')
            pp.pprint(memory[4])

            print("Reverse:", end='')
            pp.pprint(memory[5])

            print("Baud Rate:", end='')
            pp.pprint(memory[6])

            print("Return Delay:", end='')
            pp.pprint(memory[7])

            lh=[ord(memory[8]), ord(memory[9])]
            print('CW Angle Limit L,H:{0}'.format(int.from_bytes(lh, 'little', signed=True)), end='')
            pp.pprint(memory[8:10])

            lh=[ord(memory[10]), ord(memory[11])]
            print('CCW Angle Limit L,H:{0}'.format(int.from_bytes(lh, 'little', signed=True)), end='')
            pp.pprint(memory[10:12])

            lh=[ord(memory[14]), ord(memory[15])]
            print('Temperture Limit L,H:{0}'.format(int.from_bytes(lh,'little', signed=True)), end='')
            pp.pprint(memory[14:16])

            print('Damper:', end='')
            pp.pprint(memory[20])

            print('Torque in Silence:', end='')
            pp.pprint(memory[22])

            print('Warm-up Time:', end='')
            pp.pprint(memory[23])

            print('CW Compliance Margin:', end='')
            pp.pprint(memory[24])
            
            print('CCW Compliance Margin:', end='')
            pp.pprint(memory[25])

            print('CW Compliance Slope:', end='')
            pp.pprint(memory[26])
            
            print('CCW Compliance Slope:', end='')
            pp.pprint(memory[27])

            lh=[ord(memory[28]), ord(memory[29])]
            print('Punch L,H:{0}'.format(int.from_bytes(lh, 'little', signed=True)), end='')
            pp.pprint(memory[28:30])
        else:
            print("Data:", end='')
            pp.pprint(self.recv[7:-2])
            
        
        print("Checksum:", end='')
        pp.pprint(self.recv[-1])
        #else :
        #    print("invalid checksum.")
        #    print("recive packet:", end='')
        #    pp.pprint(self.recv)

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
 
