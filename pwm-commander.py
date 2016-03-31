#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Controlling Arduino nano pwm servo.

# short packet
# 'EF','65', <<Flag>>, <<addr>>, <<len>>, <<data>>..., <<sum>>
# 
# send FLAG
# 0b01000000:Write to FLASH
# 0b00000011:memory 0-31
# 0b00000001:ACK
#
# return packet
# 'EF', '66', <<flag>>, <<addr>>, <<len>>, <<data>>.... <<sum>
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

Label_fmt = '{l:>30}'

class CmdServoException(object) :
    """ CmdServo and sub class exception. """

    pass

class CmdServo(object) :
    """ Base class for servo commands. """

    FLAG_ACK = 0x01
    FLAG_MEMORY = 0x02
    FLAG_FLASH = 0x40

    RESP_SIZE = {'HEADER':2, 'FLAG':1, 'ADDR':1, 'LEN':1, 'SUM':1,}
    RESP_OFFSET = {'HEADER':0}
    RESP_OFFSET['FLAG'] = RESP_OFFSET['HEADER'] + RESP_SIZE['HEADER']
    RESP_OFFSET['ADDR'] = RESP_OFFSET['FLAG'] + RESP_SIZE['FLAG']
    RESP_OFFSET['LEN'] = RESP_OFFSET['ADDR'] + RESP_SIZE['ADDR']
    RESP_OFFSET['DATA'] = RESP_OFFSET['LEN'] + RESP_SIZE['LEN']

    RESP_HEADER_SIZE = RESP_SIZE['HEADER']+RESP_SIZE['FLAG']+RESP_SIZE['ADDR']+RESP_SIZE['LEN']
    
    def __init__(self) :
        self.packet = []
        self.recv = []

    def get_checksum(self, packet) :
        """
        calculate checksum byte from packet. 
        addr(next header) to chceksum -1 to xor.

        """
        
        checksum = packet[0]
        for value in packet[1:] :
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

    M = {'I2C':0,
         'SV0':1,
         'SV1':2,
         'SV0MIN':3,
         'SV0MAX':5,
         'SV1MIN':7,
         'SV1MAX':9,
         'ATTACH0':11,
         'ATTACH1':12,
         'PULSE0':13,
         'PULSE1':15,}

    def __init__(self) :
        super(CmdInfo, self).__init__()
        self.packet_size = 0;

    def prepare(self) :
        self.packet = array.array('B',
                                  [0xEF, 0x65, CmdServo.FLAG_MEMORY, 0, 0])
        checksum = self.get_checksum(self.packet[2:])
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        ser.write(self.packet)
        ser.flush()
        while ser.in_waiting < CmdServo.RESP_HEADER_SIZE :
            time.sleep(0.5)
        self.recv.extend(list(ser.read(CmdServo.RESP_HEADER_SIZE)))
        while ser.in_waiting < self.recv[CmdServo.RESP_OFFSET['LEN']] :
            time.sleep(0.5)
        self.recv.extend(list(ser.read(self.recv[CmdServo.RESP_OFFSET['LEN']])))
        while ser.in_waiting < CmdServo.RESP_SIZE['SUM'] :
            time.sleep(0.5)
        self.recv.extend(list(ser.read(CmdServo.RESP_SIZE['SUM']))) # checksum
        return self.recv

    def info(self, pp) :
        print('Returned packet:')
        print('[{s}]'.format(s=','.join(['{0:X}'.format(v) for v in self.recv])))
        checksum = self.get_checksum(self.recv[2:-2])
        print('calculate checksum:{0}'.format(checksum))
        print('recv checksum:{0}'.format(self.recv[-1]))
        if checksum == self.recv[-1] :
            print('checksum OK')
        else :
            print('checksum NG')
        print((Label_fmt+':{h1:#x},{h2:#x}').format(l='header',
                                                    h1=self.recv[CmdServo.RESP_OFFSET['HEADER']],
                                                    h2=self.recv[CmdServo.RESP_OFFSET['HEADER']+1]))
        print((Label_fmt+':({v:#x})').format(l='flag',
                                             v=self.recv[CmdServo.RESP_OFFSET['FLAG']]))
        print((Label_fmt+':{a:#x}').format(l='address',
                                           a=self.recv[CmdServo.RESP_OFFSET['ADDR']]))
        print((Label_fmt+':{v:#x}').format(l='length',
                                           v=self.recv[CmdServo.RESP_OFFSET['LEN']]))
        #print("Data:", end='')
        #pp.pprint(self.recv[CmdServo.RESP_OFFSET['DATA']:-1])
        self.memory = self.recv[CmdServo.RESP_OFFSET['DATA']:-1]
        print((Label_fmt+':{v}').format(l='DATA;I2C address(no use)',
                                        v=self.memory[CmdInfo.M['I2C']]))
        print((Label_fmt+':{v}').format(l='DATA;Servo 0 pin',
                                        v=self.memory[CmdInfo.M['SV0']]))
        print((Label_fmt+':{v}').format(l='DATA;Servo 1 pin',
                                        v=self.memory[CmdInfo.M['SV1']]))
        print_h_l('DATA;Servo 0 min', self.memory[CmdInfo.M['SV0MIN']:CmdInfo.M['SV0MAX']])
        print_h_l('DATA;Servo 0 max', self.memory[CmdInfo.M['SV0MAX']:CmdInfo.M['SV1MIN']])
        print_h_l('DATA;Servo 1 min', self.memory[CmdInfo.M['SV1MIN']:CmdInfo.M['SV1MAX']])
        print_h_l('DATA;Servo 1 max', self.memory[CmdInfo.M['SV1MAX']:CmdInfo.M['ATTACH0']])
        print((Label_fmt+':{v}').format(l='DATA;Servo 0 attach',
                                        v=self.memory[CmdInfo.M['ATTACH0']]))
        print((Label_fmt+':{v}').format(l='DATA;Servo 1 attach',
                                        v=self.memory[CmdInfo.M['ATTACH1']]))
        print_h_l('DATA;Servo 0 pulse', self.memory[CmdInfo.M['PULSE0']:CmdInfo.M['PULSE1']])
        print_h_l('DATA;Servo 0 pulse', self.memory[CmdInfo.M['PULSE1']:CmdInfo.M['PULSE1']+2])
        print((Label_fmt+':{v:#x}').format(l='Checksum',
                                           v=self.recv[-1]))

class CmdAck(CmdServo) :
    """ ACK command. """

    def prepare(self) :
        self.packet = array.array('B',
                                  [0xEF, 0x65, CmdServo.FLAG_ACK, 0x00, 0x00, 0x00])
        checksum = self.get_checksum(self.packet)
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAck, self).execute()
        ser.write(self.packet)
        time.sleep(0.5);
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
        checksum = self.get_checksum(self.packet[2:])
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdFlash, self).execute()
        ser.write(self.packet)
        ser.flush()

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
        checksum = self.get_checksum(self.packet[2:])
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAttach, self).execute()
        ser.write(self.packet)
        ser.flush()

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
        checksum = self.get_checksum(self.packet[2:])
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdDetach, self).execute()
        ser.write(self.packet)
        ser.flush()

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
        checksum = self.get_checksum(self.packet[2:])
        self.packet.append(checksum)
        return self.packet

    def execute(self, ser) :
        super(CmdAngle, self).execute()
        ser.write(self.packet)
        ser.flush()

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
    parser.add_argument('-w', '--wait',
                        type=float,
                        dest='wait',
                        default=3.0,
                        help='wait board prepare from port open.')
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
        cmd.prepare()
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
        print('wait {w} sec. board prepare from port open.'.format(w=args.wait))
        time.sleep(args.wait)
        cmd.execute(ser)
        cmd.info(pp)
        ser.close()

if __name__ == '__main__':
    main()
