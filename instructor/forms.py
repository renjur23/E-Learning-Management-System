from django.contrib.auth.forms import UserCreationForm

from django.forms import inlineformset_factory

from instructor.models import User,Course,Category,Module,Lesson

from django import forms


class InstructorCreateForm(UserCreationForm):

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(InstructorCreateForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None


class ModuleForm(forms.ModelForm):

    class Meta:

        model=Module

        fields=["title"]

LessonFormSet=inlineformset_factory(
                                    Module,
                                    Lesson,                                    
                                    fields=["title","video"],
                                    extra=2,
                                    can_delete=False                                 
                                    
                                    )




