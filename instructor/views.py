from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from instructor.forms import InstructorCreateForm, ModuleForm, LessonFormSet
from instructor.models import Course

class InstructorCreateView(View):
    def get(self, request):
        return render(request, 'instructor_register.html', {'form': InstructorCreateForm()})
    def post(self, request):
        form = InstructorCreateForm(request.POST)
        if form.is_valid():
            form.instance.role = 'instructor'
            # Staff access is granted only by an administrator, never public registration.
            form.save()
            messages.success(request, 'Instructor account created. You can now sign in.')
            return redirect('signin')
        return render(request, 'instructor_register.html', {'form': form})

class ModuleLessonCreateView(LoginRequiredMixin, View):
    login_url = 'signin'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.course = get_object_or_404(Course, pk=kwargs['pk'])
        if request.user.role != 'instructor' or self.course.owner_id != request.user.pk:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    def handle(self, request, data=None):
        form = ModuleForm(data)
        formset = LessonFormSet(data, instance=form.instance)
        if data is not None:
            valid = form.is_valid()
            valid_set = formset.is_valid()
            if valid and valid_set:
                with transaction.atomic():
                    module = form.save(commit=False)
                    module.course_object = self.course
                    module.save()
                    formset.instance = module
                    formset.save()
                messages.success(request, 'Module saved.')
                return redirect('course-detail', pk=self.course.pk)
        return render(request, 'module_add.html', {'course': self.course, 'module_form': form, 'lesson_formset': formset})
    def get(self, request, **kwargs):
        return self.handle(request)
    def post(self, request, **kwargs):
        return self.handle(request, request.POST)
