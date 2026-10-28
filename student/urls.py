# student>urls

from django.urls import path

from student import views
from student.assessments import CourseAssessmentsView, AssessmentView, MockTestsView
from student.course_notes import CourseNotesView

urlpatterns=[
    path('mock-tests/', MockTestsView.as_view(), name='mock-tests'),
    path('courses/<int:pk>/notes.pdf', CourseNotesView.as_view(), name='course-notes'),
    path('courses/<int:pk>/assessments/', CourseAssessmentsView.as_view(), name='course-assessments'),
    path('assessments/<int:pk>/', AssessmentView.as_view(), name='assessment'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('purchases/', views.PurchaseHistoryView.as_view(), name='purchase-history'),

    path("register/",views.StudentRegistrationView.as_view(),name="student-register"),
    path("signin/",views.SignInView.as_view(),name="signin"),
    path("index/",views.IndexView.as_view(),name="index"),
    path("courses/<int:pk>/",views.CourseDetailView.as_view(),name="course-detail"),

    path("courses/<int:pk>/add-to-cart/",views.AddToCartView.as_view(),name="add-to-cart"),

    path("cart/summary/",views.CartSummaryView.as_view(),name="cart-summary"),

    path("carts/<int:pk>/remove/",views.CartItemDeleteView.as_view(),name="cart-item-delete"),

    path("checkout/",views.CheckOutView.as_view(),name="checkout"),

    path("mycourses/",views.MyCoursesView.as_view(),name="mycourses"),

    path("courses/<int:pk>/watch",views.LessonDetailView.as_view(),name="lesson-detail"),
    
    path('payment/webhook/', views.PaymentWebhookView.as_view(), name='payment_webhook'),
    path('payment/verify',views.PaymentVerificationView.as_view(),name="payment_verify"),
    
    path('contact/',views.ContactView.as_view(),name="contact"),
    
    path('signout/',views.SignOutView.as_view(),name="signout"),



    
]
