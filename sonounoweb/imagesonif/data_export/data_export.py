#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Dec 12 2017
Adapted for Django web application

@author: sonounoteam (view licence)
"""

import logging
import datetime
import os
from django.conf import settings

class DataExport(object):
    def __init__(self, log=False):
        """
        This class allows to export data and save the outputs of the software.
        Simplified version for Django web application.
        """
        self.log = log
        
        if self.log:
            # Use Django's logging configuration
            self.logger = logging.getLogger('imagesonif')
        
    def writeinfo(self, info):
        """
        This method prints information.
        """
        now = datetime.datetime.now()
        time = now.strftime('%H-%M-%S')
        msg = f'The time of the next information is: {time}\n{info}'
        
        if self.log:
            self.logger.info(msg)
        else:
            print(msg)
        
    def writeexception(self, e):
        """
        This method prints errors.
        """
        now = datetime.datetime.now()
        time = now.strftime('%H-%M-%S')
        info_msg = f'The time of the next exception is: {time}'
        
        if self.log:
            self.logger.info(info_msg)
            self.logger.exception(e)
        else:
            print(info_msg)
            print(e)
        
    def printoutput(self, message):
        """
        This method prints messages.
        """
        now = datetime.datetime.now()
        time = now.strftime('%H-%M-%S')
        msg = f'{time}: {message}'
        print(msg)
