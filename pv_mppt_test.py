#!/usr/bin/env python
# -*- coding: utf_8 -*-


import os
# from os.path import  *
import os.path

import sys
import time
# import datetime
from datetime import datetime
import serial
# import logging
from utils import *
# import struct
# from array import *
import traceback
import pprint
import csv

LOGGER = logging.getLogger("PV_Tester")

pp = pprint.PrettyPrinter(indent=4).pprint
pp_str = pprint.PrettyPrinter(indent=4).pformat
pp_str2 = pprint.PrettyPrinter(indent=2).pformat
'''
> ls /dev/*serial*
/dev/cu.usbserial  /dev/tty.usbserial
'''

PORT = '/dev/cu.usbserial-14110'
OUTDIR = '$HOME/Downloads/PV_Panel_MPPT_Results'

START_RESISTANCE =   400        # in ohms * 10
END_RESISTANCE   =   40
RESISTANCE_STEP  =   -5

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

    # logger.info(f"Final Cmd {[hex(x) for x in cmd]}, {cmd_len=}")

    # serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
    # Set read timeout to 3 Sec
    po = serial.Serial(port=PORT, baudrate=9600, timeout=0.25) # , timeout=0.2)

    bytes_written = po.write(cmd)
    # logger.info(f"{bytes_written=}")

    # time.sleep(0.25)

    read_buf = []
    read_buf_len = len(read_buf)

    startTimer = datetime.now()

    empty_reads = 0;
    while True:
        # if (datetime.datetime.now() - startTimer) > datetime.timedelta(seconds=2.0):
        #     logger.info(f"Timeout waiting for response to complete")
        #     break

        # read_buf.append(po.read())
        temp_buf = po.read()

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

    # logger.info(f"RESPONSE : {[hex((ord(x))) for x in response if x]}")

    # response_int = int.from_bytes([ord(x) for x in response[5:9]], "big")
    # logger.info(f"Response as integer {type(response_int)}: {response_int}")
    return


def read_cmd(panelSN):
    """
    """
    cmd_base = [0x01,     # device address
                0x03,     # read the instruction number of register.
                0x03, 0,  # read the special defined address of the common register bank.
                0, 0]     # Dummy vals

    response = send_cmd_bytes(cmd_base)

    # logger.info(f"READ RESPONSE : " + str(' '.join('%02x'%ord(i) for i in response if i)))

    response_int = int.from_bytes([ord(x) for x in response[5:9]], "big")
    # logger.info(f"Response as integer {type(response_int)}: {response_int}")

    milivolts = int.from_bytes([ord(x) for x in response[5:8]], "big")

    milliamps = int.from_bytes([ord(x) for x in response[8:11]], "big")
    # logger.info(f"READ milliamps: " + str(''.join('%02x' % ord(i) for i in response[8:11] if i)) + f" which is {milliamps} milliamps")

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

    rv = {"Volts": milivolts/1000.0,
          "volts": milivolts/1000.0,
          "amps": milliamps/1000.0,
          "watts":  round((milivolts/1000.0) * (milliamps/1000.0), 2),
          "state": state,
          "mode_str": mode_str,
          "panelSN": panelSN,}

    return rv


def run_test(panelSN=None):
    def timestamp():
        ts_str =  f"{datetime.now().strftime('%Y%m%d_%H%M%S.%f')}"
        return ts_str[:-4]

    global logger, po
    global START_RESISTANCE, END_RESISTANCE, RESISTANCE_STEP

    test_readings = []


    logger.info(f"set initial Load resistance ")
    r = 100000
    logger.info(f"Set to {r/10} ohms")
    send_cmd(cmd_dict["CR_SETTING"], r)
    time.sleep(0.5)


    # Capture VOC
    VOC_readings = read_cmd(panelSN)
    logger.info(f"Readings: {VOC_readings}")

    logger.info(f"set CR mode: (Constant Resistance)")
    send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])

    VOC_readings['resistance'] = r
    VOC_readings['timestamp'] = timestamp()
    test_readings.append(VOC_readings)

    logger.info(f"Set Load ON ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 1)

    logger.info(f"Run test for decreasing Load resistance ")

    # for r in range(200, 0, -10):
    # for r in range(400, 50, -5):
    logger.info(f"{START_RESISTANCE=}, {END_RESISTANCE=}, {RESISTANCE_STEP=}")
    for r in range(START_RESISTANCE, END_RESISTANCE, RESISTANCE_STEP):

        # readings=None
        logger.info(f"Set to {r/10.0} ohms")
        send_cmd(cmd_dict["CR_SETTING"], r)
        time.sleep((0.5))
        readings = read_cmd(panelSN)
        readings['resistance'] = r / 10.0
        readings['timestamp'] = timestamp()
        test_readings.append(readings)

        logger.info(f"Readings: {readings}")

    logger.info(f"Set Load OFF ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    # print(f"Test Results:\n {pp_str(test_readings)}")
    # print(f"Test Results:\n {[pp_str(x) for x in test_readings]}")
    # print(f"Test Results:\n {test_readings}")


    return test_readings


def main():
    """main"""
    global logger, po, OUTDIR

    logger = create_logger("console")

    po = serial.Serial(port=PORT, baudrate=115200, timeout=0.5) # , timeout=0.2)

    logger.info(f"Set Load OFF ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    panelSN = input("Panel S/N? :")

    while True:
        print(f"{panelSN=}")
        if len(panelSN) == 12:
            break
        print(f"Try again, or enter (blank) to quit")
        panelSN = input("Panel S/N? (or text) ")
        if len(panelSN):
            break
        if not len(panelSN):
            sys.exit()


    file_name = f"MPPT_Test_{panelSN}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_name =  os.path.join(OUTDIR, file_name)

    logger.info(f"panelSN is {panelSN}\n")

    results = run_test(panelSN)
    header = list(results[0].keys())

    with open(file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"\nResults in {file_name}\n")


    max_watts = 0.0
    r_at_max_w = 0
    v_at_max_watts = 0

    for i in results:
        if i['watts'] > max_watts:
            max_watts = i['watts'];
            r_at_max_w = i['resistance']
            v_at_max_watts = i['volts']

    logger.info(f"\n-----FINAL RESULTS: {datetime.now().strftime('%Y%m%d %H:%M:%S')} Panel {panelSN} "
                f"@ {r_at_max_w} ohms, {v_at_max_watts} volts,  MAX WATTS: {max_watts}\n{80*'-'}\n")



if __name__ == "__main__":
    main()
