from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from embed_video.fields import EmbedVideoField
from django.db.models import Max

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

    def __str__(self):
        return f"{self.course_object.title} - {self.title}"
    
    def save(self,*args,**kwargs):
        max_order=Module.objects.filter(course_object=self.course_object).aggregate(max=Max("order")).get("max") or 0
        self.order=max_order+1
        super().save(*args,**kwargs)

class Lesson(models.Model):

    title=models.CharField(max_length=200)

    module_object=models.ForeignKey(Module,on_delete=models.CASCADE,related_name="lessons")

    video=EmbedVideoField(null=True)

    order=models.PositiveIntegerField()

    def __str__(self):
        
        return f"{self.module_object.title} - {self.title}"

    def save(self,*args,**kwargs):
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








