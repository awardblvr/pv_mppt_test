#!/usr/bin/env python

"""
 Import MPPT CSV data and plot it.

 CSV format:
 Volts,volts,amps,watts,state,mode_str,panelSN,resistance,timestamp
 29.646,29.646,0.0,0.0,0,CR,B41J00052893,100000,20210913_120014.79
 14.267,14.267,0.354,5.05,1,CR,B41J00052893,40.0,20210913_120016.16

"""

from __future__ import print_function
import os
import sys
import argparse
from datetime import datetime as dt
import time
import pandas as pd
from numpy import *
import numpy as np
from mpl_toolkits.axes_grid1 import host_subplot
from mpl_toolkits import axisartist
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from csv import reader
import pprint

pp = pprint.PrettyPrinter(indent=4, depth=4).pprint
pp_str = pprint.PrettyPrinter(indent=4, depth=4).pformat

def plot_df(df):
    '''
       0      1        2      3       4       5          6             7            8
    0  Volts,  volts,   amps,  watts,  state,  mode_str,  panelSN,      resistance,  timestamp
    1  29.646,  29.646, 0.0,   0.0,    0,      CR,        B41J00052893, 100000,      20210913_120014.79   <--Voc
    2  14.267,  14.267, 0.354, 5.05,   1,      CR,        B41J00052893, 40.0,        20210913_120016.16
    '''
    print(df)
    title_sn = df['panelSN'][1]

    volt_series = df['Volts'][1:]

    std_voltage_series = np.arange(50, 0, 0-(50.0 /volt_series.size ))

    print(f"{volt_series.size=}")
    print(f"std_voltage_series-> size {len(std_voltage_series)}, {std_voltage_series})")

    amps_series = df['amps'][1:]
    watts_series = df['watts'][1:]
    ohms_series = df['resistance'][1:]

    # print(volt_series)

    fig, ax1 = plt.subplots()


    color = 'tab:red'
    ax1.set_xlabel('Voltage')
    # ax1.set_ylabel('Current', color=color)
    ax1.set_ylim(1, 6)
    # ax1.plot(volt_series, amps_series, color=color)
    ax1.plot(std_voltage_series, amps_series, color=color, label='Current')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    # ax2.set_ylabel('Watts', color=color)  # we already handled the x-label with ax1
    # ax2.plot(volt_series, watts_series, color=color)
    ax2.plot(std_voltage_series, watts_series, color=color, label='Watts')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title(f"Panel S/N {title_sn}")
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.legend()
    plt.show()

def get_and_plot_mppt(df):

    # IL = array(ItemList)
    
    host = host_subplot(111, axes_class=axisartist.Axes)   # (1 row, 1 column, plot number 1)
    plt.subplots_adjust(right=0.75)

    par1 = host.twinx()
    # par2 = host.twinx()

    # par2.axis["right"] = par2.new_fixed_axis(loc="right", offset=(60, 0))

    par1.axis["right"].toggle(all=True)
    # OUT_FOR_SINGLE par2.axis["right"].toggle() #all=True)

    '''
       0      1        2      3       4       5          6             7            8
    0  Volts,  volts,   amps,  watts,  state,  mode_str,  panelSN,      resistance,  timestamp
    1  29.646,  29.646, 0.0,   0.0,    0,      CR,        B41J00052893, 100000,      20210913_120014.79   <--Voc
    2  14.267,  14.267, 0.354, 5.05,   1,      CR,        B41J00052893, 40.0,        20210913_120016.16
    '''

    # print
    # '\n'.join(['%i: %s' % (n, l[n]) for n in xrange(len(l))])

    # print(f"Current:     {['%.2f'.format(x[0]) for x in IL[2:]]}, \n    {[x[2] for x in `IL`[2:]]}")
    print("Voltage:  %s"%(", ".join(["%.1f"%float(x[0]) for x in IL[2:]]))) # , \n    {[x[2] for x in IL[2:]]}")
    print("Current:  %s"%(", ".join(["%.1f"%float(x[2]) for x in IL[2:]]))) # , \n    {[x[2] for x in IL[2:]]}")
    #  OUT_FOR_SINGLE print(f"Watts:       {[x[3] for x in IL[2:]]}, \n    {[x[3] for x in IL[2:]]}")
    #  OUT_FOR_SINGLE print(f"Resistance:  {[x[7] for x in IL[2:]]}, \n    {[x[7] for x in IL[2:]]}")


    p1, = host.plot([float(x[0]) for x in IL[2:]], [float(x[2]) for x in IL[2:]], label="Current")
    p2, = par1.plot([float(x[0]) for x in IL[2:]], [float(x[3]) for x in IL[2:]], label="Watts")
    #  OUT_FOR_SINGLE p3, = host.plot([x[7] for x in IL[2:]], [x[7] for x in IL[2:]], label="Resistance")

    xlim_min = 0 # min([x[0] for x in IL[2:]])
    xlim_max = 50 # max([x[0] for x in IL[2:]])
    print(f"X-Axis  {xlim_min=}, {xlim_max=}")

    ylim_min = min([x[2] for x in IL[2:]])
    ylim_max = max([x[2] for x in IL[2:]])
    print(f"Y-Axis  {ylim_min=}, {ylim_max=}")

    host.set_xlim( xlim_min, xlim_max)   # X Axis (Voltage)
    host.set_ylim( ylim_min, ylim_max)   # # Left Y Axis  (Current)
    par1.set_ylim( 0, 200)   # Right Y Axis 1 (Wattage)
    #  OUT_FOR_SINGLE  par2.set_ylim( IL[2][7], IL[-1][7])   # Right Y Axis 2 (Resistance)

    host.set_xlabel("Voltage")
    host.set_ylabel("Current (Amps)")
    par1.set_ylabel("Watts")
    #  OUT_FOR_SINGLE par2.set_ylabel("Load Resistance")

    host.legend()

    host.axis["left"].label.set_color(p1.get_color())
    par1.axis["right"].label.set_color(p2.get_color())
    #  OUT_FOR_SINGLE par2.axis["right"].label.set_color(p3.get_color())

    # from MAYBE related examples   axes.yaxis.set_major_locator(MaxNLocator(5))
    host.yaxis.set_major_locator(MaxNLocator(10))
    host.xaxis.set_major_locator(MaxNLocator(8))
    # par1.yaxis.set_major_locator(MaxNLocator(8))

    plt.show()

def main(arguments=None):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', help="Input file")  # type=argparse.FileType('r'))
    # parser.add_argument('-o', '--outfile', help="Output file",
    #                     default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args(arguments)

    # print(pp_str(args))

    # read csv file as a list of lists

    # with open(args.infile, 'r') as read_obj:
    #     # pass the file object to reader() to get the reader object
    #     csv_reader = reader(read_obj)
    #     # Pass reader object to list() to get a list of lists
    #     list_of_rows = list(csv_reader)
    #     # print(pp_str(list_of_rows))
    #     for i in list_of_rows:
    #         print(f"{i}")

    df = pd.read_csv(args.infile)

    # get_and_plot_mppt(df)

    plot_df(df)



if __name__ == '__main__':

    main(sys.argv[1:])
    # time.sleep(2.612)


    sys.exit(0)
