from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from CourseCloud.configuration import parse_debug
from instructor.models import Course, Module, Lesson

class CurriculumOrderingTests(TestCase):
    def test_editing_preserves_module_and_lesson_positions(self):
        course = Course.objects.create(title='Example', price=0, thumbnail='')
        first = Module.objects.create(course_object=course, title='First')
        second = Module.objects.create(course_object=course, title='Second')
        lesson = Lesson.objects.create(module_object=first, title='First lesson')
        Lesson.objects.create(module_object=first, title='Second lesson')
        first.title = 'Edited first'
        first.save()
        lesson.title = 'Edited lesson'
        lesson.save()
        self.assertEqual(first.order, 1)
        self.assertEqual(lesson.order, 1)
        self.assertEqual(list(course.modules.values_list('pk', flat=True)), [first.pk, second.pk])
        # Explicitly ordering a new module must also be respected.
        custom = Module.objects.create(course_object=course, title='Custom', order=10)
        self.assertEqual(custom.order, 10)


class DebugConfigurationTests(TestCase):
    def test_host_release_is_safe_and_boolean_values_are_supported(self):
        self.assertFalse(parse_debug('release'))
        self.assertTrue(parse_debug('True'))
        self.assertFalse(parse_debug('False'))
        with self.assertRaises(ImproperlyConfigured):
            parse_debug('not-a-setting')
