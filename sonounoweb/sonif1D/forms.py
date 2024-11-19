from django import forms

class ArchivoForm(forms.Form):
    archivo = forms.FileField(label='Seleccione un archivo CSV o TXT')