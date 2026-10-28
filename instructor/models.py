from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from embed_video.fields import EmbedVideoField
from django.db.models import Max
from django.core.exceptions import ValidationError

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES =(
        ("instructor","Instructor"),
        ("student","Student")
    )

    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="student")

class InstructorProfile(models.Model):
    owner=models.OneToOneField(User,on_delete=models.CASCADE,related_name="instructor_profile")
    expertise=models.CharField(max_length=100,null=True)
    picture= models.ImageField(upload_to="profilepics",null=True,blank=True,default="profilepics/default.png")
    description=models.CharField(max_length=100,null=True)

    def __str__(self):
        return self.owner.username

def create_instructor_profile(sender,instance,created,**kwargs):

    if created and instance.role=="instructor":
        InstructorProfile.objects.create(owner=instance)

post_save.connect(create_instructor_profile,User)

class Category(models.Model):
    name=models.CharField(max_length=200,unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):

    title=models.CharField(max_length=200)

    description=models.TextField()

    price=models.DecimalField(decimal_places=2,max_digits=7)

    owner=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="courses",null=True)

    is_free=models.BooleanField(default=False)

    picture=models.ImageField(upload_to="courseimages",null=True,blank=True,default="courseimages/default.png")

    thumbnail=EmbedVideoField()

    category_objects=models.ManyToManyField(Category)
    
    created_at=models.DateTimeField(auto_now_add=True)

    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Module(models.Model):

    title=models.CharField(max_length=200)
    course_object=models.ForeignKey(Course,on_delete=models.CASCADE,related_name="modules")
    order=models.PositiveIntegerField()

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return f"{self.course_object.title} - {self.title}"
    
    def save(self,*args,**kwargs):
        if self._state.adding and self.order is None:
            max_order=Module.objects.filter(course_object=self.course_object).aggregate(max=Max("order")).get("max") or 0
            self.order=max_order+1
        super().save(*args,**kwargs)

class Lesson(models.Model):

    title=models.CharField(max_length=200)

    module_object=models.ForeignKey(Module,on_delete=models.CASCADE,related_name="lessons")

    video=EmbedVideoField(null=True)

    order=models.PositiveIntegerField()

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        
        return f"{self.module_object.title} - {self.title}"

    def save(self,*args,**kwargs):
        if self._state.adding and self.order is None:
            max_order=Lesson.objects.filter(module_object=self.module_object).aggregate(max=Max("order")).get("max") or 0
            self.order=max_order+1
        super().save(*args,**kwargs)

#Child

#cart_items=Cart.objects.filter(user=request.user)
# basket_items=request.user.basket.all()

class Cart(models.Model):

    course_object=models.ForeignKey(Course,on_delete=models.CASCADE)

    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="basket")

    created_date=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course_object.title





class Order(models.Model):

    course_objects=models.ManyToManyField(Course,related_name="enrolment")

    student=models.ForeignKey(User,on_delete=models.CASCADE,related_name="purchase")

    is_paid=models.BooleanField(default=False)

    rzp_order_id=models.CharField(max_length=100,null=True)

    created_date=models.DateTimeField(auto_now_add=True)

    total=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    
    


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.name


class Assessment(models.Model):
    KIND_CHOICES = [('quiz', 'Practice quiz'), ('live', 'Live test')]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assessments')
    after_lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='quiz')
    duration_minutes = models.PositiveIntegerField(default=15)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    published = models.BooleanField(default=False)
    weekly_sunday = models.BooleanField(default=False, help_text='Create a fresh weekly mock every Sunday at 12 PM IST.')
    series_root = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='weekly_occurrences')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['series_root', 'opens_at'], name='unique_weekly_mock_occurrence')]

    def clean(self):
        if self.duration_minutes < 1:
            raise ValidationError('Duration must be at least one minute.')
        if self.kind == 'live' and self.published and (not self.opens_at or not self.closes_at):
            raise ValidationError('Published live tests need a shared opening and closing time.')
        if self.opens_at and self.closes_at and self.closes_at <= self.opens_at:
            raise ValidationError('Closing time must be after opening time.')
        if self.after_lesson_id and self.after_lesson.module_object_id != self.module_id:
            raise ValidationError('Choose a lesson from this assessment module.')
        if self.weekly_sunday and self.kind != 'live':
            raise ValidationError('Weekly mocks must be live tests.')

    def __str__(self):
        return self.title


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[(v, v.upper()) for v in 'abcd'])
    explanation = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'pk']

    @property
    def choices(self):
        return [(key, getattr(self, 'option_' + key)) for key in 'abcd']

    def __str__(self):
        return self.prompt[:80]


class AssessmentAttempt(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(default=dict)
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    expired = models.BooleanField(default=False)
    # Freeze question content when starting: later admin edits cannot change grading.
    question_snapshot = models.JSONField(default=list)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['assessment', 'student'], name='one_assessment_attempt_per_student')]














# class Movie(models.Model):


#     title=models.CharField(max_length=200)

#     year=models.CharField(max_length=10)

#     director=models.CharField(max_length=200)

#     def __str__(self):
#         return self.title

# class Songs(models.Model):

#     title=models.CharField(max_length=200)

#     singers=models.CharField(max_length=200)

#     movie_object=models.ForeignKey(Movie,on_delete=models.CASCADE,related_name="musics")

#     def __str__(self):
#         return self.title


# # # orm query for creating a movie object

# # kgf_movie_instance=Movie.objects.create(title="KGF",year="2017",director="prasanth")

# # arm_movie_instance=Movie.objects.create(title="ARM",year="2024",director="jithin")

# # # orm query for adding song instance

# # kgf_movie_song_instance1=Songs.objects.create(title="kgf title song1",signers="singer1,singer2",movie_object=kgf_movie_instance)

# # kgf_movie_song_instance2=Songs.objects.create(title="kgf intro  song1",signers="singer1,singer2",movie_object=kgf_movie_instance)





# class Order(models.Model):

    # course_objects(M:M(Course))
    #student:FK(User)
    #is_paid(False)
    # rzp_order_id(charf(null))
    # created_date
    # total








