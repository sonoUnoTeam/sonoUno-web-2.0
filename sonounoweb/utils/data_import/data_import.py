#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Dec 12 2017

@author: sonounoteam (view licence)
"""

import numpy as np
import pandas as pd


class DataImportColumns (object):
    
    
    def __init__(self):
        
        """
        This class open multiple columns files (csv or txt) using the provided
        path. Different methods allows to recover the data set and its title.
        """
        # Parameters initialization with setter methods
        self.set_datafilename('')
        
    def set_datafilename(self, filename): 
        
        """
        This method set the internal filename of the data opened.
        It not modify the file on the operative system.
        """
        self._filename = filename
        
    def get_datafilename(self): 
        
        """
        This method return the file name of the data imported.
        """
        return self._filename
    
    def set_arrayfromfile(self, archivo, filetype):
        
        """
        This method import a txt or csv data file into a dataFrame, check 
        if the columns have names if not one generic name is set, and check 
        that the names don't have spaces, if there is any space the program
        delete it.
        """
        if filetype == 'txt':
            try:
                with open (archivo, 'r') as txtfile:
                    data = pd.read_csv(txtfile, delimiter = '\t', header = None)
            except IOError as Error:
                msg = 'Cannot open the txt file, this is an IO Error. \
                    Check the error file for more information.'
                return None, False, msg
            except Exception as Error:
                msg = 'Cannot open the txt file. Check the error file for \
                    more information.'
                return None, False, msg
            # Check if the data are imported in the right way, if not try to
            # import as space separated.
            if data.shape[1] < 2:
                with open (archivo, 'r') as txtfile:
                    data = pd.read_csv(txtfile, sep = ' ', header = None)
                if data.shape[1] < 2:
                    msg = 'Check the delimiter on the data, txt separator \
                        must be "\t" or " ".'
                    return None, False, msg
        elif filetype == 'csv':
            try:
                with open (archivo, 'r') as csvfile:
                    data = pd.read_csv(csvfile, delimiter = ',', header = None)
            except IOError as Error:
                msg = 'Cannot open the csv file, this is an IO Error. \
                    Check the error file for more information.'
                return None, False, msg
            except Exception as Error:
                msg = 'Cannot open the txt file. Check the error file for \
                    more information.'
                return None, False, msg
            # Check if the data are imported in the right way, if not try to
            # import as ; separated.
            if data.shape[1] < 2:
                with open (archivo, 'r') as csvfile:
                    data = pd.read_csv(csvfile, sep = ';', header = None)
                if data.shape[1] < 2:
                    msg = 'Check the delimiter on the data, csv separator \
                        must be "," or ";".'
                    return None, False, msg
        else:
            msg = 'The data type provided is unknow.'
            return None, False, msg
        # If the data are imported correctly, continue checking the columns
        # names.
        if type(data.loc[0,0]) is not str:
            # Walk the first row and set generic column names
            for i in range (0, data.shape[1]):
                if i == 0:
                    xlabel = pd.DataFrame({i : ['Column'+str(i)]})
                else:
                    xlabel.loc[:, i] = 'Column' + str(i)
            data = pd.concat([xlabel, data]).reset_index(drop = True)
        # This part check if the column names present spaces and if it has, 
        # it delete it.
        for i in range (0, data.shape[1]):
            data.iloc[0,i] = data.iloc[0,i].replace(' ','')
        msg = 'The data was correctly imported.'
        return data, True, msg
