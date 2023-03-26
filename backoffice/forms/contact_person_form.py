from django import forms
from django.forms import formset_factory


class ContactPersonForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    tel = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))


ContactPersonFormSet = formset_factory(ContactPersonForm, extra=0, min_num=1, can_delete=True)
