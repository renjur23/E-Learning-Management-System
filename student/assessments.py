from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
import math

from instructor.models import Assessment, AssessmentAttempt, Course
from student.decorator import signin_required
from student.mock_schedule import ensure_weekly_mocks, sunday_window


def enrolled(user, course):
    return user.purchase.filter(is_paid=True, course_objects=course).exists()


@method_decorator(signin_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class MockTestsView(View):
    def get(self, request):
        mocks = ensure_weekly_mocks()
        purchased = set(request.user.purchase.filter(is_paid=True).values_list('course_objects', flat=True))
        rows = [{'assessment': mock, 'course': mock.module.course_object, 'enrolled': mock.module.course_object_id in purchased} for mock in mocks]
        start, end = sunday_window()
        return render(request, 'mock_tests.html', {'mock_rows': rows, 'next_start': start, 'next_end': end})


@method_decorator(signin_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class CourseAssessmentsView(View):
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if not enrolled(request.user, course):
            return redirect('course-detail', pk=pk)
        ensure_weekly_mocks(course)
        assessments = Assessment.objects.filter(module__course_object=course, published=True).select_related('module', 'after_lesson').order_by('module__order', 'pk')
        attempts = {a.assessment_id: a for a in request.user.assessment_attempts.filter(assessment__module__course_object=course)}
        now = timezone.now()
        rows = []
        for assessment in assessments:
            attempt = attempts.get(assessment.pk)
            upcoming = bool(assessment.opens_at and now < assessment.opens_at)
            closed = bool(assessment.closes_at and now >= assessment.closes_at)
            rows.append({'assessment': assessment, 'attempt': attempt, 'upcoming': upcoming, 'closed': closed})
        return render(request, 'assessments.html', {'course': course, 'rows': rows})


@method_decorator(signin_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AssessmentView(View):
    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment.objects.select_related('module__course_object'), pk=kwargs['pk'], published=True)
        self.course = self.assessment.module.course_object
        if not enrolled(request.user, self.course):
            return redirect('course-detail', pk=self.course.pk)
        return super().dispatch(request, *args, **kwargs)

    def deadline(self, attempt):
        return attempt.expires_at

    def expire(self, attempt):
        attempt.expired = True
        attempt.submitted_at = timezone.now()
        attempt.score = 0
        attempt.save(update_fields=['expired', 'submitted_at', 'score'])

    def get(self, request, pk):
        attempt = AssessmentAttempt.objects.filter(assessment=self.assessment, student=request.user).first()
        if attempt and not attempt.submitted_at and timezone.now() >= self.deadline(attempt):
            # Do not overwrite a simultaneous successful submission.
            with transaction.atomic():
                attempt = AssessmentAttempt.objects.select_for_update().get(pk=attempt.pk)
                if not attempt.submitted_at:
                    self.expire(attempt)
        if not attempt:
            return redirect('course-assessments', pk=self.course.pk)
        if attempt.submitted_at:
            review = []
            review_pending = self.assessment.kind == 'live' and self.assessment.closes_at and timezone.now() < self.assessment.closes_at
            for question in ([] if review_pending else attempt.question_snapshot):
                selected = attempt.answers.get(str(question['id']), '')
                review.append({'question': question, 'selected': selected, 'correct': selected == question['correct_answer']})
            return render(request, 'assessment_result.html', {'course': self.course, 'assessment': self.assessment, 'attempt': attempt, 'review': review, 'review_pending': review_pending})
        # Answers and explanations never reach the browser during a running test.
        questions = [{key: q[key] for key in ('id', 'prompt', 'choices')} for q in attempt.question_snapshot]
        now = timezone.now()
        remaining = max(0, math.ceil((self.deadline(attempt) - now).total_seconds()))
        return render(request, 'assessment_take.html', {
            'course': self.course, 'assessment': self.assessment, 'questions': questions,
            'remaining': remaining, 'countdown': f'{remaining // 60:02d}:{remaining % 60:02d}',
            'test_deadline': self.deadline(attempt).isoformat(), 'server_now': now.isoformat(),
        })

    @transaction.atomic
    def post(self, request, pk):
        now = timezone.now()
        attempt = AssessmentAttempt.objects.select_for_update().filter(assessment=self.assessment, student=request.user).first()
        if attempt and attempt.submitted_at:
            return redirect('assessment', pk=pk)
        if not attempt:
            assessment = self.assessment
            if ((assessment.kind == 'live' and (not assessment.opens_at or not assessment.closes_at))
                    or (assessment.opens_at and now < assessment.opens_at)
                    or (assessment.closes_at and now >= assessment.closes_at)):
                messages.info(request, 'This test is outside its scheduled window.')
                return redirect('course-assessments', pk=self.course.pk)
            snapshot = [{'id': q.pk, 'prompt': q.prompt, 'choices': q.choices, 'correct_answer': q.correct_answer, 'explanation': q.explanation} for q in assessment.questions.all()]
            if not snapshot:
                messages.info(request, 'Questions are not available yet.')
                return redirect('course-assessments', pk=self.course.pk)
            # The unique constraint also protects against concurrent start requests.
            end = now + timedelta(minutes=assessment.duration_minutes)
            if assessment.closes_at:
                end = min(end, assessment.closes_at)
            AssessmentAttempt.objects.get_or_create(assessment=assessment, student=request.user, defaults={'question_snapshot': snapshot, 'total': len(snapshot), 'expires_at': end})
            return redirect('assessment', pk=pk)
        if now >= self.deadline(attempt):
            self.expire(attempt)
        else:
            answers = {str(q['id']): request.POST.get('question_' + str(q['id']), '') for q in attempt.question_snapshot}
            answers = {key: value for key, value in answers.items() if value in 'abcd' and len(value) == 1}
            attempt.answers = answers
            attempt.score = sum(answers.get(str(q['id'])) == q['correct_answer'] for q in attempt.question_snapshot)
            attempt.submitted_at = now
            attempt.save(update_fields=['answers', 'score', 'submitted_at'])
        return redirect('assessment', pk=pk)
