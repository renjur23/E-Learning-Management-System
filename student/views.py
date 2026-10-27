from decimal import Decimal
import logging
import json
import hashlib
import hmac
import razorpay
from requests.exceptions import RequestException
from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, FormView, CreateView
from instructor.models import Course, Cart, Order, Module, Lesson
from student.forms import StudentCreateForm, LoginForm, ContactForm
from student.decorator import signin_required

logger = logging.getLogger(__name__)
RZP_KEY_ID = config('RZP_KEY_ID', default='').strip()
RZP_KEY_SECRET = config('RZP_KEY_SECRET', default='').strip()
RZP_WEBHOOK_SECRET = config('RZP_WEBHOOK_SECRET', default='')
PAYMENT_DEMO = config('PAYMENT_DEMO', default=False, cast=bool)

def confirm_payment(order, payment):
    # Called inside a transaction with the local order locked.
    if (payment.get('order_id') != order.rzp_order_id
            or payment.get('amount') != int(order.total * 100)
            or payment.get('currency') != 'INR'
            or payment.get('status') != 'captured'):
        return False
    if not order.is_paid:
        order.is_paid = True
        order.save(update_fields=['is_paid'])
        Cart.objects.filter(user=order.student, course_object__in=order.course_objects.all()).delete()
    return True


class StudentRegistrationView(CreateView):
    template_name = 'student_register.html'
    form_class = StudentCreateForm
    success_url = reverse_lazy('signin')
    def form_valid(self, form):
        messages.success(self.request, 'Account created. You can now sign in.')
        return super().form_valid(form)

class SignInView(FormView):
    template_name = 'signin.html'
    form_class = LoginForm
    def form_valid(self, form):
        user = authenticate(self.request, **form.cleaned_data)
        if user is None:
            form.add_error(None, 'The username or password is incorrect. Please try again.')
            return self.form_invalid(form)
        login(self.request, user)
        return redirect('index')

@method_decorator(signin_required, name='dispatch')
class IndexView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        courses = Course.objects.select_related('owner').prefetch_related('category_objects').order_by('-created_at')
        if query:
            courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
        purchased = request.user.purchase.filter(is_paid=True).values_list('course_objects', flat=True)
        return render(request, 'home.html', {'courses': courses, 'purchased_courses': purchased, 'query': query})

@method_decorator(signin_required, name='dispatch')
class CourseDetailView(View):
    def get(self, request, pk):
        course = get_object_or_404(Course.objects.select_related('owner').prefetch_related('category_objects', 'modules__lessons'), pk=pk)
        modules = list(course.modules.all())
        return render(request, 'course_retrieve.html', {'course': course,
            'learning_topics': modules,
            'lesson_count': sum(len(module.lessons.all()) for module in modules),
            'enrolled': request.user.purchase.filter(is_paid=True, course_objects=course).exists(),
            'in_cart': request.user.basket.filter(course_object=course).exists()})

@method_decorator(signin_required, name='dispatch')
class AddToCartView(View):
    def get(self, request, pk):
        return redirect('course-detail', pk=pk)
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if request.user.purchase.filter(is_paid=True, course_objects=course).exists():
            return redirect('lesson-detail', pk=pk)
        _, created = Cart.objects.get_or_create(user=request.user, course_object=course)
        messages.success(request, 'Course added to your cart.' if created else 'This course is already in your cart.')
        return redirect('cart-summary')

@method_decorator(signin_required, name='dispatch')
class CartSummaryView(View):
    def get(self, request):
        carts = request.user.basket.select_related('course_object__owner').prefetch_related('course_object__modules__lessons')
        total = carts.aggregate(total=Sum('course_object__price'))['total'] or Decimal('0')
        return render(request, 'cart-summary.html', {'carts': carts, 'basket_total': total})

@method_decorator(signin_required, name='dispatch')
class CartItemDeleteView(View):
    def get(self, request, pk):
        return redirect('cart-summary')
    def post(self, request, pk):
        get_object_or_404(Cart, pk=pk, user=request.user).delete()
        messages.success(request, 'Course removed from your cart.')
        return redirect('cart-summary')

@method_decorator(signin_required, name='dispatch')
class CheckOutView(View):
    def get(self, request):
        carts = list(request.user.basket.select_related('course_object__owner'))
        if not carts:
            messages.info(request, 'Add a course before checking out.')
            return redirect('cart-summary')
        courses = list({c.course_object_id: c.course_object for c in carts}.values())
        total = sum((c.price for c in courses), Decimal('0'))
        return render(request, 'checkout.html', {'courses': courses, 'total': total})
    def post(self, request):
        carts = list(request.user.basket.select_related('course_object'))
        if not carts:
            messages.info(request, 'Add a course before checking out.')
            return redirect('cart-summary')
        courses = list({c.course_object_id: c.course_object for c in carts}.values())
        if any(c.price < 0 for c in courses):
            messages.error(request, 'A course has an invalid price. Please contact support.')
            return redirect('cart-summary')
        total = sum((c.price for c in courses), Decimal('0'))
        if PAYMENT_DEMO and settings.DEBUG and total > 0:
            if request.POST.get('demo_confirm') == 'yes':
                with transaction.atomic():
                    order = Order.objects.create(student=request.user, total=total, is_paid=True)
                    order.course_objects.set(courses)
                    request.user.basket.filter(pk__in=[c.pk for c in carts]).delete()
                messages.success(request, 'Demo payment completed. No money was charged. Your courses are ready.')
                return redirect('mycourses')
            return render(request, 'checkout.html', {'courses': courses, 'total': total, 'demo_payment': True})
        payment = None
        if total > 0:
            if not RZP_KEY_ID or not RZP_KEY_SECRET:
                messages.error(request, 'Payments are temporarily unavailable. Your cart has been saved.')
                return redirect('cart-summary')
            try:
                payment = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET)).order.create(
                    data={'amount': int(total * 100), 'currency': 'INR'})
            except razorpay.errors.BadRequestError as error:
                logger.warning('Razorpay rejected order creation')
                if 'authentication' in str(error).lower():
                    message = ('Razorpay authentication failed. Set a matching RZP_KEY_ID and '
                               'RZP_KEY_SECRET from the Razorpay dashboard in .env, then restart the server.'
                               if settings.DEBUG else 'Payments are temporarily unavailable. Please contact support.')
                else:
                    message = 'Razorpay could not accept this order. Please contact support.'
                messages.error(request, message + ' Your cart has been saved.')
                return redirect('cart-summary')
            except Exception:
                logger.exception('Unable to create payment order')
                messages.error(request, 'Payment could not be started. Your cart has been saved. Please try again.')
                return redirect('cart-summary')
        with transaction.atomic():
            order = Order.objects.create(student=request.user, total=total, is_paid=total == 0,
                                         rzp_order_id=payment['id'] if payment else None)
            order.course_objects.set(courses)
            if total == 0:
                request.user.basket.filter(pk__in=[c.pk for c in carts]).delete()
        if payment:
            options = {'key': RZP_KEY_ID, 'amount': int(total * 100), 'currency': 'INR',
                'name': 'CourseCloud', 'description': 'Course enrolment', 'order_id': payment['id'],
                'callback_url': request.build_absolute_uri(reverse('payment_verify')),
                'prefill': {'name': request.user.get_full_name(), 'email': request.user.email},
                'theme': {'color': '#24634e'}}
            return render(request, 'payment.html', {'payment_options': options, 'total': total, 'courses': courses})
        messages.success(request, 'You are enrolled. Your course is ready to open.')
        return redirect('mycourses')

@method_decorator(signin_required, name='dispatch')
class MyCoursesView(View):
    def get(self, request):
        courses = Course.objects.filter(enrolment__student=request.user, enrolment__is_paid=True).distinct().select_related('owner').prefetch_related('category_objects')
        return render(request, 'mycourses.html', {'courses': courses})

@method_decorator(signin_required, name='dispatch')
class LessonDetailView(View):
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if not request.user.purchase.filter(is_paid=True, course_objects=course).exists():
            messages.info(request, 'Enrol in this course to access its lessons.')
            return redirect('course-detail', pk=pk)
        modules = course.modules.order_by('order', 'pk')
        module = get_object_or_404(modules, pk=request.GET['module']) if request.GET.get('module') else modules.first()
        lesson = None
        if module:
            lessons = module.lessons.order_by('order', 'pk')
            lesson = get_object_or_404(lessons, pk=request.GET['lesson']) if request.GET.get('lesson') else lessons.first()
        return render(request, 'lesson_detail.html', {'course': course, 'lesson': lesson})

@method_decorator(csrf_exempt, name='dispatch')
class PaymentVerificationView(View):
    def post(self, request):
        if not RZP_KEY_ID or not RZP_KEY_SECRET:
            return HttpResponse('Payments are unavailable.', status=503)
        try:
            data = {k: request.POST[k] for k in ('razorpay_payment_id', 'razorpay_order_id', 'razorpay_signature')}
            order = get_object_or_404(Order, rzp_order_id=data['razorpay_order_id'])
            client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))
            # Use the order identifier stored by our server for signature verification.
            data['razorpay_order_id'] = order.rzp_order_id
            client.utility.verify_payment_signature(data)
            payment = client.payment.fetch(data['razorpay_payment_id'])
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=order.pk)
                confirmed = confirm_payment(order, payment)
            if confirmed:
                messages.success(request, 'Payment confirmed. Sign in to view your courses.' if not request.user.is_authenticated else 'Payment confirmed. Your courses are ready.')
                return redirect('mycourses')
            messages.info(request, 'Payment is awaiting confirmation. Your courses will appear in My learning after confirmation.')
            return redirect('mycourses')
        except (KeyError, razorpay.errors.SignatureVerificationError):
            messages.error(request, 'Payment could not be verified. Please contact support if you were charged.')
            return redirect('cart-summary')
        except (razorpay.errors.BadRequestError, razorpay.errors.GatewayError,
                razorpay.errors.ServerError, RequestException, OSError):
            logger.exception('Unable to fetch payment status')
            messages.error(request, 'Payment confirmation is temporarily unavailable. Please check My learning shortly.')
            return redirect('mycourses')


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    def post(self, request):
        if not RZP_WEBHOOK_SECRET:
            return HttpResponse(status=503)
        signature = request.headers.get('X-Razorpay-Signature', '')
        expected = hmac.new(RZP_WEBHOOK_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return HttpResponse(status=400)
        try:
            event = json.loads(request.body)
            if event.get('event') not in ('payment.captured', 'order.paid'):
                return HttpResponse(status=200)
            payment = event['payload']['payment']['entity']
            with transaction.atomic():
                order = Order.objects.select_for_update().filter(rzp_order_id=payment['order_id']).first()
                if order is None:
                    # Retry if the webhook raced with checkout saving the order.
                    return HttpResponse(status=503)
                if not confirm_payment(order, payment):
                    return HttpResponse(status=400)
        except (ValueError, KeyError, TypeError, AttributeError):
            return HttpResponse(status=400)
        return HttpResponse(status=200)

class SignOutView(View):
    def get(self, request):
        logout(request)
        return redirect('signin')

@method_decorator(signin_required, name='dispatch')
class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')
    def form_valid(self, form):
        from instructor.models import Contact
        Contact.objects.create(**form.cleaned_data)
        messages.success(self.request, 'Your message has been sent successfully.')
        return super().form_valid(form)


@method_decorator(signin_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        from student.forms import ProfileForm
        return render(request, 'profile.html', {'form': ProfileForm(instance=request.user)})

    def post(self, request):
        from student.forms import ProfileForm
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        return render(request, 'profile.html', {'form': form})


@method_decorator(signin_required, name='dispatch')
class PurchaseHistoryView(View):
    def get(self, request):
        orders = request.user.purchase.filter(is_paid=True).prefetch_related('course_objects').order_by('-created_date', '-pk')
        return render(request, 'purchase_history.html', {'orders': orders})
