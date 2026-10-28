from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from instructor.models import User, Course, Module, Lesson, Order, Assessment, Question, AssessmentAttempt


class AssessmentWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='quizstudent')
        self.course = Course.objects.create(title='Reasoning', description='Practice', price=100, thumbnail='')
        self.module = Module.objects.create(course_object=self.course, title='Series')
        self.lesson = Lesson.objects.create(module_object=self.module, title='Introduction')
        self.quiz = Assessment.objects.create(module=self.module, after_lesson=self.lesson, title='Checkpoint', published=True)
        self.question = Question.objects.create(assessment=self.quiz, prompt='What comes after 2, 4, 6?', option_a='8', option_b='9', option_c='10', option_d='12', correct_answer='a', explanation='Add two.')
        self.url = reverse('assessment', args=[self.quiz.pk])
        self.client.force_login(self.user)

    def enrol(self):
        order = Order.objects.create(student=self.user, is_paid=True)
        order.course_objects.add(self.course)

    def test_enrolment_required_for_start_and_view(self):
        self.assertRedirects(self.client.post(self.url), reverse('course-detail', args=[self.course.pk]))
        self.assertEqual(AssessmentAttempt.objects.count(), 0)
        self.assertRedirects(self.client.get(self.url), reverse('course-detail', args=[self.course.pk]))
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_scoring_snapshot_and_duplicate_submission(self):
        self.enrol()
        self.client.post(self.url)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Add two.')
        self.question.correct_answer = 'b'
        self.question.save()
        self.client.post(self.url, {f'question_{self.question.pk}': 'a', 'score': '999'})
        attempt = AssessmentAttempt.objects.get()
        self.assertEqual((attempt.score, attempt.total), (1, 1))
        self.assertContains(self.client.get(self.url), 'Add two.')
        self.client.post(self.url, {f'question_{self.question.pk}': 'b'})
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 1)
        self.assertEqual(AssessmentAttempt.objects.count(), 1)

    def test_deadline_cannot_be_reset_or_bypassed(self):
        self.enrol()
        self.client.post(self.url)
        attempt = AssessmentAttempt.objects.get()
        AssessmentAttempt.objects.filter(pk=attempt.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.client.post(self.url, {f'question_{self.question.pk}': 'a'})
        attempt.refresh_from_db()
        self.assertTrue(attempt.expired)
        self.assertEqual(attempt.score, 0)

    def test_refresh_keeps_deadline_and_disables_page_caching(self):
        self.enrol()
        self.client.post(self.url)
        deadline = AssessmentAttempt.objects.get().expires_at
        for _ in range(2):
            response = self.client.get(self.url)
            self.assertContains(response, 'data-test-deadline=')
            self.assertContains(response, 'data-server-now=')
            self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertEqual(AssessmentAttempt.objects.get().expires_at, deadline)

    def test_shared_live_window_and_delayed_review(self):
        self.enrol()
        now = timezone.now()
        self.quiz.kind = 'live'
        self.quiz.opens_at = now + timedelta(hours=1)
        self.quiz.closes_at = now + timedelta(hours=2)
        self.quiz.save()
        self.client.post(self.url)
        self.assertFalse(AssessmentAttempt.objects.exists())
        self.quiz.opens_at = now - timedelta(minutes=1)
        self.quiz.closes_at = now + timedelta(minutes=3)
        self.quiz.save()
        self.client.post(self.url)
        self.assertEqual(AssessmentAttempt.objects.get().expires_at, self.quiz.closes_at)
        self.client.post(self.url, {f'question_{self.question.pk}': 'a'})
        self.assertNotContains(self.client.get(self.url), 'Add two.')
        self.quiz.closes_at = now - timedelta(seconds=1)
        self.quiz.save()
        self.assertContains(self.client.get(self.url), 'Add two.')

    def test_csrf_and_attempt_privacy(self):
        self.enrol()
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.user)
        self.assertEqual(protected.post(self.url).status_code, 403)
        self.client.post(self.url)
        other = User.objects.create_user(username='other')
        order = Order.objects.create(student=other, is_paid=True)
        order.course_objects.add(self.course)
        self.client.force_login(other)
        self.assertRedirects(self.client.get(self.url), reverse('course-assessments', args=[self.course.pk]))

    def test_list_and_lesson_assessment_links(self):
        self.enrol()
        self.assertContains(self.client.get(reverse('course-assessments', args=[self.course.pk])), 'Checkpoint')
        self.assertContains(self.client.get(reverse('lesson-detail', args=[self.course.pk])), 'Checkpoint')

    def test_invalid_lesson_selections_return_404(self):
        self.enrol()
        url = reverse('lesson-detail', args=[self.course.pk])
        for selection in [{'module': 'invalid'}, {'lesson': 'not-a-number'}, {'module': '-1'}]:
            self.assertEqual(self.client.get(url, selection).status_code, 404)

    def test_test_only_module_shows_schedule_instead_of_missing_video(self):
        self.enrol()
        module = Module.objects.create(course_object=self.course, title='Scheduled Exam Tests')
        Assessment.objects.create(module=module, title='Scheduled test', kind='live', published=True)
        response = self.client.get(reverse('lesson-detail', args=[self.course.pk]), {'module': module.pk})
        self.assertContains(response, 'Scheduled Exam Tests')
        self.assertNotContains(response, 'The instructor has not added a video here yet.')

    def test_exam_modules_move_existing_tests_without_duplicates(self):
        self.course.title = 'Kerala PSC General Studies'
        self.course.save()
        live = Assessment.objects.create(module=self.module, after_lesson=self.lesson, title='Foundation live test', kind='live')
        call_command('seed_assessments', stdout=StringIO())
        live.refresh_from_db()
        self.assertEqual(live.module.title, 'Scheduled Exam Tests')
        self.assertIsNone(live.after_lesson)
        self.assertEqual(live.module.course_object, self.course)
        call_command('seed_assessments', stdout=StringIO())
        self.assertEqual(self.course.modules.filter(title='Scheduled Exam Tests').count(), 1)
        self.assertEqual(Assessment.objects.filter(module__course_object=self.course, kind='live').count(), 1)
        response = self.client.get(reverse('course-detail', args=[self.course.pk]))
        self.assertContains(response, 'Scheduled Exam Tests')
