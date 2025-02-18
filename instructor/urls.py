from django.urls import path
from instructor import views

urlpatterns = [
    path('register/',views.InstructorCreateView.as_view(),name="instructor-create"),

    path("course/<int:pk>/module/add/",views.ModuleLessonCreateView.as_view(),name="module-create")
]