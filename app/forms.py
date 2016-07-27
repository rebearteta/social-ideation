from django import forms
from app.models import ParticipaUser
import choices

class SignInForm (forms.Form):
   first_name = forms.CharField(label = "Nombre(s)", max_length=100)
   last_name = forms.CharField(label = 'Apellido(s)', max_length=100)
   email = forms.EmailField(label = "E-mail", widget=forms.EmailInput)
   birthdate = forms.DateField(label = 'Fecha de Nacimiento', widget=forms.DateInput)
   #age = forms.ChoiceField(choices=choices.GRUPOS_ETARIOS, label = "Edad")
   sex = forms.ChoiceField(choices=choices.SEXOS, label = "Sexo")
   city = forms.ChoiceField(choices=choices.CIUDADES, label = "Ciudad de Residencia")
"""
class MyModelForm(SignInForm):
    class Meta:
        model = ParticipaUser
        widgets = {
            'birthdate': forms.TextInput(attrs={'type': 'date'}),
        }
"""
