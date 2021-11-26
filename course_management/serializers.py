from rest_framework import serializers
from django.contrib.auth.models import User
from course_management.models import Course,Category,Chapter,CourseAlloted,Quiz_ques_answer,Quiz_question,Package,PackageAlloted,ChapterStatus,CourseStatus,Score,Banner,Upcomingevents,Services,CourseStatus,Query
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        # fields = ()
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upcomingevents
        # fields = ()
        fields = '__all__'


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        # fields = ()
        fields = '__all__'


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        # fields = '__all__'
        fields = ("id","name","about","course","image","price",)

class PackageallotedSerializer(serializers.ModelSerializer):
    package_name = PackageSerializer(read_only=True)
    class Meta:
        model = PackageAlloted
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        # fields = ("id","title","about","status","category_image","date")

class CourseSerializer(serializers.ModelSerializer):
    # category = CategorySerializer(read_only=True)
    class Meta:
        model = Course
        fields = "__all__"
        # fields = ("id","course_title","category_id","author","about","rating","total_hours","total_days","selling_price","original_price","status","course_level","bestseller","course_file","date")



class ScoreSerializer(serializers.ModelSerializer):
    # chapter_score = ChapterSerializer(read_only=True, many=True)
    class Meta:
        model = Score
        fields = ("score","user", )

class CourseAllotedSerializer(serializers.ModelSerializer):
    course_name = CourseSerializer(read_only=True)
    class Meta:
        model = CourseAlloted
        # fields = "__all__"
        fields = ("id","course_name", "course_status",)

# class CourseuserAllotedSerializer(serializers.ModelSerializer):
#     course_name = CourseSerializer(read_only=True)
#     class Meta:
#         model = CourseAlloted
#         # fields = "__all__"
#         fields = ("id","course_name", "course_status",)

class ChapterclientSerializer(serializers.ModelSerializer):
    # course = CourseSerializer(read_only=True)
    class Meta:
        model = Chapter
        fields = "__all__"

class ChapterStatusSerializer(serializers.ModelSerializer):
    # name = ChapterSerializer(read_only=True)
    class Meta:
        model = ChapterStatus
        fields = ("name",'user', "chapter_status","completedVideoLenght","totalVideoLength","is_completed")

class ChapterSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    # name = ChapterStatusSerializer(read_only=True,)
    class Meta:
        model = Chapter
        fields = "__all__"
        # fields = ("id", "course","chapter_name","about","discussions","bookmarks","status","chapter_file","chapter_video","extra_file","link","name")

class CourseStatusSerializer(serializers.ModelSerializer):
    name = ChapterSerializer(read_only=True)
    class Meta:
        model = CourseStatus
        fields = ("name", "course_status",)

class ChapterclientSerializer(serializers.ModelSerializer):
    name = ChapterStatusSerializer(read_only=True)
    class Meta:
        model = Chapter
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    # alloted_courses = CourseAllotedSerializer(read_only=True, many=True)
    package_alloted = PackageallotedSerializer(read_only=True, many=True)
    # chapter_status = ChapterStatusSerializer(read_only=True, many=True)
    class Meta:
        model = User
        # fields = "__all__"
        fields = ("id","token","first_name","user_role","last_name","username",'email','status','user_image','phone','package_alloted',)

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz_question
        fields = "__all__"
        # fields = ("id","chapter_id","question","marks","question_status","date")

class QuizQuesAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz_ques_answer
        fields = "__all__"
        # fields = ("id","question_id","answer","answer_status","correct_answer","date")

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        tokendata = super(MyTokenObtainPairSerializer, cls).get_token(user)

        # Add custom claims
        tokendata['username'] = user.username
        return tokendata

class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)



class UsercourseSerializer(serializers.Serializer):
    course_alotted = CourseAllotedSerializer(read_only=True, many=True)
    class Meta:
        model = User
        fields = ("id","token","first_name","user_role","last_name","username",'email','status','user_image','phone')


class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = '__all__'