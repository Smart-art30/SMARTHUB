from django import forms
from .models import FeeItem

class FeeItemForm(forms.ModelForm):
    class Meta:
        model = FeeItem
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
