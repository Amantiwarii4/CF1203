from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import CharField, Model
from django_mysql.models import ListCharField


class Banner(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100,blank=True)
    image = models.ImageField(null= True, blank=True,upload_to='images/')
    link = models.CharField(max_length=500,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Upcomingevents(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100,blank=True)
    about = models.TextField(_('about'), null=True, blank=True)
    image = models.ImageField(null= True, blank=True,upload_to='images/')
    link = models.CharField(max_length=500,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Services(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100,blank=True)
    image = models.ImageField(null= True, blank=True,upload_to='images/')
    link = models.CharField(max_length=500,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Category(models.Model):
    title = models.CharField(_('title'),
                             null=True,
                             max_length=150,
                             blank=True,
                             help_text=_('Required. 150 characters or fewer. digits only.'),
                             )
    about = models.TextField(_('about'), null=True, blank=True)
    category_image = models.ImageField(_('category_image'), null=True, blank=True, upload_to='category_image/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Course(models.Model):
    course_title = models.CharField(_('course_title'),
                                    null=True,
                                    max_length=250,
                                    blank=True,
                                    help_text=_('Required. 250 characters or fewer. digits only.'),
                                    )
    # category = models.ForeignKey(Category, related_name='category', null=False, on_delete=models.CASCADE,default=1)
    author = models.CharField(_('author'), null=True, max_length=150, blank=True, )
    about = models.TextField(_('about'), null=True, blank=True)
    # rating = models.IntegerField(_('rating'), null=True, blank=True)
    # total_hours = models.CharField(_('total_hours'), max_length=6, null=True, blank=True)
    # total_days = models.IntegerField(_('total_days'), null=True, blank=True)
    selling_price = models.CharField(_('selling_price'), max_length=6, null=True, blank=True)
    # original_price = models.CharField(_('original_price'), max_length=6, null=True, blank=True)
    status = models.IntegerField(_('status'), null=True, blank=True)
    # course_level = models.CharField(_('course_level'), max_length=20, null=True, blank=True)
    # bestseller = models.IntegerField(_('bestseller'), null=True, blank=True)
    course_file = models.FileField(_('course_file'), null=True, blank=True, upload_to='course_file/')
    course_video = models.CharField(_('course_video'), max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    link = models.CharField(max_length=2000, blank=True, default='xxx')


class CourseStatus(models.Model):
    name = models.ForeignKey(Course, related_name='name', null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='course_status', null=False, on_delete=models.CASCADE)
    course_status = models.CharField(_('course_status'),max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Chapter(models.Model):
    chapter_name = models.CharField(_('chapter_name'),
                                    null=True,
                                    max_length=250,
                                    blank=True,
                                    help_text=_('Required. 250 characters or fewer. digits only.'),
                                    )
    course = models.ForeignKey(Course, related_name='course', null=False, on_delete=models.CASCADE,default=1)
    parent_id = models.IntegerField(_('parent_id'), default=0, blank=True)
    about = models.TextField(_('about'), null=True, blank=True)
    discussions = models.TextField(_('discussions'), null=True, blank=True)
    bookmarks = models.TextField(_('bookmarks'), null=True, blank=True)
    status = models.IntegerField(_('status'), null=True, blank=True)
    chapter_file = models.FileField(_('chapter_file'), null=True, blank=True, upload_to='chapter_file/')
    chapter_video = models.CharField(_('chapter_video'), max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    extra_file = models.FileField(_('extra_file'), null=True, blank=True, upload_to='chapter_file/')
    link = models.CharField(max_length=2000, blank=True, default='xxx')

    def __unicode__(self):
        return self.name
class ChapterStatus(models.Model):
    name = models.ForeignKey(Chapter, related_name='name', null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='chapter_status', null=False, on_delete=models.CASCADE)
    chapter_status = models.CharField(_('chapter_status'),max_length=50, null=True, blank=True)
    completedVideoLenght = models.DecimalField(max_digits=10, decimal_places=3,default=0.0)
    totalVideoLength = models.DecimalField(max_digits=10, decimal_places=3,default=0.0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CourseAlloted(models.Model):
    course_name = models.ForeignKey(Course, related_name='course_name', null=False, on_delete=models.CASCADE,default=1)
    user = models.ForeignKey(User, related_name='alloted_courses', null=False, on_delete=models.CASCADE,default=1)
    course_status = models.CharField(_('course_status'),max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Quiz_question(models.Model):
    course = models.ForeignKey(Course, related_name='course_quiz', null=False, on_delete=models.CASCADE,default=1)
    question = models.CharField(_('question'), max_length=50, null=True, blank=True)
    marks = models.CharField(_('marks'), max_length=50, null=True, blank=True)
    question_status = models.IntegerField(_('question_status'), null=True, blank=True)
    options = models.TextField(null=True,blank=False,default='xxxx')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Quiz_ques_answer(models.Model):
    question = models.ForeignKey(Quiz_question, related_name='question_id', null=False, on_delete=models.CASCADE,default=1)
    answer = models.CharField(_('answer'), max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Package(models.Model):
    name = models.CharField(max_length=150, blank=False)
    course = ListCharField(
        base_field=CharField(max_length=10),
        size=6,
        max_length=(6 * 11),  # 6 * 10 character nominals, plus commas
    )
    price = models.IntegerField(blank=True)
    about = models.TextField(_('about'), null=True, blank=True)
    image = models.ImageField(null= True, blank=True,upload_to='images/')
    # payment_link = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PackageAlloted(models.Model):
    package_name = models.ForeignKey(Package, related_name='package_name', null=False, on_delete=models.CASCADE,
                                     default=1)
    user = models.ForeignKey(User, related_name='package_alloted', null=False, on_delete=models.CASCADE, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Score(models.Model):
    user = models.ForeignKey(User, related_name='user_score', null=False, on_delete=models.CASCADE,default=1)
    course_score = models.ForeignKey(Course, related_name='course_score', null=False, on_delete=models.CASCADE,default=1)
    score = models.CharField(max_length=10,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Certificate(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_certificate', null=False, on_delete=models.CASCADE,default=1)
    course_score = models.ForeignKey(Course, related_name='course_completed', null=False, on_delete=models.CASCADE,default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Query(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254,)
    subject = models.CharField(max_length=500,blank=True,null=True)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payments(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_payment', null=False, on_delete=models.CASCADE)
    course = models.ForeignKey(Course,related_name='course_payment',null=True, on_delete=models.CASCADE)
    packge = models.ForeignKey(Package,related_name='package_payment',null=True,on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=250,null=True,blank=True)
    razorpay_payment_id = models.CharField(max_length=250,null=True,blank=True)
    razorpay_signature = models.CharField(max_length=250,null=True,blank=True)
