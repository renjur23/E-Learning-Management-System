"""Materialise the current or next Sunday occurrence on demand; no scheduler required."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils import timezone
from instructor.models import Assessment, Question

IST = ZoneInfo('Asia/Kolkata')


def sunday_window(now=None, duration=30):
    local = (now or timezone.now()).astimezone(IST)
    day = local.date() + timedelta(days=(6-local.weekday()) % 7)
    start = datetime.combine(day, time(12), tzinfo=IST)
    if local >= start + timedelta(minutes=duration):
        start += timedelta(days=7)
    return start, start + timedelta(minutes=duration)


@transaction.atomic
def ensure_weekly_mocks(course=None, now=None):
    roots = Assessment.objects.select_for_update().filter(weekly_sunday=True, published=True)
    if course:
        roots = roots.filter(module__course_object=course)
    occurrences = []
    for root in roots:
        start, end = sunday_window(now, root.duration_minutes)
        if root.opens_at and start < root.opens_at:
            start, end = root.opens_at, root.closes_at
        if root.opens_at == start:
            occurrences.append(root)
            continue
        occurrence, created = Assessment.objects.get_or_create(series_root=root, opens_at=start, defaults={
            'module': root.module, 'title': root.title, 'kind': 'live',
            'duration_minutes': root.duration_minutes, 'closes_at': end, 'published': True,
        })
        if created:
            Question.objects.bulk_create([Question(assessment=occurrence, prompt=q.prompt, option_a=q.option_a, option_b=q.option_b, option_c=q.option_c, option_d=q.option_d, correct_answer=q.correct_answer, explanation=q.explanation, order=q.order) for q in root.questions.all()])
        occurrences.append(occurrence)
    return occurrences
