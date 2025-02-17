

from django import forms


from instructor.models import User

from django.contrib.auth.forms import UserCreationForm


class StudentCreateForm(UserCreationForm):

    class Meta:

        model=User

        fields=["username","password1","password2","email"]


class LoginForm(forms.Form):

    username=forms.CharField()

    password=forms.CharField()
    
class ContactForm(forms.Form):
    
    Name=forms.CharField()
    
    Email=forms.EmailField()
    
    Message=forms.Textarea()

    