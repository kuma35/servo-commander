#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Controlling FUTABA RS405CB
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

class CmdSetId(CmdServo) :
    """ Set Servo ID. """

    def prepare(self, servo_id, new) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x00, 0x04, 0x01, 0x01, new])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdSetId, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

class CmdFlash(CmdServo) :
    """ Write to flash ROM. """

    def prepare(self, servo_id) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x40, 0xFF, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdFlash, self).execute()
        ser.write(self.packet)
        time.sleep(1)

    def info(self, pp) :
        pass

class CmdReboot(CmdServo) :
    """ Reboot Servo. """

    def prepare(self, servo_id) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x20, 0xFF, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdReboot, self).execute()
        ser.write(self.packet)
        time.sleep(3)

    def info(self, pp) :
        pass

class CmdAngle(CmdServo) :
    """ Goal Angle and Goal Time. Please later Torque ON."""

    def prepare(self, servo_id, degree, speed) :
        degree_packet = list(degree.to_bytes(2, 'little', signed=True))
        speed_packet = list(speed.to_bytes(2, 'little', signed=True))
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x00, 0x1E, 0x04, 0x01])
        self.packet.extend(degree_packet)
        self.packet.extend(speed_packet)
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAngle, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

class CmdMaxTorque(CmdServo) :
    """ Set Max Torque. """

    def prepare(self, servo_id, rate) :
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x00, 0x23, 0x01, 0x01, rae])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdMaxTorque, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

class CmdTorque(CmdServo) :
    """ Torque on/off/brak """

    def prepare(self, servo_id, flag) :
        if flag == 'on':
            value = 1
        elif flag == 'off' :
            value = 0
        elif flag == 'break' :
            value = 2
        else :
            raise CommandServoException('unknown torque flag. valid on/off/break.')
        self.packet = array.array('B',
                                  [0xFA, 0xAF, servo_id, 0x00, 0x24, 0x01, 0x01, value])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdTorque, self).execute()
        ser.write(self.packet)

    def info(self, pp) :
        pass

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

    def _print_l_h(self, title, memory) :
        print((self.label_fmt+':{1:5}({2:#x},{3:#x})').format(title,
                                                              int.from_bytes(list(memory[0:2]), 'little', signed=True),
                                                              memory[0], memory[1]))
        
    
    def _print_section_3(self, memory) :
        """ memory No.00-29. """
        
        print((self.label_fmt+':{1:#x},{2:#x}').format('Model Number L,H', memory[0], memory[1]))
        print((self.label_fmt+':{1}').format('Firmware Version', memory[2]))
        print((self.label_fmt+':{1}').format('Servo ID', memory[4]))
        print((self.label_fmt+':{1}').format('Reverse', memory[5]))
        print((self.label_fmt+':{1:#x}').format('Baud Rate', memory[6]))
        print((self.label_fmt+':{1}').format('Return Delay', memory[7]))
        self._print_l_h('CW Angle Limit L,H', memory[8:10])
        self._print_l_h('CCW Angle Limit L,H', memory[10:12])
        self._print_l_h('Temperture Limit L,H', memory[14:16])
        print((self.label_fmt+':{1}').format('Damper', memory[20]))
        print((self.label_fmt+':{1}').format('Torque in Silence', memory[22]))
        print((self.label_fmt+':{1}').format('Warm-up Time',memory[23]))
        print((self.label_fmt+':{1}').format('CW Compliance Margin', memory[24]))
        print((self.label_fmt+':{1}').format('CCW Compliance Margin', memory[25]))
        print((self.label_fmt+':{1}').format('CW Compliance Slope', memory[26]))
        print((self.label_fmt+':{1}').format('CCW Compliance Slope', memory[27]))
        self._print_l_h('Punch L,H', memory[28:30])

    def _print_section_5(self, memory) :
        """ memory No.30-59.  offset 30"""
        self._print_l_h('Goal Posision L,H', memory[0:2])
        self._print_l_h('Goal Time L,H', memory[2:4])
        print((self.label_fmt+':{1}').format('Max Torque', memory[5]))
        print((self.label_fmt+':{1}').format('Torque Enable', memory[6]))
        self._print_l_h('Present Posion L,H', memory[12:14])
        self._print_l_h('Present Time L,H', memory[14:16])
        self._print_l_h('Present Speed L,H', memory[16:18])
        self._print_l_h('Present Current L,H', memory[18:20])
        self._print_l_h('Present Temperture L,H', memory[20:22])
        self._print_l_h('Present Volts L,H', memory[22:24])
    
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
            self._print_section_3(self.recv[7:-1])
        elif self.section == 5:
            self._print_section_5(self.recv[7:-1])
        else:
            print("Data:", end='')
            pp.pprint(self.recv[7:-1])
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
    parser.add_argument('-i', '--id',
                        dest='servo_id',
                        type=int,
                        help='servo ID.',
                        default=1)
    parser.add_argument('--ack',
                        action='store_true',
                        default=True,
                        help='Checking specified id\'s servo existance.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='no port open, no execute.')
    subparsers = parser.add_subparsers(dest='subparser_name')
    subparser1 = subparsers.add_parser('ack',
                                       help='return ACK(\\x07)')
    subparser2 = subparsers.add_parser('info',
                                       help='read memory')
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
    subparser3 = subparsers.add_parser('setid',
                                       help='set new servo ID to Servo. NOTICE:NO UPDATE FLASH.')
    subparser3.add_argument('new',
                            type=int,
                            help='new servo ID.')
    subparser4 = subparsers.add_parser('flash',
                                       help='write to flash ROM.')
    subparser5 = subparsers.add_parser('reboot',
                                       help='Reboot Servo.')
    subparser6 = subparsers.add_parser('angle',
                                       help='set angle and speed.')
    subparser6.add_argument('--speed',
                            type=int,
                            default=0x3fff,
                            help='Goal Time. 0-0x3fff.')
    subparser6.add_argument('degree',
                            type=int,
                            help='Goal Angle. 90degree to set 900.')
    subparser7 = subparsers.add_parser('maxtorque',
                                       help='max torque')
    subparser7.add_argument('torque_rate',
                            type=int,
                            default=100,
                            choices=range(0,101),
                            help='max torque % 0-100')
    subparser8 = subparsers.add_parser('torque',
                                       help='torque on/off/break.')
    subparser8.add_argument('torque_flag',
                            choices=['on', 'off', 'break'],
                            help='torque on/off/break')
    args = parser.parse_args()
    
    if args.subparser_name == 'ack' :
        cmd = CmdAck()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'info' :
        cmd = CmdInfo()
        cmd.prepare(args.servo_id, args.section, args.addr, args.length)
    elif args.subparser_name == 'setid' :
        cmd = CmdSetId()
        cmd.prepare(args.servo_id, args.new)
    elif args.subparser_name == 'flash' :
        cmd = CmdFlash()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'reboot' :
        cmd = CmdReboot()
        cmd.prepare(args.servo_id)
    elif args.subparser_name == 'angle' :
        cmd = CmdAngle()
        cmd.prepare(args.servo_id, args.degree, args.speed)
    elif args.subparser_name == 'maxtorque' :
        cmd = CmdMaxTorque()
        cmd.prepare(args.servo_id, args.torque_rate)
    elif args.subparser_name == 'torque' :
        cmd = CmdTorque()
        cmd.prepare(args.servo_id, args.torque_flag)
    else :
        parser.exit(0, 'no specifiy command, nothing to do.\n')
    
    pp = pprint.PrettyPrinter(indent=4)
    if args.dryrun :
        print("====== DRY RUN. NOT EXECUTING =====")
        print("generate packet:", end= '')
        pp.pprint(cmd.packet)
    else :
        ser = serial.Serial(args.port, args.baud, timeout=1)
        if args.ack and args.subparser_name != 'ack' :
            cmd_ack = CmdAck()
            cmd_ack.prepare(args.servo_id)
            cmd_ack.execute(ser)
            if len(cmd_ack.recv) == 0 or cmd_ack.recv[0] != bytes([7]) :
                print("NO EXIST Servo ID's Servo. please check servo ID.")
                sys.exit(1)
        cmd.execute(ser)
        cmd.info(pp)
        ser.close()

if __name__ == '__main__':
    main()
