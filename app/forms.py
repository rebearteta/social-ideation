# -*- coding: UTF-8 -*-
from django import forms
from app.models import ParticipaUser
import choices

class SignInForm (forms.Form):
   first_name = forms.CharField(label = "Nombre(s)", max_length=100)
   last_name = forms.CharField(label = 'Apellido(s)', max_length=100)
   email = forms.EmailField(label = "E-mail", widget=forms.EmailInput)
   platform = forms.ChoiceField( choices=(('','---Seleccione su canal---'),('Facebook', 'Facebook'),('IdeaScale','IdeaScale')), label="Canal de participación", widget=forms.Select(attrs = {'onchange' : "showFormFields();",}))
   birthdate = forms.DateField(label = 'Fecha de Nacimiento', widget=forms.DateInput)
   #age = forms.ChoiceField(choices=choices.GRUPOS_ETARIOS, label = "Edad")
   sex = forms.ChoiceField(choices=choices.SEXOS, label = "Sexo", widget=forms.Select(attrs = {'onchange' : '$("#id_sex option[value=\'\']").remove();',}))
   city = forms.ChoiceField(choices=choices.CIUDADES, label = "Ciudad de Residencia", widget=forms.Select(attrs = {'onchange' : '$("#id_city option[value=\'\']").remove();',}))
"""
class MyModelForm(SignInForm):
    class Meta:
        model = ParticipaUser
        widgets = {
            'birthdate': forms.TextInput(attrs={'type': 'date'}),
        }
"""
