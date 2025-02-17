from django.shortcuts import render,redirect
from django.views.generic import View
from instructor.forms import InstructorCreateForm,LessonFormSet,ModuleForm

# Create your views here.
class InstructorCreateView(View):

    def get(self,request,*args,**kwargs):
        form_instance=InstructorCreateForm()
        return render(request,"instructor_register.html",{"form":form_instance})

    def post(self,request,*args,**kwargs):
        form_data = request.POST 
        form_instance = InstructorCreateForm(form_data)

        if form_instance.is_valid():
            form_instance.instance.role="instructor"
            form_instance.instance.is_superuser=True
            form_instance.instance.is_staff=True
            form_instance.save()
            return redirect("instructor-create")
        
        else:
            return render(request,"instructor_register.html",{"form":form_instance})


class ModuleLessonCreateView(View):

    def get(self,request,*args,**kwargs):

        module_form=ModuleForm()

        lesson_formset=LessonFormSet()

        context={
                    "module_form":module_form,
                    "lesson_formset":lesson_formset
                }

        return render(request,"module_add.html",context)

