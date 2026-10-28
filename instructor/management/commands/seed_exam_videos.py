"""Curated public video references; videos remain hosted by their creators."""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from instructor.models import Course, Lesson
from .seed_exam_courses import COURSES


# course index, module index, credited lesson title, YouTube video ID
VIDEOS = [
    (0, 0, 'Logical reasoning worked examples - CareerRide (English)', 'iifXCRd3FyA'),
    (0, 0, 'Number series concepts and practice - Bharat Sir (Hindi)', 'qb49tIfu_Ew'),
    (1, 1, 'Percentages: concepts and worked examples - CareerRide (English)', 'RWdNhJWwzSs'),
    (1, 0, 'Quantitative aptitude demo class - Drishti IAS English', 'ENTJR9Rttxc'),
    (2, 2, 'Constitution of India, Part 1 - YesLearners (Malayalam)', 'vDxrA2Yb3MI'),
    (2, 2, 'Fundamental rights revision - Chakrapani Classes (Malayalam)', 'wthSXs9zb68'),
    (3, 1, 'Logical reasoning worked examples - CareerRide (English)', 'iifXCRd3FyA'),
    (3, 3, 'Malayalam grammar: Samasam - Arya G (Malayalam)', 'QGnEyAN4LmQ'),
    (4, 2, 'Indian polity introduction - StudyIQ, Shashank Tyagi (English)', 'rSZ69uc6qjw'),
    (4, 2, 'Fundamental rights: Articles 12-35 - StudyIQ (English)', '1PLoUVRQnGo'),
    (5, 2, 'CSAT quantitative aptitude demo class - Drishti IAS English', 'ENTJR9Rttxc'),
    (5, 1, 'Logical reasoning worked examples - CareerRide (English)', 'iifXCRd3FyA'),
]


class Command(BaseCommand):
    help = 'Add two credited public video lessons to each new exam course without replacing existing lessons.'

    @transaction.atomic
    def handle(self, *args, **options):
        call_command('seed_exam_courses', stdout=self.stdout)
        added = 0
        for course_index, module_index, title, video_id in VIDEOS:
            course = Course.objects.get(title=COURSES[course_index][0])
            module = course.modules.get(title=COURSES[course_index][5][module_index])
            url = f'https://www.youtube.com/watch?v={video_id}'
            if not module.lessons.filter(video=url).exists():
                Lesson.objects.create(module_object=module, title=title, video=url)
                added += 1
            if not course.thumbnail:
                course.thumbnail = url
                course.save(update_fields=['thumbnail', 'updated_at'])
        old = ('Curriculum preview: the module outline is available below. '
               'Lesson videos and practice materials have not been added yet. ')
        new = ('Introductory video collection: selected modules include public YouTube lessons '
               'credited to their original creators. Other modules are outlines awaiting content. '
               'Videos are freely available on YouTube; the listed price is a project demo price. '
               'Practice materials have not been added yet. ')
        for item in COURSES:
            course = Course.objects.get(title=item[0])
            if old in course.description:
                course.description = course.description.replace(old, new)
                course.save(update_fields=['description', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(f'Added {added} public video lessons.'))
