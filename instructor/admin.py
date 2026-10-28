from django.contrib import admin
from django.contrib.admin import sites
from instructor.models import User, Category, Course, Module, Lesson,InstructorProfile,Order

admin.site.register(Order)




# Register User and Category
admin.site.register(User)
admin.site.register(Category)

# Course Admin with Owner Auto-Assignment
class CourseAdmin(admin.ModelAdmin):
    exclude = ("owner",)
    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Course, CourseAdmin)

# Inline Lesson within Module
class LessonInline(admin.TabularInline):  # Change to StackedInline for block layout
    exclude=("order",)
    model = Lesson
    extra = 1  # Show one empty lesson form by default
    ordering = ["order"]  # Sort lessons by their order field

# Module Admin with Inline Lessons
class ModuleAdmin(admin.ModelAdmin):
    exclude=("order",)
    inlines = [LessonInline]

admin.site.register(Module, ModuleAdmin)


admin.site.register(InstructorProfile)

from instructor.models import Assessment, Question, AssessmentAttempt


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'kind', 'weekly_sunday', 'opens_at', 'closes_at', 'published')
    list_filter = ('kind', 'weekly_sunday', 'published')
    inlines = [QuestionInline]


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'score', 'total', 'started_at', 'submitted_at', 'expired')
    readonly_fields = ('assessment', 'student', 'score', 'total', 'started_at', 'submitted_at', 'expired', 'answers', 'question_snapshot')

    def has_add_permission(self, request):
        return False


