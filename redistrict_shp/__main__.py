from .app import convert
#from .config import *
from .dialogs import getInfile, getOutfile

import argparse
import datetime
import tkinter
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', default=None)
    parser.add_argument('outfile', nargs='?', default=None)
    args = parser.parse_args()
    root = tkinter.Tk()
    root.withdraw()
    infile = args.infile
    outfile = args.outfile
    if not infile:
        print('Select input CSV or DRF file.')
    while not infile:
        infile = getInfile()
        if not infile:
            input('Input file not provided, press Enter to try again.')
    print('Input file is: {}'.format(infile))
    if not outfile:
        print('Select output ZIP file')
    while not outfile:
        outfile = getOutfile(infile)
        if not outfile:
            input('Output path not provided, press Enter to try again.')
    print('Output file is: {}'.format(outfile))
    print('Beginning conversion to .shp ...')
    t0 = datetime.datetime.now()
    print('Start time: {}'.format(t0))
    convert(infile,outfile)
    t1 = datetime.datetime.now()
    print('End time: {}'.format(t1))
    print('Processing time: {}'.format(t1-t0))
        
                
        
if __name__ == '__main__':
    main()
