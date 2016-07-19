from django import forms
import choices

class SignInForm (forms.Form):
   name = forms.CharField(label = "Nombre Completo", max_length=100)
   email = forms.EmailField(label = "E-mail")
   edad = forms.ChoiceField(choices=choices.GRUPOS_ETARIOS, label = "Edad")
   sexo = forms.ChoiceField(choices=choices.SEXOS, label = "Sexo")
   ciudad = forms.ChoiceField(choices=choices.CIUDADES, label = "Ciudad de Residencia")
   
