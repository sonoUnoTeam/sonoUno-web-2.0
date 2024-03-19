# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 08:30:39 2024

@author: JMCasado
"""

#import micropip

#General import
import os
import argparse
import glob
import numpy as np
import datetime
import matplotlib.pyplot as plt
import math
import pandas as pd

#await micropip.install("pandas")

#Local import
from data_export.data_export import DataExport
from data_import.data_import import DataImport
from sound_module.simple_sound import simpleSound
from data_transform.predef_math_functions import PredefMathFunctions

# Instanciate the sonoUno clases needed
_dataexport = DataExport(False)
_dataimport = DataImport()
_simplesound = simpleSound()
_math = PredefMathFunctions()

# Sound configurations, predefined at the moment
_simplesound.reproductor.set_continuous()
_simplesound.reproductor.set_waveform('celesta')
_simplesound.reproductor.set_time_base(0.05)
_simplesound.reproductor.set_min_freq(300)
_simplesound.reproductor.set_max_freq(1500)

# The argparse library is used to pass the path and extension where the data
# files are located
parser = argparse.ArgumentParser()
# Receive the extension from the arguments
parser.add_argument("-t", "--file-type", type=str,
                    help="Select file type.",
                    choices=['csv', 'txt'])
# Receive the directory path from the arguments
parser.add_argument("-d", "--directory", type=str,
                    help="Indicate a directory to process as batch.")
# Indicate to save or not the plot
parser.add_argument("-p", "--save-plot", type=bool,
                    help="Indicate if you want to save the plot (False as default)",
                    choices=[False,True])
# Alocate the arguments in variables, if extension is empty, select txt as
# default
args = parser.parse_args()
ext = args.file_type or 'csv'
#path = args.directory
path = args.directory
plot_flag = args.save_plot or True
# Print a messege if path is not indicated by the user
if not path:
    print('1At least on intput must be stated.\nUse -h if you need help.')
    exit()
# Format the extension to use it with glob
extension = '*.' + ext

#Init the plot
if plot_flag:
    # Create an empty figure or plot to save it
    #cm = 1/2.54  # centimeters in inches
    #fig = plt.figure(figsize=(5*cm, 1*cm), dpi=300)
    fig = plt.figure()
    # Defining the axes so that we can plot data into it.
    ax = plt.axes()
#Inits to generalize

# Loop to walk the directory and sonify each data file
now = datetime.datetime.now()
print(now.strftime('%Y-%m-%d_%H-%M-%S'))

# Open each file
data, status, msg = _dataimport.set_arrayfromfile(path, ext)
# Check if the data is ok
if data.shape[1]<2:
    print("Error reading file 1, only detect one column.")
    exit()
# Erase the names and turn to float
data_float = data.iloc[1:, :].astype(float)

# Generate the plot if needed
if plot_flag:
    # Configure axis, plot the data and save it
    # Erase the plot
    ax.cla()
    # First file of the column is setted as axis name
    x_name = str(data.iloc[0,0])
    ax.set_xlabel(x_name)
    # Separate the name file from the path to set the plot title
    #head, tail = os.path.split(filename)
    ax.plot(data_float.loc[:,0], data_float.loc[:,1], label='Linear functino')
    ax.legend()
    # Set the path to save the plot and save it
    plot_path = path[:-4] + '_plot.png'
    fig.savefig(plot_path)
    plt.pause(0.001)

"""
HASTA AQUÍ EL SIGUIENTE PASO, dejo el sonido para que lo tengan de referencia
"""






















# Normalize the data to sonify
x1, y1, status = _math.normalize(data_float.loc[:,0], data_float.loc[:,1], init=1)

# Reproduction
minval1 = float(np.abs(data_float.loc[:,1]).min())
maxval1 = float(np.abs(data_float.loc[:,1]).max())

ordenada = np.array([minval1, maxval1])

input("Press Enter to continue...")

for x in range (1, data_float.loc[:,0].size):
    # Plot the position line
    if not x == 1:
        line = red_line.pop(0)
        line.remove()
    abscisa = np.array([float(data_float.loc[x,0]), float(data_float.loc[x,0])])
    red_line = ax.plot(abscisa, ordenada, 'r')
    plt.pause(0.05)
    # Make the sound
    _simplesound.reproductor.set_waveform('sine')
    _simplesound.make_sound(y1[x], 1)

# Save sound
wav_name = path[:-4] + '_sound.wav'
#_simplesound.save_sound_multicol(wav_name, data_float1.loc[:,0], y1, y2, init=1)
# Print time
now = datetime.datetime.now()
print(now.strftime('%Y-%m-%d_%H-%M-%S'))

plt.pause(0.5)
# Showing the above plot
plt.show()
plt.close()
