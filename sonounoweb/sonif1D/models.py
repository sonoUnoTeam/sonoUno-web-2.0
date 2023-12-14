from django.db import models

# Configuration to use matplotlib
from django_matplotlib import MatplotlibFigureField

class MyModel(models.Model):
    figure = MatplotlibFigureField(figure='my_figure')

# Create your models here.
