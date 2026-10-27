from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from instructor.models import User, Course, Order, Cart, Module, Lesson, Contact

class LearningWorkflowTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='learner',password='Testpass123!')
        self.owner=User.objects.create_user(username='teacher',password='Testpass123!',role='instructor')
        self.course=Course.objects.create(title='Python basics', description='Learn Python', price=0, owner=self.owner, thumbnail='')
        self.client.force_login(self.user)
    def test_pages_and_search(self):
        for name in ['index','mycourses','cart-summary','contact']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertContains(self.client.get(reverse('course-detail',args=[self.course.pk])),'Python basics')
        self.assertContains(self.client.get(reverse('index'),{'q':'unmatched'}),'No courses found')
    def test_invalid_login_and_contact(self):
        self.client.logout()
        self.assertContains(self.client.post(reverse('signin'),{'username':'learner','password':'wrong'}),'incorrect')
        self.assertEqual(self.client.post(reverse('signin'),{}).status_code,200)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('contact'),{'name':'Test','email':'test@example.com','message':'Help please'}).status_code,302)
        self.assertEqual(Contact.objects.count(),1)
        self.assertContains(self.client.post(reverse('contact'),{'name':'Test','email':'invalid'}),'Enter a valid email')
    def test_cart_and_free_enrolment(self):
        url=reverse('add-to-cart',args=[self.course.pk])
        self.client.get(url)
        self.assertEqual(Cart.objects.count(),0)
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Cart.objects.count(),1)
        self.client.post(reverse('checkout'))
        self.assertTrue(Order.objects.get().is_paid)
        self.assertEqual(Cart.objects.count(),0)
        self.assertContains(self.client.get(reverse('mycourses')),'Python basics')
        self.assertContains(self.client.get(reverse('lesson-detail',args=[self.course.pk])),'Content is on its way')
    def test_access_and_cart_ownership(self):
        self.assertRedirects(self.client.get(reverse('lesson-detail',args=[self.course.pk])),reverse('course-detail',args=[self.course.pk]))
        cart=Cart.objects.create(user=self.owner,course_object=self.course)
        self.assertEqual(self.client.post(reverse('cart-item-delete',args=[cart.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('module-create',args=[self.course.pk])).status_code,403)
    def test_instructor_module_save(self):
        self.client.force_login(self.owner)
        url=reverse('module-create',args=[self.course.pk])
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.post(url,{'title':'Introduction','lessons-TOTAL_FORMS':'2','lessons-INITIAL_FORMS':'0','lessons-MIN_NUM_FORMS':'0','lessons-MAX_NUM_FORMS':'1000','lessons-0-title':'Welcome','lessons-0-video':'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}).status_code,302)
        self.assertEqual(Lesson.objects.count(),1)
    def test_public_instructor_does_not_grant_staff(self):
        self.client.logout()
        self.client.post(reverse('instructor-create'),{'username':'newteacher','password1':'SafeExample773!','password2':'SafeExample773!','email':'teacher@example.com'})
        teacher=User.objects.get(username='newteacher')
        self.assertEqual(teacher.role,'instructor')
        self.assertFalse(teacher.is_staff)
        self.assertFalse(teacher.is_superuser)
    @patch('student.views.razorpay.Client')
    def test_paid_checkout_keeps_cart_until_verified(self, client_class):
        self.course.price=100
        self.course.save()
        Cart.objects.create(user=self.user,course_object=self.course)
        client_class.return_value.order.create.return_value={'id':'order_test'}
        client_class.return_value.payment.fetch.return_value={'id':'payment_test','order_id':'order_test','amount':10000,'currency':'INR','status':'captured'}
        with patch('student.views.RZP_KEY_ID','key'), patch('student.views.RZP_KEY_SECRET','secret'):
            self.assertContains(self.client.post(reverse('checkout')),'Pay securely')
            self.assertEqual(Cart.objects.count(),1)
            self.assertFalse(Order.objects.get().is_paid)
            self.client.post(reverse('payment_verify'),{'razorpay_order_id':'order_test','razorpay_payment_id':'payment_test','razorpay_signature':'test'})
        self.assertTrue(Order.objects.get().is_paid)
        self.assertEqual(Cart.objects.count(),0)


class PaymentSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='Testpass123!')
        self.course = Course.objects.create(title='Paid course', price=100, owner=self.user)
        self.order = Order.objects.create(student=self.user, total=100, rzp_order_id='order_secure')
        self.order.course_objects.add(self.course)
        Cart.objects.create(user=self.user, course_object=self.course)
        self.payment = {'id': 'pay_secure', 'order_id': 'order_secure', 'amount': 10000,
                        'currency': 'INR', 'status': 'captured'}

    def webhook(self, payment=None, signature_valid=True):
        import json, hmac, hashlib
        body = json.dumps({'event': 'payment.captured', 'payload': {'payment': {'entity': payment or self.payment}}})
        signature = hmac.new(b'webhook-secret', body.encode(), hashlib.sha256).hexdigest()
        with patch('student.views.RZP_WEBHOOK_SECRET', 'webhook-secret'):
            return self.client.post(reverse('payment_webhook'), data=body, content_type='application/json',
                                    HTTP_X_RAZORPAY_SIGNATURE=signature if signature_valid else 'invalid')

    def test_webhook_retries_are_idempotent(self):
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(self.webhook().status_code, 200)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        self.assertFalse(Cart.objects.exists())
        self.assertEqual(Order.objects.count(), 1)

    def test_webhook_rejects_forgery_and_wrong_amount_or_status(self):
        self.assertEqual(self.webhook(signature_valid=False).status_code, 400)
        for values in ({'amount': 1}, {'currency': 'USD'}, {'status': 'authorized'}):
            self.assertEqual(self.webhook({**self.payment, **values}).status_code, 400)
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)
        self.assertTrue(Cart.objects.exists())

    @patch('student.views.razorpay.Client')
    def test_callback_does_not_enrol_an_uncaptured_payment(self, client_class):
        self.client.force_login(self.user)
        client_class.return_value.payment.fetch.return_value = {**self.payment, 'status': 'authorized'}
        with patch('student.views.RZP_KEY_ID', 'key'), patch('student.views.RZP_KEY_SECRET', 'secret'):
            self.client.post(reverse('payment_verify'), {'razorpay_order_id': 'order_secure',
                'razorpay_payment_id': 'pay_secure', 'razorpay_signature': 'signature'})
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)
        self.assertTrue(Cart.objects.exists())

    def test_callback_rejects_invalid_signature(self):
        with patch('student.views.RZP_KEY_ID', 'key'), patch('student.views.RZP_KEY_SECRET', 'secret'):
            self.client.post(reverse('payment_verify'), {'razorpay_order_id': 'order_secure',
                'razorpay_payment_id': 'pay_secure', 'razorpay_signature': 'invalid'})
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)

    @patch('student.views.razorpay.Client')
    def test_provider_outage_keeps_order_unpaid(self, client_class):
        from requests.exceptions import ConnectionError
        client_class.return_value.payment.fetch.side_effect = ConnectionError('Provider unavailable')
        with patch('student.views.RZP_KEY_ID', 'key'), patch('student.views.RZP_KEY_SECRET', 'secret'):
            with self.assertLogs('student.views', level='ERROR'):
                response = self.client.post(reverse('payment_verify'), {'razorpay_order_id': 'order_secure',
                    'razorpay_payment_id': 'pay_secure', 'razorpay_signature': 'signature'})
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)


class ProfileAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='renjith', password='Testpass123!', first_name='Renjith', last_name='Rajendran')
        self.client.force_login(self.user)

    def test_profile_save_and_menu(self):
        self.assertContains(self.client.get(reverse('profile')), 'RR')
        self.client.post(reverse('profile'), {'first_name': 'Ren', 'last_name': 'Raj', 'email': 'ren@example.com', 'is_staff': 'true'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'ren@example.com')
        self.assertFalse(self.user.is_staff)
        self.assertContains(self.client.get(reverse('profile')), 'Purchase history')

    def test_purchase_history_shows_only_own_paid_orders(self):
        other = User.objects.create_user(username='other')
        course = Course.objects.create(title='Your purchased course', price=50, owner=other)
        order = Order.objects.create(student=self.user, total=50, is_paid=True)
        order.course_objects.add(course)
        hidden = Course.objects.create(title='Private course', price=100, owner=other)
        for student, paid in ((other, True), (self.user, False)):
            order = Order.objects.create(student=student, total=100, is_paid=paid)
            order.course_objects.add(hidden)
        response = self.client.get(reverse('purchase-history'))
        self.assertContains(response, 'Your purchased course')
        self.assertNotContains(response, 'Private course')

    def test_account_pages_require_login(self):
        self.client.logout()
        for name in ('profile', 'purchase-history'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)


class CourseOverviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='overview', password='Testpass123!')
        self.course = Course.objects.create(title='Python course', description='Learn Python with projects.', price=100, owner=self.user)
        module = Module.objects.create(title='Build Python applications', course_object=self.course)
        Lesson.objects.create(title='Your first application', module_object=module)
        self.client.force_login(self.user)

    def test_reference_layout_uses_course_content(self):
        response = self.client.get(reverse('course-detail', args=[self.course.pk]))
        for text in ("What you'll learn", 'Build Python applications', '1 lesson', 'Enrol now', 'Last updated'):
            self.assertContains(response, text)
        self.assertNotContains(response, 'Certificate of completion')

    def test_enrolment_card_reflects_cart_and_access(self):
        Cart.objects.create(user=self.user, course_object=self.course)
        self.assertContains(self.client.get(reverse('course-detail', args=[self.course.pk])), 'Go to cart')
        order = Order.objects.create(student=self.user, total=100, is_paid=True)
        order.course_objects.add(self.course)
        self.assertContains(self.client.get(reverse('course-detail', args=[self.course.pk])), 'Continue learning')


class CheckoutPresentationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shopper', password='Testpass123!')
        self.course = Course.objects.create(title='Shopping course', price=125, owner=self.user)
        Cart.objects.create(user=self.user, course_object=self.course)
        self.client.force_login(self.user)

    def test_cart_and_review_show_real_total_without_creating_order(self):
        response = self.client.get(reverse('cart-summary'))
        self.assertContains(response, 'Shopping Cart')
        self.assertContains(response, 'Proceed to Checkout')
        self.assertContains(response, '125.00')
        response = self.client.get(reverse('checkout'))
        self.assertContains(response, 'Order summary')
        self.assertContains(response, 'Shopping course')
        self.assertContains(response, '125.00')
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Cart.objects.exists())

    def test_empty_checkout_returns_to_cart(self):
        Cart.objects.all().delete()
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('cart-summary'))


class DemoPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='demo-buyer', password='Testpass123!')
        self.course = Course.objects.create(title='Demo course', price=100, owner=self.user)
        Cart.objects.create(user=self.user, course_object=self.course)
        self.client.force_login(self.user)

    @patch('student.views.PAYMENT_DEMO', True)
    def test_demo_requires_confirmation_and_unlocks_courses(self):
        with self.settings(DEBUG=True):
            response = self.client.post(reverse('checkout'))
            self.assertContains(response, 'Complete demo payment')
            self.assertFalse(Order.objects.exists())
            self.client.post(reverse('checkout'), {'demo_confirm': 'yes'})
        self.assertTrue(Order.objects.get().is_paid)
        self.assertFalse(Cart.objects.exists())

    @patch('student.views.PAYMENT_DEMO', True)
    @patch('student.views.RZP_KEY_ID', '')
    def test_demo_disabled_in_production(self):
        with self.settings(DEBUG=False):
            self.client.post(reverse('checkout'), {'demo_confirm': 'yes'})
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Cart.objects.exists())


class RazorpayAuthenticationTests(TestCase):
    @patch('student.views.PAYMENT_DEMO', False)
    @patch('student.views.RZP_KEY_ID', 'rzp_test_invalid')
    @patch('student.views.RZP_KEY_SECRET', 'invalid')
    @patch('student.views.razorpay.Client')
    def test_authentication_failure_preserves_cart_and_explains_configuration(self, client_class):
        import razorpay
        user = User.objects.create_user(username='auth-buyer')
        course = Course.objects.create(title='Test course', price=100, owner=user)
        Cart.objects.create(user=user, course_object=course)
        self.client.force_login(user)
        client_class.return_value.order.create.side_effect = razorpay.errors.BadRequestError('Authentication failed')
        with self.settings(DEBUG=True), self.assertLogs('student.views', level='WARNING'):
            response = self.client.post(reverse('checkout'), follow=True)
        self.assertContains(response, 'Razorpay authentication failed')
        self.assertContains(response, 'restart the server')
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Cart.objects.exists())
