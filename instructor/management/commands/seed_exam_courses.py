"""Add editable exam-preparation curriculum previews without replacing existing data."""
from html import escape

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from instructor.models import Category, Course, Module


COURSES = [
    ('General Reasoning: Logical Thinking & Problem Solving', 'General Reasoning', 'REASONING', '#276c8b',
     'Develop a structured approach to verbal and non-verbal reasoning with patterns, logical deductions and analytical problems.',
     ['Number and letter series', 'Analogies, classification and coding-decoding', 'Directions, blood relations and ranking', 'Syllogisms, arrangements and puzzles']),
    ('Quantitative Aptitude: Everyday Maths to Exam Practice', 'Quantitative Aptitude', 'APTITUDE', '#2356b2',
     'Build confidence with numerical problems, mental calculations and practical methods for competitive-exam aptitude practice.',
     ['Number systems, fractions and simplification', 'Percentages, ratios and averages', 'Profit and loss, interest and mixtures', 'Time and work, speed and data interpretation']),
    ('Kerala PSC: General Studies Foundation', 'Kerala PSC', 'KERALA PSC', '#14685f',
     'Begin a structured study routine covering Kerala-focused general knowledge and foundational Indian general studies for Kerala PSC preparation.',
     ['Kerala history, renaissance and culture', 'Kerala and Indian geography', 'Indian Constitution, governance and civic institutions', 'Basic science, economy and current-affairs study methods']),
    ('Kerala PSC: Maths, Reasoning & Language Practice', 'Kerala PSC', 'PSC PRACTICE', '#386f91',
     'Organise your Kerala PSC practice around arithmetic, reasoning, English and Malayalam language fundamentals.',
     ['Arithmetic and numerical ability', 'Mental ability and logical reasoning', 'English grammar and vocabulary', 'Malayalam grammar and reading comprehension']),
    ('UPSC Civil Services: General Studies Foundation', 'UPSC Preparation', 'UPSC / GS', '#3458a0',
     'Create a foundation for civil-services study through history, geography, polity, economy and environment, with an introduction to analytical writing.',
     ['Indian history, heritage and society', 'Physical and Indian geography, environment and ecology', 'Constitution, governance and economic fundamentals', 'Current-affairs analysis, ethics and answer-writing habits']),
    ('UPSC CSAT: Reasoning, Numeracy & Comprehension', 'UPSC Preparation', 'UPSC / CSAT', '#405b8c',
     'Practise the core skills used in aptitude papers: reading carefully, reasoning logically and interpreting numerical information.',
     ['Reading comprehension and inference', 'Logical reasoning and analytical ability', 'Basic numeracy and quantitative problem solving', 'Data interpretation and time-management practice']),
]

# Starter prices in INR, in the same order as the catalogue above.
COURSE_PRICES = [499, 699, 1499, 999, 1999, 999]


class Command(BaseCommand):
    help = 'Add six exam-preparation curriculum previews; existing courses are left intact.'

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for index, (title, category, label, color, overview, modules) in enumerate(COURSES, 1):
            if Course.objects.filter(title=title).exists():
                self.stdout.write(f'Already exists: {title}')
                continue
            course = Course.objects.create(
                title=title, price=COURSE_PRICES[index - 1], is_free=False, owner=None, picture='', thumbnail='',
                description=(overview + '\n\nCurriculum preview: the module outline is available below. '
                             'Lesson videos and practice materials have not been added yet. '
                             'This is an independent study resource, not an official commission course. '
                             'Check the relevant official exam notification for the applicable syllabus and requirements.'),
            )
            course.category_objects.add(Category.objects.get_or_create(name=category)[0])
            for topic in modules:
                Module.objects.create(course_object=course, title=topic)
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
<rect width="960" height="540" fill="{color}"/><circle cx="810" cy="110" r="225" fill="none" stroke="#ffffff" stroke-opacity=".18" stroke-width="2"/>
<circle cx="810" cy="110" r="160" fill="none" stroke="#ffffff" stroke-opacity=".18" stroke-width="2"/>
<path d="M680 340h150v100H680z M755 340v100" fill="none" stroke="#c7e8ff" stroke-width="5"/>
<text x="60" y="75" fill="#ffffff" font-family="sans-serif" font-size="20" letter-spacing="4">LEARNORBIT / STUDY STUDIO</text>
<text x="60" y="270" fill="#f0f8ff" font-family="sans-serif" font-size="56" font-weight="bold">{escape(label)}</text>
<text x="60" y="325" fill="#ffffff" font-family="sans-serif" font-size="25">FOUNDATIONS &amp; PRACTICE</text>
<text x="60" y="475" fill="#ffffff" font-family="sans-serif" font-size="20">CURRICULUM PREVIEW / {index:02d}</text></svg>'''
            course.picture.save(f'exam-study-{index}.svg', ContentFile(svg.encode('utf-8')), save=True)
            created_count += 1
            self.stdout.write(f'Added: {title}')
        self.stdout.write(self.style.SUCCESS(f'Added {created_count} courses.'))
