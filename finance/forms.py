from django import forms
from .models import FeeItem
from finance.models import SchoolPaymentMethod

class FeeItemForm(forms.ModelForm):
    class Meta:
        model = FeeItem
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, fee_structure=None, **kwargs):
        """
        Accept a fee_structure when initializing the form
        """
        super().__init__(*args, **kwargs)
        self.fee_structure = fee_structure
        if self.instance.pk is None and self.fee_structure:
            self.instance.fee_structure = self.fee_structure  

    def save(self, commit=True):
        """
        Ensure the fee_structure is assigned before saving
        """
        obj = super().save(commit=False)
        if self.fee_structure:
            obj.fee_structure = self.fee_structure
        if commit:
            obj.save()
        return obj





class SchoolPaymentMethodForm(forms.ModelForm):
    class Meta:
        model = SchoolPaymentMethod
        fields = ['method', 'details', 'notes']
        widgets = {
            'method': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
