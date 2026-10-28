from django.core.management.base import BaseCommand
from django.db import transaction
from instructor.models import Assessment, Course, Module, Question
from student.mock_schedule import sunday_window


class Command(BaseCommand):
    help = 'Add weekly Sunday mock-test series without modifying existing tests or attempts.'

    @transaction.atomic
    def handle(self, *args, **options):
        start, end = sunday_window()
        added = 0
        for course in Course.objects.all():
            source = Assessment.objects.filter(module__course_object=course, kind='live', weekly_sunday=False, series_root__isnull=True).first()
            if not source or not source.questions.exists():
                continue
            module, _ = Module.objects.get_or_create(course_object=course, title='Scheduled Exam Tests')
            mock, created = Assessment.objects.get_or_create(module=module, weekly_sunday=True, defaults={
                'title': 'Sunday Mock Test', 'kind': 'live', 'duration_minutes': 30,
                'opens_at': start, 'closes_at': end, 'published': True,
            })
            if created:
                for q in source.questions.all():
                    Question.objects.create(assessment=mock, prompt=q.prompt, option_a=q.option_a, option_b=q.option_b, option_c=q.option_c, option_d=q.option_d, correct_answer=q.correct_answer, explanation=q.explanation, order=q.order)
                added += 1
        self.stdout.write(self.style.SUCCESS(f'Added {added} weekly mock series. Every Sunday, 12:00-12:30 PM IST.'))
