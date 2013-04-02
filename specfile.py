#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SpecfileData object to work with SPEC files from Certified Scientific Software (http://www.certif.com/)

Requirements
------------
- specfilewrapper from PyMca distribution (http://pymca.sourceforge.net/)

TODO
----
- implement get_map() method to extract a 2D plane, e.g. a RIXS plane
- better handling the scan types to create specific labels in the larch group
"""

__author__ = "Mauro Rovezzi"
__email__ = "mauro.rovezzi@gmail.com"
__version__ = "2013-04-01"

import os, sys, warnings
import numpy as np

try:
    from PyMca import specfilewrapper as specfile
except ImportError:
    print "Error: cannot load specfile -- PyMca broken?"
    sys.exit(1)

class SpecfileData(object):
    "SpecFile object"
    def __init__(self, fname=None):
        """reads the given specfile"""
        #TODO: separate fname from working dir (wdir)
        if fname is None:
            raise NameError('Please, provide a SPEC data file to load!')
        elif not os.path.isfile(fname):
            raise OSError("File not found: '%s'" % fname)
        else:
            self.fname = fname
            if hasattr(self, 'sf'):
                pass
            else:
                self.sf = specfile.Specfile(fname) #sf = specfile file
                print "Loaded SPEC file: {0}".format(fname)
                print "The number of scans is: {0}".format(self.sf.scanno())
            
    def get_scan(self, scan=None, cntx=None, csig=None, cmon=None, csec=None, scnt=None):
        """ get a single scan

        Parameters
        ----------
        scan : scan number to get [integer]
        cntx : counter for x axis, motor scanned [string]
        csig : counter for y axis, signal [string]
        cmon : counter for monitor/normalization [string]
        csec : counter for time in seconds [string]
        scnt : scan type [string]
 
        Returns
        -------
        scan_datx : 1D array with x data
        scan_daty : 1D array with y data
        scan_mots : dictionary with motors positions for the given scan
        
        """
        if scan is None:
            raise NameError('Provide the scan number to get [integer]')
        if cntx is None:
            raise NameError('Provide the counter for x, the abscissa [string]')
        if csig is None:
            raise NameError('Provide the counter for signal [string]')
        if cmon is None:
            raise NameError('Provide the counter for monitor/normalization [string]')
        if csec is None:
            _iscps = False
            warnings.warn('No counter for time in seconds [string]: the signal will not be expressed in cps')
        else:
            _iscps = True

        #select the given scan number
        self.sd = self.sf.select(str(scan)) #sd = specfile data
        
        ## x-axis
        if scnt is None:
            #try to guess the scan type if it is not given
            #this condition should work in case of an energy scan
            if ('ene' in cntx.lower()):
                #this condition should detect if the energy scale is KeV
                if (self.sd.datacol(cntx).max() - self.sd.datacol(cntx).min()) < 3.0:
                    scan_datx = self.sd.datacol(cntx)*1000
            else:
                scan_datx = self.sd.datacol(cntx)
        else:
            raise NameError('Provide a correct scan type string')

        ## y-axis
        if _iscps:
            scan_daty = (self.sd.datacol(csig)/self.sd.datacol(cmon))*(np.mean(self.sd.datacol(cmon))/self.sd.datacol(csec))
        else:
            scan_daty = self.sd.datacol(csig)/self.sd.datacol(cmon)
        
        ## and the motors dictionary
        scan_mots = dict(zip(self.sf.allmotors(), self.sd.allmotorpos()))
        
        return scan_datx, scan_daty, scan_mots

### LARCH ###
def spec_getscan2group(fname, scan=None, cntx=None, csig=None, cmon=None, csec=None, scnt=None, _larch=None):
    """simple mapping of SpecfileData to larch groups"""
    if _larch is None:
        raise Warning("larch broken?")

    specscan = SpecfileData(fname)
    group = _larch.symtable.create_group()
    group.__name__ = 'SPEC data file %s' % fname
    x, y, motors = specscan.get_scan(scan, cntx, csig, cmon, csec, scnt)
    setattr(group, 'x', x)
    setattr(group, 'y', y)
    setattr(group, 'motors', motors)

    return group

def registerLarchPlugin():
    return ('_io', {'read_specfile_scan': spec_getscan2group})

if __name__ == '__main__':
    """ testing this class """
    fname = 'specfile_test.dat'
    signal = 'zap_det_dtc'
    monitor = 'arr_I02sum'
    seconds = 'arr_seconds'
    counter = 'arr_hdh_ene'
    motor = 'Spec.Energy'
    motor_counter = 'arr_xes_en'
    t = SpecfileData(fname)
    x, y, motors = t.get_scan(3, cntx=counter, csig=signal, cmon=monitor, csec=seconds)
    import matplotlib.pyplot as plt
    plt.plot(x, y)
    plt.show()
