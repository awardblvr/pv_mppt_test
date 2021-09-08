#!/usr/bin/env python
# -*- coding: utf_8 -*-


import os
import sys
import time
import datetime
import serial
# import logging
from utils import *
# import struct
# from array import *
import traceback

LOGGER = logging.getLogger("PV_Tester")

'''
> ls /dev/*serial*
/dev/cu.usbserial  /dev/tty.usbserial
'''

PORT = 1
PORT = '/dev/cu.usbserial'
logger = {}
po = None

mode_dict = {"CV": 0,
             "CC": 1,
             "CR": 2,
             "CP": 3}

cmd_dict = {
    "LOAD_ONOFF": 0x010E,
    "LOAD_MODE" : 0x0110,
    "CV_SETTING": 0x0112,
    "CC_SETTING": 0x0116,
    "CR_SETTING": 0x011A,
    "CW_SETTING": 0x011E,
    "U_MEASURE" : 0x0122,
    "I_MEASURE" : 0x0126 }


'''
Generate C language function of CRC check code:
    unsigned short Get_CRC16RTU(volatile unsigned char *ptr,unsigned char len) {
        unsigned char i;
        unsigned short crc = 0xFFFF; 
        if(len == 0) 
            len = 1;
        while (len--) {
            crc ^= *ptr; 
            for(i=0; i<8; i++) {
                if(crc&1) {
                    crc >>= 1; 
                    crc ^= 0xA001;
                } else {
                    crc >>= 1;
                }
            ptr++; 
        }
        return(crc); 
    }

'''

def create_logger(name="dummy", level=logging.DEBUG, record_format=None):
    """Create a logger according to the given settings"""
    if record_format is None:
        record_format = "%(asctime)s\t%(levelname)s\t%(module)s.%(funcName)s\t%(threadName)s\t%(message)s"

    logger = logging.getLogger("modbus_tk")
    logger.setLevel(level)
    formatter = logging.Formatter(record_format)
    if name == "udp":
        log_handler = LogitHandler(("127.0.0.1", 1975))
    elif name == "console":
        log_handler = ConsoleHandler()
    elif name == "dummy":
        log_handler = DummyHandler()
    else:
        raise Exception("Unknown handler %s" % name)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger


def Get_CRC16RTU(byte_array, len):
    crc = 0xFFFF
    len = (len, 1)[len == 0]

    for i in range(0, len):
        crc = byte_array[i] ^ crc
        for x in range(0, 8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    #Per manual.....    return ((crc >> 8, crc & 0xFF))    BUT THIS IS WRONG.. It is REVERSED!
    return ((crc & 0xFF, crc >> 8))



def send_cmd_bytes(cmd):
    # cmd = [0x01, 0x06, 0x01, 0x16, 0x00, 0x01, 0x04, 0x00, 0x00, 0x07, 0xD0] # , 0, 0 ]   #  0C 9D
    cmd_len = len(cmd) # - 2

    # logger.info(f"{[hex(x) for x in cmd]}, {cmd_len=}")

    my_crc = Get_CRC16RTU(cmd, cmd_len)

    # logger.info(f"Resulting CRC is {hex(my_crc)}")
    # logger.info(f"Resulting CRC is {[hex(x) for x in my_crc]}")

    cmd.extend(my_crc)

    logger.info(f"Final Cmd {[hex(x) for x in cmd]}, {cmd_len=}")

    # serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
    # Set read timeout to 3 Sec
    po = serial.Serial(port=PORT, baudrate=9600, timeout=0.25) # , timeout=0.2)

    bytes_written = po.write(cmd)
    # logger.info(f"{bytes_written=}")

    # time.sleep(0.25)

    read_buf = []
    read_buf_len = len(read_buf)

    startTimer = datetime.datetime.now()

    empty_reads = 0;
    while True:
        # if (datetime.datetime.now() - startTimer) > datetime.timedelta(seconds=2.0):
        #     logger.info(f"Timeout waiting for response to complete")
        #     break

        # read_buf.append(po.read())
        temp_buf = po.read()

        # if len(read_buf) != read_buf_len:
        #     logger.info(f"now read_buf is: {read_buf}")
        #     try:
        #         logger.info(f"now {[hex(x) for x in read_buf]}")
        #     except TypeError:
        #         pass
        #
        #     read_buf_len = len(read_buf)
        if len(temp_buf):
            # logger.info(f"Appending {temp_buf}")
            read_buf.append(temp_buf)
            # logger.info(f"read_buf NOW {read_buf}\n")
            empty_reads = 0
        else:
            # logger.info(f"temp_buf NULL")
            empty_reads += 1
            # read_buf.append(0xFF)
            break;

        if empty_reads > 1:
            break

        #
        # try:
        #     last_buffer_item = read_buf[-1]
        #     logger.info(f"last buffer: {type(last_buffer_item)}:{repr(last_buffer_item)}")
        #     if not last_buffer_item:
        #         logger.info(f"NULL")
        #
        # except Exception as exc:
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fqfname = exc_tb.tb_frame.f_code.co_filename
        #     fname = os.path.split(fqfname)[1]
        #     traceback.print_exception(exc_type, exc_obj, exc_tb)
        #
        # # logger.info(f"{empty_reads=}, {rb_len=}, last buf <{ord(read_buf[-1])}>")
        # logger.info(f"{empty_reads=}, {rb_len=}")
        # if read_buf_len == rb_len:
        #     empty_reads += 1
        # else:
        #     read_buf_len = rb_len
        #
        # if empty_reads > 5:
        #     logger.info(f"{empty_reads=} - DONE")
        #     break
        #
        # # if len(read_buf) >= len(cmd):
        # #     logger.info(f"Length of buffer exceeds original command length")
        # #     break

    # try:
    #     logger.info(f"RESPONSE : {[hex(x) for x in read_buf if x]}")
    # except TypeError:
    #     logger.info(f"RESPONSE NON-ARRAY: {read_buf}")
    #     pass

    return read_buf


def send_cmd(reg_addr, reg_value ):
    """
    send_cmd:

    :param reg_addr:  16 bit value to be converted to 2 bytes
    :param reg_value: 32 bit value to be converted to 2 bytes
    :return:
    """

    cmd_base = [0x01, # device address
                0x06, #  this instruction is a single register
                reg_addr >> 8, reg_addr & 0xFF,
                0x0, 0x01,
                0x4,    # first byte index of data for register   Maybe not.. See cryptic manual
                (reg_value >> 24) & 0xFF, (reg_value >> 16) & 0xFF, (reg_value >> 8) & 0xFF, reg_value & 0xFF]

    response = send_cmd_bytes(cmd_base)

    # logger.info(f"RESPONSE length : {len(response)}, {type(response)}")
    # for  e_idx, e in enumerate(response):
    #     if not e:
    #         continue
    #     logger.info(f"incoming response[{e_idx}] is {type(response[e_idx])}: {ord(response[e_idx])} Check: {repr(response[e_idx])}")


    logger.info(f"RESPONSE : {[hex((ord(x))) for x in response if x]}")
    # try:
    #     logger.info(f"final RESPONSE : {[hex(x) for x in response]}")
    # except TypeError:
    #     logger.info(f"final RESPONSE NON-ARRAY: {response}")
    #     pass


    # response_val = bytes(response[5:9])
    # response_val_str = b''.join(response[5:9])
    # response_val_str = '%02X'.join(response[5:9])
    # response_val_str = f"{format(response[5], '%02X')}"
    # logger.info(f"{response=}")

    response_int = int.from_bytes([ord(x) for x in response[5:9]], "big")
    logger.info(f"Response as integer {type(response_int)}: {response_int}")

    # for  e_idx, e in enumerate(response[5:9]):     # also try repr()
    #     e_offset = e_idx + 5
    #     logger.info(f"incoming response[{e_offset}] is {type(response[e_offset])}: {ord(response[e_offset])} Check: {repr(response[e_offset])}")
    #     # logger.info(f"incoming response[{e_offset}] is {type(response[e_offset])}")
    #
    # response_bytes = bytearray()
    # logger.info(f"initial response_bytes {response_bytes=}")
    # for e_idx, e in enumerate(response[5:9]):     # also try repr()
    #     e_offset = e_idx + 5
    #     logger.info(f"to append {type(e)}: {ord(e)} Check: {repr(e)}")
    #     # response_bytes.append(e)
    #     response_bytes.extend(e)
    #     logger.info(f"[{e_idx}] {repr(response_bytes)=}")
    #
    # logger.info(f"FINAL {type(response_bytes)}: {response_bytes}")
    #
    # response_int = int.from_bytes(response_bytes, "big")
    # logger.info(f"FINAL as integer  {type(response_int)}: {response_int}")
    #
    #
    # #response_list = [hex(ord(x)) for x in response[5:9]]
    # response_list = [ord(x) for x in response[5:9]]
    # logger.info(f"response response_bytes ---> Elements List {type(response_list)}: {response_list}")
    #
    # # response_list = struct.unpack("<I", bytearray([hex(ord(x)) for x in response[5:9]]))[0]
    # # response_list = struct.pack("@4B", *[ord(response[5]), ord(response[6]), ord(response[7]), ord(response[8])])
    # # response_list = array.array.fromlist([ord(response[5]), ord(response[6]), ord(response[7]), ord(response[8])])
    #
    # response_list2 = array('I')
    # response_list2 = response_list2.fromlist([int(x) for x in response[5:9]]) # fromlist([ord(response[5]), ord(response[6]), ord(response[7]), ord(response[8])])
    # logger.info(f"response 2 Elements Lis t {type(response_list2)}: {response_list2}")
    #
    #
    #
    # print(f"Elements List {type(response[5:9])}: {response[5:9]}")
    # response_list = response[5] + response[6] + response[7] + response[8]
    # print(f"response Elements List {type(response_list)}: {response_list}")
    # response_list_as = bytes(response[5])
    # print(f"{type(response_list_as)}: {response_list_as}")
    #
    # response_bytes = bytearray()
    # logger.info(f"--> {response_bytes=}")
    # response_val = int.from_bytes(response[5:9], "little")
    # logger.info(f"Response value bytes {response_val=}")
    # int_value = struct.unpack("<I", bytearray(response_val))[0]
    # # int_val = int.from_bytes(response_val, "big")
    #
    # logger.info(f"Numeric response is {int_val=}")

    return

def read_cmd():
    """
    """

    #01 03 03 00 00 00 8E 45

    cmd_base = [0x01,     # device address
                0x03,     # read the instruction number of register.
                0x03, 0,  # read the special defined address of the common register bank.
                0, 0]     # Dummy vals

    response = send_cmd_bytes(cmd_base)

    # logger.info(f"RESPONSE length : {len(response)}, {type(response)}")
    # for  e_idx, e in enumerate(response):
    #     if not e:
    #         continue
    #     logger.info(f"incoming response[{e_idx}] is {type(response[e_idx])}: {ord(response[e_idx])} Check: {repr(response[e_idx])}")


    # logger.info(f"READ RESPONSE : " + str([ f'{ord(x):#02X}' for x in response if x]))
    logger.info(f"READ RESPONSE : " + str(' '.join('%02x'%ord(i) for i in response if i)))

    # try:
    #     logger.info(f"final RESPONSE : {[hex(x) for x in response]}")
    # except TypeError:
    #     logger.info(f"final RESPONSE NON-ARRAY: {response}")
    #     pass


    # response_val = bytes(response[5:9])
    # response_val_str = b''.join(response[5:9])
    # response_val_str = '%02X'.join(response[5:9])
    # response_val_str = f"{format(response[5], '%02X')}"
    # logger.info(f"{response=}")

    response_int = int.from_bytes([ord(x) for x in response[5:9]], "big")
    logger.info(f"Response as integer {type(response_int)}: {response_int}")

    milivolts = int.from_bytes([ord(x) for x in response[5:8]], "big")

    milliamps = int.from_bytes([ord(x) for x in response[8:11]], "big")
    logger.info(f"READ milliamps: " + str(''.join('%02x' % ord(i) for i in response[8:11] if i)) + f" which is {milliamps} milliamps")

    mode_state = ord(response[3])
    state = mode_state & 0x1
    mode = mode_state >> 1
    if mode == 0:
        mode_str = "CV"
    elif mode == 1:
        mode_str = "CC"
    elif mode == 2:
        mode_str = "CR"
    elif mode == 3:
        mode_str = "CP"
    else:
        logger.error(f"ERROR: unrecognized pattern for mode_state: {mode:#x}")

    rv = {"state": state,
          "mode_str": mode_str,
          "volts": milivolts/1000,
          "amps": milliamps/1000,
          "watts":  round((milivolts/1000) * (milliamps/1000), 2)}

    return rv


def main():
    """main"""
    global logger, po

    # logger = modbus_tk.utils.create_logger("console")
    logger = create_logger("console")

    po = serial.Serial(port=PORT, baudrate=115200, timeout=0.5) # , timeout=0.2)

    logger.info(f"Set Load OFF ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    # Capture VOC
    VOC_readings = read_cmd()
    logger.info(f"Readings: {VOC_readings}")

    time.sleep(3)

    logger.info(f"set CR mode: (Constant Resistance)")
    send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])


    logger.info(f"set initial Load resistance ")
    for r in range(200, 0, -10):
        logger.info(f"Set to {r/10} ohms")
        send_cmd(cmd_dict["CR_SETTING"], r)
    print()

    '''
    logger.info(f"Try to set Load Ohms")
    for r in range(200, 0, -10):
        logger.info(f"Set to {r/10} ohms")
        send_cmd(0x011A, r) 
    send_cmd(0x011A, 0)
    print()
    time.sleep(3)
    '''

    #01 03 03 00 00 00 8E 45      read voltage, current
    readings = read_cmd()
    logger.info(f"Readings: {readings}")



    sys.exit()


if __name__ == "__main__":
    main()
