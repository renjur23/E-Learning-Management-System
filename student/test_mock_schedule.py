from datetime import datetime, timedelta
from django.test import TestCase
from django.urls import reverse
from instructor.models import Assessment, Module, Course, Question, AssessmentAttempt, User
from student.mock_schedule import sunday_window, ensure_weekly_mocks, IST


class SundayMockTests(TestCase):
    def setUp(self):
        self.start = datetime(2026,11,1,12,tzinfo=IST)
        self.course = Course.objects.create(title='Kerala PSC', price=100, thumbnail='')
        module = Module.objects.create(course_object=self.course, title='Scheduled Exam Tests')
        self.root = Assessment.objects.create(module=module, title='Sunday Mock Test', kind='live', weekly_sunday=True, published=True, duration_minutes=30, opens_at=self.start, closes_at=self.start+timedelta(minutes=30))
        Question.objects.create(assessment=self.root, prompt='Example question', option_a='First', option_b='Second', option_c='Third', option_d='Fourth', correct_answer='b', explanation='Example explanation.')

    def test_sunday_window_before_during_and_after_session(self):
        for value in [self.start-timedelta(days=1), self.start-timedelta(seconds=1), self.start, self.start+timedelta(minutes=29)]:
            self.assertEqual(sunday_window(value)[0], self.start)
        self.assertEqual(sunday_window(self.start+timedelta(minutes=30))[0], self.start+timedelta(days=7))

    def test_new_week_has_separate_attempts_and_no_duplicate_sessions(self):
        student = User.objects.create_user(username='weekly-student')
        previous = AssessmentAttempt.objects.create(assessment=self.root, student=student, expires_at=self.root.closes_at, submitted_at=self.root.closes_at, score=1, total=1)
        now = self.start+timedelta(days=7)
        first = ensure_weekly_mocks(self.course, now)[0]
        second = ensure_weekly_mocks(self.course, now)[0]
        self.assertEqual(first.pk, second.pk)
        self.assertNotEqual(first.pk, self.root.pk)
        self.assertEqual(first.questions.get().prompt, 'Example question')
        self.assertFalse(first.attempts.exists())
        previous.refresh_from_db()
        self.assertEqual(previous.score, 1)
        self.root.refresh_from_db()
        self.assertEqual(self.root.opens_at, self.start)

    def test_mock_cards_and_login(self):
        self.assertEqual(self.client.get(reverse('mock-tests')).status_code, 302)
        user = User.objects.create_user(username='mock-browser')
        self.client.force_login(user)
        response = self.client.get(reverse('mock-tests'))
        self.assertContains(response, 'Weekly mock tests')
        self.assertContains(response, 'Kerala PSC')
        self.assertContains(response, 'View course')
        self.assertIn('no-store', response['Cache-Control'])
