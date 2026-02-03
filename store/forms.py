from decimal import Decimal
from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    coupon_code = forms.CharField(required=False, max_length=30)

    class Meta:
        model = Order
        fields = [
            'full_name',
            'phone',
            'email',
            'address',
            'city',
            'state',
            'postal_code',
            'notes',
            'payment_method',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_coupon_code(self):
        code = self.cleaned_data.get('coupon_code', '').strip().upper()
        return code

    def clean(self):
        cleaned = super().clean()
        cleaned['coupon_code'] = cleaned.get('coupon_code', '').strip().upper()
        return cleaned
