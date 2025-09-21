# SonoUno Software

This development is powered by CONICET-Argentina and Universidad de Mendoza-Argentina.

<Img src="logos/logo_conicet.png" width="100"> <Img src="logos/iteda.jpeg" width="120"> <Img src="logos/ibio.jpeg" width="70"> <Img src="logos/eulogo2.png" width="70">

This work is partially supported by REINFORCE Project. REINFORCE has received funding from the European Union’s Horizon 2020 project call H2020-SwafS-2018-2020 under Grant Agreement no. 872859. The content of this website does not represent the opinion of the European Commission, and the European Commission is not responsible for any use that might be made of such.

## Description

The sonification technique proposed here is developed in Python, using the openCV library for image manipulation and the sonoUno sound library for the sonification process (included in the folder sound_module). The sonification involves sonifying the intensity of the image column with the same pitch variation as the 2D plot in sonoUno. The brightness value (white) corresponds to the highest tone and the darkest value (black) to the lowest tone (silence). Some examples are on the YouTube channel (https://www.youtube.com/@sonouno6873/shorts), and the Galery of sonoUno website (https://www.sonouno.org.ar/galaxy-sdss-j115845-43-002715-7/).

## Pre-requirements

1.	Check that you have python 3.x installed on your system running ‘python3’ or ‘python’ on a terminal. If you don’t have python:

For Mac: ```brew install python3```\
For Ubuntu: ```sudo apt install --upgrade python3```\
For Windows download the installer from: https://www.python.org/downloads/

Note: from here we use python3, you have to use python or python3 depending on the step before.

2.	Check that pip is installed with ‘python3 -m pip -V’. If not:

For Mac, pip is installed with python installation.\
For Ubuntu: ```sudo apt install python3-pip```\
For Windows, pip is installed with the executable.

3.	Install the libraries with pip:
        ```python3 -m pip install matplotlib numpy pandas pygame opencv-python```

## Running the script

To run the image sonification script, it has to be called from the command window and it opens a new window displaying the image, to sonify you have to press a key and a position bar will be shown during the sonification. From bash, go to the sonoUno folder where the script is located and type:

```python3 img_sonif.py -d "path_to_the_image_to_sonify"```

Once the window with the image appears, to start the sonification press enter, with the cursor on the image. 

For example, in my computer I write: ```python3 img_sonif.py -d "/Users/sonounoteam/Downloads/image.png"```

About the command to run the script: the ‘-d’ indicates the path of the image to be sonified. When the sonification display finished, the code saved the sound in the same folder as the image file with the same name, the label ‘_sound’ and in wav format (for example: ‘image_sound.wav’).
