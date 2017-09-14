from django.forms import ModelForm
from .models import Personaldata

# Create the form class.
class personaldataForm(ModelForm):
    class Meta:
        model = Personaldata
        fields = ['name', 'title', 'birth_date']
