from django.contrib import admin
from course_management.models import Course,Category,Chapter,CourseAlloted,Quiz_question,Quiz_ques_answer

# Register your models here.
admin.site.register(Course)
admin.site.register(Category)
admin.site.register(Chapter)
admin.site.register(CourseAlloted)
admin.site.register(Quiz_question)
admin.site.register(Quiz_ques_answer)