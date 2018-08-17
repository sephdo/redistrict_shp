import os
from tkinter import filedialog

def getInfile():
    return filedialog.askopenfilename(filetypes=[('CSV or DRF files','*.csv;*.drf')])
def getOutfile(infile=None):
    initialdir = os.path.dirname(infile) if infile else None
    initialfile = os.path.basename(infile).split('.')[0] if infile else 'shp_output'
    return filedialog.asksaveasfilename(defaultextension='.zip',
                                     initialdir=initialdir,
                                     initialfile=initialfile,
                                     filetypes=[('ZIP','*.zip')])
