#!/usr/bin/env python
# -*- coding: utf_8 -*-


import os
# from os.path import  *
import os.path
from pathlib import Path
import argparse
import re
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
import pandas as pd
from tabulate import tabulate
from collections import OrderedDict
from operator import itemgetter

TEST_SHORTEN_FACTOR = 20
HIGH_CURRENT_SHORTEN_FACTOR = 20

SkipHighCurrentCheck=False

LOGGER = logging.getLogger("PV_Tester")

pp = pprint.PrettyPrinter(indent=4).pprint
pp_str = pprint.PrettyPrinter(indent=4).pformat
pp_str2 = pprint.PrettyPrinter(indent=2).pformat
'''
> ls /dev/*serial*
/dev/cu.usbserial  /dev/tty.usbserial
'''

PORT = '/dev/cu.usbserial' # /dev/cu.usbserial-14110'
DEFAULT_USER_OUTDIR = 'Downloads/PV_Panel_MPPT_Results'

test_steps = {
    "CV_SETTING": {"param_start": 0,
                    "param_end": 50000,
                    "param_step": 100},
    "CC_SETTING": {"param_start":1,
                    "param_end":1,
                    "param_step":1},
    "CR_SETTING": {"param_start":400,
                    "param_end": 1,
                    "param_step": -1},
    "CW_SETTING": {"param_start":1,
                    "param_end": 1,
                    "param_step": 1},
}

INTER_STEP_SEC = 0.01

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
    # po = serial.Serial(port=PORT, baudrate=9600, timeout=0.25) # , timeout=0.2)
    po = serial.Serial(port=PORT, baudrate=115200, timeout=0.25) # , timeout=0.2)

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


def read_cmd(panelSN, idx, prog_value):
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

    # rv = {"idx": idx,
    #       "volts": milivolts/1000.0,
    #       "amps": milliamps/1000.0,
    #       "watts":  round((milivolts/1000.0) * (milliamps/1000.0), 2),
    #       "prog_value": prog_value,
    #       "state": state,
    #       "mode_str": mode_str,
    #       "panelSN": panelSN,
    #       }

    rv = OrderedDict([("idx", idx),
                      ("volts", milivolts/1000.0),
                      ("amps", milliamps/1000.0),
                      ("watts",  round((milivolts/1000.0) * (milliamps/1000.0), 2)),
                      # ("prog_value", prog_value),
                      ("state", state),
                      ("mode_str", mode_str),
                      ("panelSN", panelSN),
                      ('param', None),
                      ('Prog Val', None),
                      ('Prog Units', None),
                      ('timestamp', None)])

    return rv


def capture_ISC(panelSN, idx=-1):
    # Capture ISC
    param = 1
    logger.info(f"Capture Isc, Set to {param / 10.0} ohms")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)
    send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])
    send_cmd(cmd_dict["CR_SETTING"], param)
    send_cmd(cmd_dict["LOAD_ONOFF"], 1)
    time.sleep(0.5)

    # Capture ISC
    ISC_readings = read_cmd(panelSN, idx, param)
    ISC_readings['Prog Val'] = param / 10.0
    ISC_readings['Prog Units'] = "ohms"

    # logger.info(f"ISC Readings: {ISC_readings}")
    logger.info(f"ISC Readings: {ISC_readings['amps']} amps, "
                f"{ISC_readings['volts']} volts, {ISC_readings['watts']} watts, {ISC_readings['mode_str']} mode, "
                f"Programmed: {ISC_readings['Prog Val']} {ISC_readings['Prog Units']}")

    send_cmd(cmd_dict["LOAD_ONOFF"], 0)
    return(ISC_readings)


def capture_VOC(panelSN, idx=-1):
    logger.info(f"Capture Voc set to High Z (Load OFF)")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)
    param = 80000
    time.sleep(0.5)

    # Capture VOC
    VOC_readings = read_cmd(panelSN, idx, param)
    VOC_readings['Prog Val'] = param / 10.0
    VOC_readings['Prog Units'] = "ohms"

    # logger.info(f"Voc Readings: {VOC_readings}")
    logger.info(f"Voc Readings: {VOC_readings['amps']} amps, "
                f"{VOC_readings['volts']} volts, {VOC_readings['watts']} watts, {VOC_readings['mode_str']} mode, "
                f"Programmed: {VOC_readings['Prog Val']} {VOC_readings['Prog Units']}")

    return VOC_readings


def timestamp():
    ts_str =  f"{datetime.now().strftime('%Y%m%d_%H%M%S.%f')}"
    return ts_str[:-4]


def run_test_type(panelSN, type):

    global logger, po

    '''
    "CV_SETTING": 0x0112,
    "CC_SETTING": 0x0116,
    "CR_SETTING": 0x011A,
    "CW_SETTING": 0x011E,
    '''

    param_start = test_steps[type]['param_start']
    param_end = test_steps[type]['param_end']
    param_step = test_steps[type]['param_step']
    test_readings = []

    index_offset = 0
    VOC_readings = capture_VOC(panelSN, index_offset)
    VOC_readings['timestamp'] = "TS "+str(timestamp())
    VOC_readings['param'] = "VOC"
    VOC_readings['Peak'] = ""
    index_offset += 1
    test_readings.append(VOC_readings)

    ISC_readings = capture_ISC(panelSN, index_offset)
    ISC_readings['timestamp'] = "TS "+str(timestamp())
    ISC_readings['param'] = "ISC"
    ISC_readings['Peak'] = ""
    index_offset += 1
    test_readings.append(ISC_readings)

    # logger.info(f"Readings: {VOC_readings}")

    value_divisor = None

    if type == "CR_SETTING":
        units= "ohms"
        logger.info(f"set CR mode: (Constant Resistance)")
        # send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])
        load_test_mode = mode_dict['CR']
        value_divisor = 10.0

    elif type == "CC_SETTING":
        units= "amps"
        logger.info(f"set CC mode: (Constant Current)")
        # send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CC'])
        load_test_mode = mode_dict['CC']
        value_divisor = 1000.0

    elif type == "CV_SETTING":
        units= "volts"
        logger.info(f"set CV mode: (Constant Voltage)")
        # send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CV'])
        load_test_mode = mode_dict['CV']
        value_divisor = 1000.0

    elif type == "CW_SETTING":
        units= "watts"
        logger.info(f"set CE mode: (Constant Wattage)")
        # send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CW'])
        load_test_mode = mode_dict['CW']
        value_divisor = 1.0

    else:
        logger.error("UNRECOGNIZED test type")
        return


    # logger.info(f"Set Load OFF")
    # send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    if not SkipHighCurrentCheck:
        # EXPERIMENT with Getting Highest Current

        high_param_start = test_steps['CR_SETTING']['param_start']
        high_param_end   = test_steps['CR_SETTING']['param_end']
        high_param_step  = test_steps['CR_SETTING']['param_step']

        logger.info(f"HIGH Sweep: Start @ {high_param_start}, End @ {high_param_end}, Step {high_param_step}")

        steps = len(range(high_param_start, high_param_end, high_param_step * HIGH_CURRENT_SHORTEN_FACTOR))

        high_readings = []
        # for param_idx, param in enumerate(range(high_param_start, high_param_end, high_param_step*10)):
        param_idx=0
        for par_idx, param in enumerate(range(high_param_start, high_param_end, high_param_step * HIGH_CURRENT_SHORTEN_FACTOR)):
            if par_idx == 0:
                logger.info(f"TURNING LOAD OFF")
                send_cmd(cmd_dict["LOAD_ONOFF"], 0)
                # time.sleep(0.5)
                send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])
                # time.sleep(0.5)

            # logger.info(f"HIGH Step {param_idx} of {steps} --> {param /10} ohms")
            send_cmd(cmd_dict['CR_SETTING'], param)
            if par_idx == 0:
                logger.info(f"TURNING LOAD ON")
                send_cmd(cmd_dict["LOAD_ONOFF"], 1)
                # send_cmd(cmd_dict["LOAD_MODE"], mode_dict['CR'])

            high_reading = read_cmd(panelSN, param_idx, param)
            # logger.info(f"Got: {high_reading=}")
            high_reading['param'] = "RES LOAD CR"
            high_reading['Prog Val'] = param / 10.0
            high_reading['Prog Units'] = "ohms"
            high_reading['timestamp'] = "TS "+str(timestamp())
            high_reading['Peak'] = ""   
            logger.info(f"HIGH Step {param_idx} of {steps} --> {param /10} ohms: {high_reading['amps']} amps, "
                        f"{high_reading['volts']} volts, {high_reading['watts']} watts, {high_reading['mode_str']} mode, "
                        f"Programmed: {high_reading['Prog Val']} {high_reading['Prog Units']}")
            high_readings.append(high_reading)

            param_idx += 1

        # logger.info(f"HIGH Readings: \n{pp_str(high_readings)}")
        # logger.info(f"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        highest_current = max(high_readings, key=lambda x: x['amps'])
        print(f"{80*'-'}\n"
                    f"CR to find values @ peak amps: @ {highest_current['amps']} Amps"
                    f"@ {highest_current['volts']} Volts, "
                    # f"{highest_current['Prog Val']/10.0} Ohms, {highest_current['watts']} Watts"
                    f"\n{80*'-'}")
    else:
        highest_current = None
        high_readings=[]


    logger.info(f"{type=}: from {param_start} to {param_end}, {param_step=}")
    steps = len(range(param_start, param_end, param_step * TEST_SHORTEN_FACTOR))

    target_reached_flag = None
    for param_idx, param in enumerate(range(param_start, param_end, param_step * TEST_SHORTEN_FACTOR)):
        if not target_reached_flag and  param > 38000:
            logger.info(f"Reached 38 Volts")
            target_reached_flag = True;

        if param_idx == 0:
            logger.info(f"TURNING LOAD OFF")
            send_cmd(cmd_dict["LOAD_ONOFF"], 0)
            # time.sleep(0.5)
            send_cmd(cmd_dict["LOAD_MODE"], load_test_mode)
            send_cmd(cmd_dict["LOAD_ONOFF"], 1)
            # time.sleep(0.5)

        if value_divisor is not None:
            param_disp = param / value_divisor
        else:
            param_disp = param

        # logger.info(f"Step {param_idx} of {steps}  {type}--> {param_disp} {units}")
        send_cmd(cmd_dict[type], param)
        time.sleep(INTER_STEP_SEC)
        readings = OrderedDict()
        readings = read_cmd(panelSN, (index_offset + param_idx), param)
        readings['param'] = type
        readings['Prog Val'] = param / value_divisor
        readings['Prog Units'] = units
        readings['timestamp'] = "TS "+str(timestamp())
        readings['Peak'] = ""

        logger.info(f"Test Step {param_idx} of {steps} --> {readings['amps']} amps, "
                    f"{readings['volts']} volts, {readings['watts']} watts, {readings['mode_str']} mode, "
                    f"Programmed: {readings['Prog Val']} {readings['Prog Units']}")

        test_readings.append(readings)
        # logger.info(f"Readings: {readings}")

    logger.info(f"Set Load OFF ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    # print(f"Test Results:\n {pp_str(test_readings)}")
    # print(f"Test Results:\n {[pp_str(x) for x in test_readings]}")
    # print(f"Test Results:\n {test_readings}")


    max_idx, max_member = max(enumerate(test_readings), key=lambda item: item[1]['watts'])

    test_readings[max_idx]['Peak'] = "MAX"

    return test_readings, high_readings, highest_current


def main(arguments=None):
    """main"""
    global logger, po, SkipHighCurrentCheck

    logger = create_logger("console")
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # parser.add_argument('infile', help="Input file")  # type=argparse.FileType('r'))
    # parser.add_argument('-o', '--outfile', help="Output file",
    #                     default=sys.stdout, type=argparse.FileType('w'))

    parser.add_argument('--sn',
                       dest='serial_num',
                       default=os.environ.get('SKIP_SN', f'NONE_{timestamp()}'),
                       # default=os.environ.get('SKIP_SN', None),
                       action="store_const",
                       const=f'SN_SKIP_{timestamp()}',
                       help=(f"Use provides S/N or env's 'SKIP_SN' (currently {os.environ.get('SKIP_SN', ' ')}"))

    parser.add_argument('--skip_high_current' ,
                       dest='skip_high_current',
                       default=False,
                       action="store_const",
                       const=True,
                       help=(f"Skip High Current via Constant Resistance"))

    parser.add_argument('--results_dir',
                       nargs=1,
                       dest='results_dir',
                       default=[os.environ.get('OUTDIR', os.path.join(Path.home(), DEFAULT_USER_OUTDIR))],
                       help=(f'Dir for storing results: (or use \'OUTDIR\': Defaults to {os.path.join(Path.home(), DEFAULT_USER_OUTDIR)})'))

    args = parser.parse_args(arguments)

    # Convert list to string
    args.results_dir = args.results_dir[0]

    SkipHighCurrentCheck = args.skip_high_current

    logger.info(f"ARGS:  {args=}")


    po = serial.Serial(port=PORT, baudrate=115200, timeout=0.2) # , timeout=0.2)

    logger.info(f"Set Load OFF ")
    send_cmd(cmd_dict["LOAD_ONOFF"], 0)

    if (re.match("SN_SKIP.*", args.serial_num)) : #  or
        # re.match("NONE_.*", args.serial_num) ):

        panelSN = args.serial_num
    else:
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


    # results = run_test_type(panelSN, "CR_SETTING", START_RESISTANCE, END_RESISTANCE, RESISTANCE_STEP)
    results, high_readings, high_reading = run_test_type(panelSN, "CV_SETTING")

    header = list(results[0].keys())

    logger.info(f"\nHeader Rows: {header}\n")

    # print(f"results=\n{pp_str(results)}")

    os.makedirs(args.results_dir, exist_ok=True)

    file_name_base = f"MPPT_Test_{panelSN}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    test_data_file_name =  os.path.join(args.results_dir, f"{file_name_base}")

    logger.info(f"panelSN is {panelSN}\n")
    with open(test_data_file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"\nResults in {test_data_file_name}\n")

    high_current_data_file_name =  os.path.join(args.results_dir, f"{file_name_base}_high_current")
    with open(high_current_data_file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(high_readings)

    lst_str_cols = ['timestamp']
    dict_dtypes = {x: 'str' for x in lst_str_cols}
    df = pd.read_csv(test_data_file_name, dtype=dict_dtypes)

    # logger.info(f"\n-----FINAL RESULTS: {datetime.now().strftime('%Y%m%d %H:%M:%S')} Panel {panelSN} "
    #             f"@ {r_at_max_w/10.0} ohms, {v_at_max_watts} volts,  MAX WATTS: {max_watts}\n{80*'-'}\n")

    # logger.info(f"\n-----FINAL RESULTS: ")
    # print(f"{tabulate([df['watts'] == df['watts'].max()], headers=header )}")   # df.columns

    # print(f"{30*'+'}\n" + df + f"\n{30*'+'}")
    print(f"TEST DATA {30*'+'}\n")

    # pd.set_option('display.max_columns', 20)  # or 1000
    # pd.set_option('display.max_rows', 1000)  # or 1000
    # pd.set_option('display.max_colwidth', 200)  # or 199

    # print(df)
    print(f"{tabulate(df, headers=df.columns)}")


    df = pd.read_csv(high_current_data_file_name, dtype=dict_dtypes)

    # print(f"{30*'+'}\n" + df + f"\n{30*'+'}")
    print(f"\n{30*'~'} HIGH CURRENT CHECK DATA {30*'~'}")

    print(f"{tabulate(df, headers=df.columns)}")



if __name__ == "__main__":
    main(sys.argv[1:])
