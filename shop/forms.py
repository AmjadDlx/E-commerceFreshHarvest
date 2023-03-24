from django.forms import ModelForm
from shop.models import ContactMessage

class ContactForm(ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['user_name', 'email', 'message',]