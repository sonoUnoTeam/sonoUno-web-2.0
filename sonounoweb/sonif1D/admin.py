from django.contrib import admin

# Configuration to use matplotlib
from .models import MyModel

admin.site.register(MyModel)

# Register your models here.
