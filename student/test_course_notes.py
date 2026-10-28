from io import BytesIO
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfReader
from instructor.models import User, Course, Order, Module


class CourseNotesTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='notes-student')
        self.course = Course.objects.create(title='Quantitative Aptitude', description='Maths', price=699, thumbnail='')
        Module.objects.create(course_object=self.course, title='Percentages')
        self.url = reverse('course-notes', args=[self.course.pk])

    def test_notes_require_signin_and_paid_enrolment(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.student)
        self.assertRedirects(self.client.get(self.url), reverse('course-detail', args=[self.course.pk]))
        order = Order.objects.create(student=self.student, is_paid=False)
        order.course_objects.add(self.course)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_enrolled_student_downloads_valid_course_specific_pdf(self):
        order = Order.objects.create(student=self.student, is_paid=True)
        order.course_objects.add(self.course)
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('no-store', response['Cache-Control'])
        data = b''.join(response.streaming_content)
        self.assertTrue(data.startswith(b'%PDF-'))
        reader = PdfReader(BytesIO(data))
        self.assertEqual(len(reader.pages), 2)
        text = '\n'.join(page.extract_text() for page in reader.pages)
        self.assertIn('Quantitative Aptitude', text)
        self.assertIn('Rs. 782', text)
        self.assertIn('Percentages', text)

    def test_missing_course_is_not_found(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('course-notes', args=[99999])).status_code, 404)
