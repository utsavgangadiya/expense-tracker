# tracker/forms.py
from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'description']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'f-input',
                'placeholder': 'Enter title'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'f-input',
                'placeholder': 'Enter amount'
            }),
            'category': forms.Select(attrs={
                'class': 'f-input'
            }),
            'date': forms.DateInput(attrs={
                'class': 'f-input',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'f-input',
                'placeholder': 'Enter description',
                'rows': 3
            }),
        }
