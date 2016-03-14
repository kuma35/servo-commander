#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Controlling Arduino nano pwm servo.

# short packet
# 'EF','65', <<Flag>>, <<ID>>, <<addr>>, <<len>>, <<count>>, <<data>>..., <<sum>>
# 
# send FLAG
# 0b01000000:Write to FLASH
# 0b00000011:memory 0-31
# 0b00000001:ACK
#
# return packet
# 'EF', '66', <<flag>>, <<ID>>, <<addr>>, <<len>>, <<count>>, <<data>>.... <<sum>
# resp FLAG
# 0b00000010:send packet error
#
#
# virtual register
# 0-10 copy from EEPROM at setup(). FLAG_FLASH is 1 then write to EEPROM.
# 11-  register. attach and pulse.
# addr description                 default
# ==== =========================== =======
#    0 I2C Address                       0
#    1 Servo 0 digital port number       5
#    2 Servo 1 digital port number       6
#    3 Servo 0 minimum pulse (L,H)     800
#    4 -                                 -
#    5 Servo 0 maximam pulse (L,H)    2200
#    6 -                                 -
#    7 Servo 1 minimum pulse (L,H)     800
#    8 -                                 -
#    9 Servo 1 maximam pulse (L,H)    2200
#   10 -                                 -
#   11 Servo 0 attach flag               0
#   12 Servo 1 attach flag               0
#   13 Servo 0 pulse (L,H)            1100
#   14 -                                 -
#   15 Servo 1 pulse (L,H)            1100
#   16 -                                 -



import array
import pprint
import time
#import locale
import serial
import argparse
import sys

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

Label_fmt = '{l:>30}'

def print_l_h(title, memory) :
    print((Label_fmt+':{v:5}({bl:#x},{bh:#x})').format(l=title,
                                                       v=int.from_bytes(list(memory[0:2]), 'little', signed=True),
                                                       bl=memory[0], bh=memory[1]))
def print_h_l(title, memory) :
    print((Label_fmt+':{v:5}({bh:#x},{bl:#x})').format(l=title,
                                                       v=int.from_bytes(list(memory[0:2]), 'big', signed=True),
                                                       bh=memory[0], bl=memory[1]))

class CmdInfo(CmdServo) :
    """ get servo infomation memory. """

    def __init__(self) :
        super(CmdInfo, self).__init__()

    def prepare(self) :
        self.packet = array.array('B',
                                  [0xEF, 0x65, FLAG_MEMORY, 0, 0, 0, 1])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        ser.write(self.packet)
        self.recv.extend(list(ser.read(7)))
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
        print_short_packet_header(self.recv)
        if self.section == 3:
            print_section_3(self.recv[7:-1])
        elif self.section == 5:
            print_section_5(self.recv[7:-1])
        else:
            print("Data:", end='')
            pp.pprint(self.recv[7:-1])
        print((self.label_fmt+':{1:#x}').format('Checksum', ord(self.recv[-1])))

class CmdAck(CmdServo) :
    """ ACK command. """

    def prepare(self) :
        self.packet = array.array('B',
                                  [0xEF, 0x65, 0x01, 0x00, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAck, self).execute()
        ser.write(self.packet)
        time.sleep(1);
        self.recv.append(ser.read())
        return self.recv

    def info(self, pp) :
        print('ACK(\\x07):', end='')
        pp.pprint(self.recv)

class CmdFlash(CmdServo) :
    """ Write to flash ROM. """

    def prepare(self, servo_id) :
        self.packet = array.array('B',
                                  [0xEF, 0x65, servo_id, 0x40, 0xFF, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdFlash, self).execute()
        ser.write(self.packet)
        time.sleep(1)

    def info(self, pp) :
        pass

class CmdAttach(CmdServo) :
    """ attach servo. """

    def prepare(self, servo_id) :
        addr = 11       # for servo id 0
        if servo_id == 1:
            addr = 12
        self.packet = array.array('B',
                                  [0xEF, 0x65, 0, 0, addr, 1, 1, 1])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdReboot, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

class CmdDetach(CmdServo) :
    """ detach servo. """

    def prepare(self, servo_id) :
        addr = 11       # for servo id 0
        if servo_id == 1:
            addr = 12
        self.packet = array.array('B',
                                  [0xEF, 0x65, 0, 0, addr, 1, 1, 0])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdReboot, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

class CmdAngle(CmdServo) :
    """ Goal Angle and Goal Time. before attach servo."""

    def prepare(self, servo_id, degree) :
        degree_packet = list(degree.to_bytes(2, 'big', signed=True))
        addr = 13       # for servo id 0
        if servo_id == 1:
            addr = 15
        self.packet = array.array('B',
                                  [0xEF, 0x65, 0x00, 0x00, addr, 0x02, 0x01])
        self.packet.extend(degree_packet)
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAngle, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass
    
def main() :
    parser = argparse.ArgumentParser(description='Manupirate PWM servo on Arudino nano with PwmSlave sketch.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.0')
    parser.add_argument('-p', '--port',
                         dest='port',
                         default='/dev/ttyUSB0',
                         metavar='DEVICE')
    parser.add_argument('-b', '--baud',
                         dest='baud',
                         default=9600)
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='no port open, no execute.')
    subparsers = parser.add_subparsers(dest='subparser_name')
    subparser1 = subparsers.add_parser('ack',
                                       help='return ACK(\\x07)')
    subparser2 = subparsers.add_parser('info',
                                       help='read memory')
    subparser3 = subparsers.add_parser('flash',
                                       help='write to flash ROM.')
    subparser4 = subparsers.add_parser('angle',
                                       help='set angle and speed.')
    subparser4.add_argument('servo_id',
                            type=int,
                            help='servo ID');
    subparser4.add_argument('degree',
                            type=int,
                            help='Goal Angle. 90degree to set 900.')
    subparser5 = subparsers.add_parser('attach',
                                       help='attach servo')
    subparser5.add_argument('servo_id',
                            type=int,
                            help='servo ID');
    subparser6 = subparsers.add_parser('detach',
                                       help='detach servo.')
    subparser6.add_argument('servo_id',
                            type=int,
                            help='servo id')
    
    args = parser.parse_args()
    
    if args.subparser_name == 'ack' :
        cmd = CmdAck()
        cmd.prepare()
    elif args.subparser_name == 'info' :
        cmd = CmdInfo()
        cmd.prepare(args.servo_id, args.section, args.addr, args.length)
    elif args.subparser_name == 'flash' :
        cmd = CmdFlash()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'angle' :
        cmd = CmdAngle()
        cmd.prepare(args.servo_id, args.degree)
    elif args.subparser_name == 'attach' :
        cmd = CmdAttach()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'detach' :
        cmd = CmdDetach()
        cmd.prepare(args.servo_id)
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
