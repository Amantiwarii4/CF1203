from re import UNICODE
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.http.response import JsonResponse
from django.db.models import Q
from django.utils.functional import empty
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from course_management.models import Category, Course, Chapter, CourseAlloted, Quiz_question, Quiz_ques_answer, Package, PackageAlloted, CourseStatus, ChapterStatus, Score, Banner, Upcomingevents, Services, Certificate, Query, Payments
from course_management.serializers import ChangePasswordSerializer, QuizQuestionSerializer, QuizQuesAnswerSerializer, \
    CourseAllotedSerializer, UserSerializer, MyTokenObtainPairSerializer, CourseSerializer, CategorySerializer, \
    ChapterSerializer, UsercourseSerializer, PackageSerializer, PackageallotedSerializer, ChapterStatusSerializer, ScoreSerializer, BannerSerializer, EventSerializer, ServicesSerializer, ChapterclientSerializer, CourseStatusSerializer,QuerySerializer
from datetime import date, datetime
import random
import json
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import binascii
import base64
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.authentication import get_authorization_header
from rest_framework import HTTP_HEADER_ENCODING
import smtplib
import razorpay
# Create your views here.
renderer_classes = [JSONRenderer]


# def check_authenticated(funtion):
def authorized(request):
    auth = get_authorization_header(request).split()
    if not auth or auth[0].lower() != b'basic':
        msg = _("Not basic authentication.")
        result = {'status': False, 'message': msg}
        return result
    if len(auth) == 1:
        msg = _('Invalid basic header. No credentials provided.')
        result = {'status': False, 'message': msg}
        return result
    elif len(auth) > 2:
        msg = _('Invalid basic header. Credentials string should not contain spaces.')
        result = {'status': False, 'message': msg}
        return result
    try:
        auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
    except (TypeError, UnicodeDecodeError, binascii.Error):
        msg = _('Invalid basic header. Credentials not correctly base64 encoded.')
        result = {'status': False, 'message': msg}
        return result

    userid, password = auth_parts[0], auth_parts[2]
    # Your auth table specific codes
    if 'cyberfrat' == userid and '026866326a9d1d2b23226e4e8929192g' == password:  # my dummy code
        result = {'status': True, 'message': ""}
        return result
    else:
        msg = _('User not found.')
        result = {'status': False, 'message': msg}
        return result


def admin_dashboard(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            subadmin = User.objects.all().filter(user_role=3).count()
            users = User.objects.all().filter(user_role=4).count()
            active_subadmin = User.objects.all().filter(user_role=3, status=1).count()
            active_users = User.objects.all().filter(user_role=4, status=1).count()
            deactive_subadmin = User.objects.all().filter(user_role=3, status=2).count()
            deactive_users = User.objects.all().filter(user_role=4, status=2).count()
            data = {'subadmin': subadmin, 'users': users, 'active_subadmin': active_subadmin,
                    'active_users': active_users, 'deactive_subadmin': deactive_subadmin,
                    'deactive_users': deactive_users}
            return JsonResponse({'status': True, 'message': 'Dashboard data get successfully!', 'data': data},
                                safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)
        # 'safe=False' for objects serialization


@csrf_exempt
def change_password(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            try:
                users = User.objects.get(id=user_id)
                user_pass = users.password
            except:
                password_exist = {'password': ''}
                user_pass = password_exist['password']

            if check_password(old_password, user_pass) == True:
                if old_password == new_password:
                    return JsonResponse(
                        {'Status': False, 'Message': 'New password must be different from old password'},
                        status=status.HTTP_404_NOT_FOUND)
                else:
                    if new_password == confirm_password:
                        confirm_password = make_password(request.POST.get('confirm_password'))
                        user = User.objects.filter(id=user_id).update(password=confirm_password)
                        users = User.objects.get(id=user_id)
                        users_serializer = UserSerializer(users)
                        return JsonResponse({'status': True, 'message': 'Password changed successfully!',
                                             'data': users_serializer.data}, )
                    else:
                        return JsonResponse(
                            {'status': False, 'message': 'New password and confirm password must be same'},
                            )
            else:
                return JsonResponse({'status': False, 'message': 'Old password and current password does not match'},
                                    )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def allot_course(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                # client = razorpay.Client(auth = ("rzp_test_uyIMOvTtAIVnuN", "lj4ElrD7sKLSBczz2VqJnexz"))
                course_id = Course.objects.get(id=request.POST.get('course_id'))
                user_id = User.objects.get(id=request.POST.get('user_id'))
                try:
                    course = CourseAlloted.objects.get(user=user_id,course_name=course_id)
                except:
                    course = None
                try:
                    razorpay_order_id = request.POST.get('razorpay_order_id')
                    razorpay_payment_id = request.POST.get('razorpay_payment_id')
                    razorpay_signature = request.POST.get('razorpay_signature')
                except:
                    razorpay_order_id = None
                    razorpay_payment_id = None
                    razorpay_signature = None
                if razorpay_order_id is not None:
                    Payments.objects.create(user=user_id,course=course_id,razorpay_order_id=razorpay_order_id,razorpay_payment_id=razorpay_payment_id,razorpay_signature=razorpay_signature)
                if course == None:
                    course_allot = CourseAlloted.objects.create(course_name=course_id,
                                                                user=user_id, course_status='Active',)
                    courseAllot_serializer = CourseAllotedSerializer(data=course_allot)
                    courseAllot_serializer.is_valid()
                    course_status  = CourseStatus.objects.create(name=course_id,
                                                                user=user_id, course_status='0%',)
                    chapters = Chapter.objects.filter(course_id=course_id).values('id')
                    for i in chapters:
                        chapter = Chapter.objects.get(id=i['id'])
                        ChapterStatus.objects.create(name=chapter,user=user_id,chapter_status='0%',)
                    # course_allot = CourseAlloted.objects.get(id=course_allot.id)

                    # if course_allot.course_status == 1:
                    #     course_status = 'Active'
                    # elif course_allot.course_status == 2:
                    #     course_status = 'Completed'

                    # category = Category.objects.get(id=course_allot.category_id)
                    # course = Course.objects.get(id=course_allot.course_id)
                    # user = User.objects.get(id=course_allot.user_id)

                    # data = {'id': course_allot.id, 'course_status_value': course_allot.course_status,
                    #         'course_status': course_status, 'category_id': course_allot.category_id,
                    #         'category_name': category.title, 'course_id': course_allot.course_id,
                    #         'course_name': course.course_title, 'user_id': course_allot.user_id, 'user_name': user.username,
                    #         'date': course_allot.date}
                    return JsonResponse({'status': True, 'message': 'Course Alloted successfully!',},
                                        )
                else:
                    return JsonResponse({'status': True, 'message': 'This Course is already Alloted to this!', },
                                        )
                # return JsonResponse({'status': False, 'message': courseAllot_serializer.errors},
                #                     )
            else:
                return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status': False, 'Exception': str(e)}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)

@csrf_exempt
def change_course_status(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == "POST":
                user = User.objects.get(id=request.POST.get('user_id'))
                course = Course.objects.get(id=request.POST.get('course_id'))
                status = request.POST.get('status')
                CourseStatus.objects.filter(course_name=course,user=user,).update(course_status=status,)
                return JsonResponse({'status':True,'message':'status changed !!'})
        except Exception as e:
            return JsonResponse({'status':False,'Excaprion':str(e)})
    return JsonResponse({'message':'Unauthorise User!!',})

@csrf_exempt
def change_chapter_status(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == "POST":
                user = User.objects.get(id=request.POST.get('user_id'))
                chapter = Chapter.objects.get(id=request.POST.get('chapter_id'))
                course = Course.objects.get(id=request.POST.get('course_id'))
                status = request.POST.get('status')
                completedVideoLenght = request.POST.get('completedVideoLenght')
                totalVideoLength = request.POST.get('totalVideoLength')
                c_id = Chapter.objects.filter(course=course).values("id")
                ch_id = []
                for i in c_id:
                    ch_id.append(i["id"])
                chapter_count = len(ch_id)
                if float(status) >= 0.9:
                    is_completed = True
                else:
                    is_completed = False
                try:
                    c_status = ChapterStatus.objects.get(name=chapter,user=user,)
                except:
                    c_status = None
                if c_status is not None:
                    ChapterStatus.objects.filter(name=chapter,user=user,).update(chapter_status=status,completedVideoLenght=completedVideoLenght,totalVideoLength=totalVideoLength,is_completed=is_completed)
                    completed = ChapterStatus.objects.filter(name__in=ch_id,user=user).values('is_completed')
                    l = []
                    for i in completed:
                        l.append(i['is_completed'])
                    flse = l.count(False)
                    le = len(l)
                    if flse == 0 and le == chapter_count:
                        CourseStatus.objects.filter(user=user,name=course).update(course_status='completed')
                    else:
                        CourseStatus.objects.filter(user=user,name=course).update(course_status='0%')
                    return JsonResponse({'status':True,'message':'status changed !!','chapter_count':ch_id})
                else:
                    ChapterStatus.objects.create(name=chapter,user=user,chapter_status=status,completedVideoLenght=completedVideoLenght,totalVideoLength=totalVideoLength,is_completed=is_completed)
                    completed = ChapterStatus.objects.filter(name__in=ch_id,user=user).values('is_completed')
                    l = []
                    for i in completed:
                        l.append(i['is_completed'])
                    flse = l.count(False)
                    le = len(l)
                    if flse == 0 and le == chapter_count:
                        CourseStatus.objects.filter(user=user,name=course).update(course_status='completed')
                    else:
                        CourseStatus.objects.filter(user=user,name=course).update(course_status='0%')
                    return JsonResponse({'status':True,'message':'status changed !!',})
        except Exception as e:
            return JsonResponse({'status':False,'Excaprion':str(e)})
    return JsonResponse({'message':'Unauthorise User!!',})

@csrf_exempt
def courseAllot_completed(request, allotid):
    result = authorized(request)
    if result['status'] == True:
        try:
            courseAllotDetail = CourseAlloted.objects.get(id=allotid)
        except CourseAlloted.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Course Allot does not exist'},
                                )

        if request.method == 'GET':
            courseAllot = CourseAlloted.objects.filter(id=allotid).update(course_status=2)
            course_allot = CourseAlloted.objects.get(id=allotid)

            if course_allot.course_status == 1:
                course_status = 'Active'
            elif course_allot.course_status == 2:
                course_status = 'Completed'

            category = Category.objects.get(id=course_allot.category_id)
            course = Course.objects.get(id=course_allot.course_id)
            user = User.objects.get(id=course_allot.user_id)

            data = {'id': course_allot.id, 'course_status_value': course_allot.course_status,
                    'course_status': course_status, 'category_id': course_allot.category_id,
                    'category_name': category.title, 'course_id': course_allot.course_id,
                    'course_name': course.course_title, 'user_id': course_allot.user_id, 'user_name': user.username,
                    'date': course_allot.date}

            return JsonResponse({'status': True, 'message': 'Course completed successfully!', 'data': data},
                                )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def courseAllot_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            courseallot = CourseAlloted.objects.all().filter(~Q(id=1))
            courseallot_serializer = CourseAllotedSerializer(courseallot, many=True)
            return JsonResponse(
                {'status': True, 'message': 'course allot listed successfully!', 'data': courseallot_serializer.data},
                safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
            # 'safe=False' for objects serialization
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)

@csrf_exempt
def add_package(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                name = request.POST.get('name')
                course = request.POST.get('course')
                about = request.POST.get('about')
                price = request.POST.get('price')
                image = request.FILES["image"]
                # payment_link = request.POST.get('payment_link')
                Package.objects.create(name=name,course=course,about=about,price=price,image=image,)
                return JsonResponse({"status":True,"message":"Package created sucessfull"})
        except Exception as e:
            return JsonResponse({"status":False,"exception":str(e)})
    return JsonResponse({"message":"Unauthorised User",})

@csrf_exempt
def edit_package(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                id = request.POST.get('id')
                name = request.POST.get('name')
                course = request.POST.get('course')
                about = request.POST.get('about')
                price = request.POST.get('price')
                try:
                    image = request.FILES["image"]
                except:
                    image = None
                if image == None:
                    Package.objects.filter(id=id).update(name=name,course=course,about=about,price=price)
                    return JsonResponse({"status":True,"message":"Package updated sucessfull"})
                else:
                    Package.objects.filter(id=id).update(name=name,course=course,about=about,price=price,image=image)
                    package = Package.objects.get(id=id)
                    package.image = image
                    package.save()
                    return JsonResponse({"status":True,"message":"Package updated sucessfull"})
        except Exception as e:
            return JsonResponse({"status":False,"exception":str(e)})
    return JsonResponse({"message":"Unauthorised User",})

def show_package(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "GET":
            try:
                package = Package.objects.all().order_by('-id')
                package_serializer = PackageSerializer(package, many=True)
                return JsonResponse({"status":True,"data":package_serializer.data})
            except Exception as e:
                return JsonResponse({"status":False, "Exception":str(e)})
    return JsonResponse({"status":False, "message":"Unauthorise User"})

@csrf_exempt
def show_package_course(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "POST":
            try:
                courses = Package.objects.filter(id=request.POST.get('package_id')).values("course")
                s = courses[0]
                k = s["course"]
                l = []
                for i in k:
                    l.append(int(i))
                course =  Course.objects.filter(id__in=l).all()
                course_serializer = CourseSerializer(course,many=True)
                return JsonResponse({'status':True,'data':course_serializer.data,})
            except Exception as e:
                return JsonResponse({'status':False,'Exception':str(e)})
    return JsonResponse({"status":False, "message":"Unauthorise User"})

@csrf_exempt
def delete_package(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                id = request.POST.get('id')
                package = Package.objects.get(id=id)
                package.delete()
                return JsonResponse({ 'status': True, 'message': 'Package deleted successfully!'})
            except:
                return JsonResponse({ 'status': False, 'message': 'id does not exist'})
    return JsonResponse({"message":"Unauthorise User",})

@csrf_exempt
def allot_package(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            courses = Package.objects.filter(id=request.POST.get('package_id')).values("course")
            package = Package.objects.get(id=request.POST.get('package_id'))
            user = User.objects.get(id=request.POST.get('user_id'))
            try:
                razorpay_order_id = request.POST.get('razorpay_order_id')
                razorpay_payment_id = request.POST.get('razorpay_payment_id')
                razorpay_signature = request.POST.get('razorpay_signature')
            except:
                razorpay_order_id = None
                razorpay_payment_id = None
                razorpay_signature = None
            if razorpay_order_id is not None:
                Payments.objects.create(user=user_id,course=course_id,razorpay_order_id=razorpay_order_id,razorpay_payment_id=razorpay_payment_id,razorpay_signature=razorpay_signature)
            try:
                package_alloted = PackageAlloted.objects.get(user=user)
                PackageAlloted.objects.filter(user=user).update(package_name=package)
                s = courses[0]
                k = s["course"]
                # course = s.split(",")
                for i in k:
                    course_id = Course.objects.get(id=int(i))
                    try:
                        course = CourseAlloted.objects.get(user=user,course_name=course_id)
                    except:
                        course = None
                    if course == None:
                        course_allot = CourseAlloted.objects.create(course_name=course_id,
                                                                    user=user, course_status='Active',)
                        courseAllot_serializer = CourseAllotedSerializer(data=course_allot)
                        courseAllot_serializer.is_valid()
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                    else:
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                return JsonResponse({'status':True,'message':'Package alloted',})
            except:
                package_alloted = None
            if package_alloted == None:
                PackageAlloted.objects.create(package_name=package,user=user)
                s = courses[0]
                k = s["course"]
                # course = s.split(",")
                for i in k:
                    course_id = Course.objects.get(id=int(i))
                    try:
                        course = CourseAlloted.objects.get(user=user,course_name=course_id)
                    except:
                        course = None
                    if course == None:
                        course_allot = CourseAlloted.objects.create(course_name=course_id,
                                                                    user=user, course_status='Active',)
                        courseAllot_serializer = CourseAllotedSerializer(data=course_allot)
                        courseAllot_serializer.is_valid()
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                return JsonResponse({'status':True,'message':'Package alloted'})
        except Exception as e:
            return JsonResponse({'status':False,'Exception':str(e),})
    return JsonResponse({'status':False,'message':'Unauthorised User'})


def auto_allot_package(user_id,package_id):
    result = authorized(request)
    if result['status'] == True:
        try:
            courses = Package.objects.filter(id=package_id).values("course")
            package = Package.objects.get(id=package_id)
            user = User.objects.get(id=user_id)
            try:
                package_alloted = PackageAlloted.objects.get(user=user)
                PackageAlloted.objects.filter(user=user).update(package_name=package)
                s = courses[0]
                k = s["course"]
                # course = s.split(",")
                for i in k:
                    course_id = Course.objects.get(id=int(i))
                    try:
                        course = CourseAlloted.objects.get(user=user,course_name=course_id)
                    except:
                        course = None
                    if course == None:
                        course_allot = CourseAlloted.objects.create(course_name=course_id,
                                                                    user=user, course_status='Active',)
                        courseAllot_serializer = CourseAllotedSerializer(data=course_allot)
                        courseAllot_serializer.is_valid()
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                    else:
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                return JsonResponse({'status':True,'message':'Package alloted successfull',})
            except:
                package_alloted = None
            if package_alloted == None:
                PackageAlloted.objects.create(package_name=package,user=user)
                s = courses[0]
                k = s["course"]
                # course = s.split(",")
                for i in k:
                    course_id = Course.objects.get(id=int(i))
                    try:
                        course = CourseAlloted.objects.get(user=user,course_name=course_id)
                    except:
                        course = None
                    if course == None:
                        course_allot = CourseAlloted.objects.create(course_name=course_id,
                                                                    user=user, course_status='Active',)
                        courseAllot_serializer = CourseAllotedSerializer(data=course_allot)
                        courseAllot_serializer.is_valid()
                        try:
                            course_status  = CourseStatus.objects.get(user=user,name_id=course_id)
                        except:
                            course_status = None
                        if course_status == None:
                            course_status  = CourseStatus.objects.create(name=course_id,
                                                                    user=user, course_status='0%',)
                        chapters = Chapter.objects.filter(course_id=course_id).values('id')
                        for i in chapters:
                            chapter = Chapter.objects.get(id=i['id'])
                            try:
                                chapter_status = ChapterStatus.objects.get(user=user,name_id=chapter)
                            except:
                                chapter_status = None
                            if chapter_status == None:
                                ChapterStatus.objects.create(name=chapter,user=user,chapter_status='0%',)
                return JsonResponse({'status':True,'message':'Package alloted successfull'})
        except Exception as e:
            return JsonResponse({'status':False,'Exception':str(e),})
    return JsonResponse({'status':False,'message':'Unauthorised User'})


def show_allotpackage(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            package = PackageAlloted.objects.all().order_by('-id')
            package_serializer = PackageallotedSerializer(package,many=True)
            return JsonResponse({'status':True,'data': package_serializer.data})
    return JsonResponse({'status':False,'message':'Unauthorised User'})


@csrf_exempt
def show_client_package(request,user_id):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'GET':
                # courses = Package.objects.filter(id=request.POST.get('package_id')).values("course")
                user = User.objects.get(id=user_id)
                # s = courses[0]
                # s = s["course"].strip('[]')
                # course = s.split(",")
                # data = []
                # for i in course:
                #     courses = Course.objects.filter(id=int(i)).all()
                #     data.append(courses)
                # allot_courses = CourseAlloted.objects.filter(user=user).values('course_name')
                allot_courses = CourseAlloted.objects.filter(user=user)
                # l = []
                # for i in allot_courses:
                #     l.append(i['course_name'])
                # course = CourseStatus.objects.filter(name__in=l,user=user).all()
                # serializer = CourseStatusSerializer(course,many=True)
                serializer = CourseAllotedSerializer(allot_courses,many=True)
                return JsonResponse({"status":True,'data':serializer.data})
        except Exception as e:
            return JsonResponse({"status":False,'Exception':str(e)})
    return JsonResponse({"status":False,"message":"Unauthorised User"})


# Users Functions
@csrf_exempt
def user_login(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            tok = MyTokenObtainPairSerializer()
            # logged in using email and password
            email = request.POST.get('email')
            password = request.POST.get('password')
            try:
                users = User.objects.get(email=email)
                user_pass = users.password
                if users.user_role == 4:
                    type = 'user'
                elif users.user_role == 3:
                    type = 'subadmin'
                else:
                    type = 'admin'
                k = 'chal rha hai'
            except:
                password_exist = {'password': ''}
                user_pass = password_exist['password']
                k= 'nhi chal rha'
            if check_password(password, user_pass) == True:
                tokendata = tok.get_token(users)
                stoken = str(tokendata)

                users = User.objects.get(email=email)
                User.objects.filter(id=users.id).update(token=stoken)

                users = User.objects.get(email=email)
                users_serializer = UserSerializer(users)
                return JsonResponse(
                    {'status': True, 'message': 'User logged in successful!', 'data': users_serializer.data,
                     'type': type
                     })
            else:
                return JsonResponse(
                    {'status': False, 'message': 'User not found!','k':k
                     })
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def forgot_password(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "POST":
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
            except:
                user = None
                return JsonResponse({'status': False, 'message': 'Email not found'})
            otp = random.randint(1111, 9999)
            User.objects.filter(email=email).update(otp=otp)
            gmail_user = 'your_email@gmail.com'
            gmail_password = 'your_password'

            sent_from = gmail_user
            to = email
            subject = 'OTP'
            body = 'Your otp is ' + str(otp) + ' .'

            email_text = """\
            From: %s
            To: %s
            Subject: %s

            %s
            """ % (sent_from, ", ".join(to), subject, body)

            try:
                smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                smtp_server.ehlo()
                smtp_server.login(gmail_user, gmail_password)
                smtp_server.sendmail(sent_from, to, email_text)
                smtp_server.close()
                print("Email sent successfully!")
            except Exception as ex:
                return JsonResponse({"Exception": str(ex), })
            return JsonResponse({'status': True, 'message': 'OTP sent to your email', 'otp': otp})
    return JsonResponse({'status': False, 'message': 'Unauthorised'})

@csrf_exempt
def send_payment_mail(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "POST":
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
            except:
                user = None
                return JsonResponse({'status': False, 'message': 'Email not found'})
            otp = random.randint(1111, 9999)
            User.objects.filter(email=email).update(otp=otp)
            gmail_user = 'your_email@gmail.com'
            gmail_password = 'your_password'

            sent_from = gmail_user
            to = email
            subject = 'Payment Link'
            body = 'Your otp is ' + str(otp) + ' .'

            email_text = """\
            From: %s
            To: %s
            Subject: %s

            %s
            """ % (sent_from, ", ".join(to), subject, body)

            try:
                smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                smtp_server.ehlo()
                smtp_server.login(gmail_user, gmail_password)
                smtp_server.sendmail(sent_from, to, email_text)
                smtp_server.close()
                print("Email sent successfully!")
            except Exception as ex:
                return JsonResponse({"Exception": str(ex), })
            return JsonResponse({'status': True, 'message': 'OTP sent to your email', 'otp': otp})
    return JsonResponse({'status': False, 'message': 'Unauthorised'})


@csrf_exempt
def check_token(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            token = request.POST.get('token')
            userid = request.POST.get('user_id')
            try:
                users = User.objects.get(token=token, id=userid)
                return JsonResponse({'status': True, 'message': 'Token exist!', 'data': ""})
            except User.DoesNotExist:
                return JsonResponse({'status': False, 'message': "Token doesn't exist"},
                                    status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def add_user(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                try:
                    userImage = request.FILES["user_image"]
                except:
                    userImage = None

                username = random.randint(1111, 9999)
                email = request.POST.get('email')
                password = request.POST.get('password')
                phone = request.POST.get('phone')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                user_role = request.POST.get('user_role')
                about = None
                user_image = userImage

                userphone = User.objects.filter(phone=phone)
                useremail = User.objects.filter(email=email)
                if (userphone or useremail):
                    if (userphone):
                        return JsonResponse({'status': False, 'message': 'A user with that phone already exists.'},
                                            )
                    elif (useremail):
                        return JsonResponse({'status': False, 'message': 'A user with that email already exists.'},
                                            )
                    else:
                        return JsonResponse({'status': False, 'message': 'Something went wrong'},
                                            )
                else:
                    users_serializer = UserSerializer(data=request.POST)
                    users_serializer.is_valid()
                    user = User.objects.create_user(username=username, status=1, email=email, password=password,
                                                    first_name=first_name, user_image=user_image, user_role=user_role,
                                                    phone=phone, last_name=last_name)
                    user.save()
                    id = user.id

                    # email functionality
                    # subject = "New User Registration"
                    # message = "You are receiving this mail because your email is registered with our panel. Your Credentials are:- Email:- " + email + " Password:- " + password
                    # email_from = "noreply@i4dev.in"
                    # recipient_list = {email}
                    # send_mail(subject, message, email_from, recipient_list)

                    # users = User.objects.get(id=id)
                    if user.user_role == 4:
                        type = 'user'
                    elif user.user_role == 3:
                        type = 'subadmin'
                    else:
                        type = 'admin'

                    users_serializer = UserSerializer(user)
                    return JsonResponse(
                            {'status': True, 'message': 'User added successfully!', 'data': users_serializer.data,
                             }, )
                    # return JsonResponse({'status': False, 'message': users_serializer.errors},
                    #                     )
        except Exception as e:
            return JsonResponse(
                        {'status': False, 'Exception': str(e),
                             }, )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def user_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            users = User.objects.all().filter(~Q(id=1))
            users_serializer = UserSerializer(users, many=True)
            return JsonResponse(
                {'status': True, 'message': 'Users listed successfully!', 'data': users_serializer.data}, safe=False)
            # 'safe=False' for objects serialization
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)
import string
@csrf_exempt
def singup(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            # dob = request.POST.get('dob')
            # gender = request.POST.get('gender')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            try:
                user = User.objects.get(phone=phone)
            except:
                user = None
            try:
                email1 = User.objects.get(email=email)
            except:
                email1 = None
            if user is not None:
                return JsonResponse({'status':False,'message':'Phone no. already exist',})
            if email1 is not None:
                return JsonResponse({'status':False,'message':'Email alreday exist'})
            else:
                S = 10
                username = ''.join(random.choices(string.ascii_uppercase + string.digits, k=S))

                user = User.objects.create_user(username=str(username),
                                                        phone=phone,first_name=first_name,
                                                        email=email,last_name=last_name,password=password)
                user_serializer = UserSerializer(user)
                return JsonResponse({'status':True,'message':'User added','data':user_serializer.data})
        except Exception as e:
            return JsonResponse({'status':False,'message':str(e)})
    return JsonResponse({"message": "Unauthorised User", })

def user_detail(request, uid):
    result = authorized(request)
    if result['status'] == True:
        try:
            userDetail = User.objects.get(id=uid)
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The User does not exist'},
                                )

        if request.method == 'GET':
            users_serializer = UserSerializer(userDetail)
            return JsonResponse(
                {'status': True, 'message': 'User details get successfully!', 'data': users_serializer.data},
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def user_edit(request):
    result = authorized(request)
    if result['status'] == True:
        uid = request.POST.get('user_id')
        try:
            userDetail = User.objects.get(id=uid)
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The User does not exist'},
                                )
        if request.method == 'POST':
            try:
                userImage = request.FILES["user_image"]
            except:
                userImage = userDetail.user_image
            # exit()
            username = random.randint(1111, 9999)
            email = request.POST.get('email')
            password = userDetail.password
            phone = request.POST.get('phone')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user_role = userDetail.user_role
            # about = request.POST.get('about')
            user_image = userImage
            # exit()
            users_serializer = UserSerializer(data=request.POST)
            if users_serializer.is_valid():
                user = User.objects.filter(id=uid).update(username=username, email=email, password=password,
                                                          first_name=first_name, user_role=user_role, phone=phone,
                                                          last_name=last_name)
                users = User.objects.get(id=uid)
                users.user_image = user_image
                users.save()
                userdata = User.objects.get(id=uid)
                users_serializer = UserSerializer(userdata)
                # if userdata.user_role == 4:
                #     type = 'user'
                # elif userdata.user_role == 3:
                #     type = 'subadmin'
                # elif userdata.user_role == 2:
                #     type = 'admin'
                return JsonResponse(
                    {'status': True, 'message': 'User update successfully!', 'data': users_serializer.data},
                )
            return JsonResponse({'status': False, 'message': users_serializer.errors},
                                )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def user_delete(request, uid):
    result = authorized(request)
    if result['status'] == True:
        try:
            userDetail = User.objects.get(id=uid)
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The User does not exist'},
                                )

        if request.method == 'DELETE':
            userDetail.delete()
            return JsonResponse({'status': True, 'message': 'User deleted successfully!'},
                                )
        else:
            return JsonResponse({'status': False, 'message': 'Only delete method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def user_changeStatus(request, uid):
    result = authorized(request)
    if result['status'] == True:
        try:
            userDetail = User.objects.get(id=uid)
        except User.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The User does not exist'},
                                status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            user = User.objects.filter(id=uid).update(status=2)
            users = User.objects.get(id=uid)
            user_serializer = UserSerializer(users)
            return JsonResponse(
                {'status': True, 'message': 'User status changed successfully!', 'data': user_serializer.data},
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


# User Functions end

# category Functions
@csrf_exempt
def add_category(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                title = request.POST.get('title')
                about = request.POST.get('about')
                category_image = request.FILES["category_image"]
                category_serializer = CategorySerializer(data=request.POST)
                if category_serializer.is_valid():
                    category = Category.objects.create(title=title, about=about, category_image=category_image,
                                                       )
                    # category.save()
                    id = category.id
                    categorys = Category.objects.get(id=id)
                    category_serializer = CategorySerializer(categorys)
                    return JsonResponse(
                        {'status': True, 'message': 'Category added successfully!', 'data': category_serializer.data},
                    )
                return JsonResponse({'status': False, 'message': category_serializer.errors},
                                    )
            else:
                return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'Exception': str(e), })
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def category_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            category = Category.objects.all().order_by('id').reverse()
            category_serializer = CategorySerializer(category, many=True)
            return JsonResponse(
                {'status': True, 'message': 'category listed successfully!', 'data': category_serializer.data},
                safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def category_detail(request, catid):
    result = authorized(request)
    if result['status'] == True:
        try:
            categoryDetail = Category.objects.get(id=catid)
        except Category.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Category does not exist'},
                                )

        if request.method == 'GET':
            category_serializer = CategorySerializer(categoryDetail)
            return JsonResponse(
                {'status': True, 'message': 'User details get successfully!', 'data': category_serializer.data},
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def category_edit(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            catid = request.POST.get('category_id')
            try:
                categoryDetail = Category.objects.get(id=catid)
            except Category.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'The Category does not exist'},
                                    status=status.HTTP_404_NOT_FOUND)

            if request.method == 'POST':
                title = request.POST.get('title')
                about = request.POST.get('about')
                try:
                    category_image = request.FILES["image"]
                except:
                    category_image=None
                category_serializer = CategorySerializer(data=request.POST)
                if category_serializer.is_valid() and category_image is not None:
                    category = Category.objects.filter(id=catid).update(title=title, about=about)
                    categorys = Category.objects.get(id=catid)
                    categorys.category_image = category_image
                    categorys.save()
                    categorys = Category.objects.get(id=catid)
                    category_serializer = CategorySerializer(categorys)
                    return JsonResponse({'message': 'Category update successfully!', 'data': category_serializer.data},
                                        )
                else:
                    category = Category.objects.filter(id=catid).update(title=title, about=about)
                    return JsonResponse({'message': 'Category update successfully!', 'data': category_serializer.data},
                                        )
                return JsonResponse({'status': True, 'message': category_serializer.errors},
                                    )
            else:
                return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'Exception': str(e),})

    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def category_delete(request, catid):
    result = authorized(request)
    if result['status'] == True:
        try:
            categoryDetail = Category.objects.get(id=catid)
        except Category.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Category does not exist'},
                                )

        if request.method == 'DELETE':
            categoryDetail.delete()
            return JsonResponse({'status': True, 'message': 'Category deleted successfully!'},
                                )
        else:
            return JsonResponse({'status': False, 'message': 'Only delete method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def category_changeStatus(request, catid):
    result = authorized(request)
    if result['status'] == True:
        try:
            categoryDetail = Category.objects.get(id=catid)
        except Category.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Category does not exist'},
                                 )

        if request.method == 'GET':
            category = Category.objects.filter(id=catid).update(status=2)
            categorys = Category.objects.get(id=catid)
            category_serializer = CategorySerializer(categorys)
            return JsonResponse(
                {'status': True, 'message': 'Category status changed successfully!', 'data': category_serializer.data},
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


# category Functions End


# Category Course Function
@csrf_exempt
def add_course(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                course_title = request.POST.get('course_title')
                # category_id = request.POST.get('category_id')
                author = request.POST.get('author')
                about = request.POST.get('about')
                # rating = request.POST.get('rating')
                # total_hours = request.POST.get('total_hours')
                # total_days = request.POST.get('total_days')
                selling_price = request.POST.get('selling_price')
                # original_price = request.POST.get('original_price')
                # course_level = request.POST.get('course_level')
                # bestseller = request.POST.get('bestseller')
                link = request.POST.get('link')
                course_file = request.FILES["course_file"]
                # category = Category.objects.get(id=category_id)
                course_serializer = CourseSerializer(data=request.POST)
                course_serializer.is_valid()
                course = Course.objects.create(course_title=course_title, author=author,
                                               about=about, status='1',
                                              course_file=course_file, link=link,selling_price=selling_price)
                id = course.id
                courses = Course.objects.get(id=id)
                course_serializer = CourseSerializer(courses)
                return JsonResponse(
                    {'status': True, 'message': 'Course added successfully!', 'data': course_serializer.data},
                )
            else:
                return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({"Exception":str(e),})
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def course_list(request, catid):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            category = Category.objects.get(id=request.POST.get('category_id'))
            course = Course.objects.all().filter(category=category).order_by('id').reverse()
            course_serializer = CourseSerializer(course, many=True)

            # categoryDetail = Category.objects.get(id=catid)
            return JsonResponse(
                {'status': True, 'message': 'Course listed successfully!', 'data': course_serializer.data,
                 'category_name': categoryDetail.title}, safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def all_course(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            course = Course.objects.all().order_by('id').reverse()
            course_serializer = CourseSerializer(course, many=True)
            return JsonResponse(
                {'status': True, 'message': 'Course listed successfully!', 'data': course_serializer.data}, safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)



def course_detail(request, cid):
    result = authorized(request)
    if result['status'] == True:
        try:
            courseDetail = Course.objects.get(id=cid)
        except Course.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The course does not exist'},
                                status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            course_serializer = CourseSerializer(courseDetail)

            # chapter = Chapter.objects.all().filter(course_id=cid)
            # chapter_serializer = ChapterSerializer(chapter, many=True)

            # categoryDetail = Category.objects.get(id=courseDetail.category_id)
            # category_serializer = CategorySerializer(categoryDetail)
            return JsonResponse(
                {'status': True, 'message': 'course details get successfully!', 'data': course_serializer.data,
                 },
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def course_edit(request):
    result = authorized(request)
    if result['status'] == True:
        cid = request.POST.get('course_id')
        try:
            courseDetail = Course.objects.get(id=cid)
        except Course.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Course does not exist'},
                                )
        try:
            if request.method == 'POST':
                course_title = request.POST.get('course_title')
                # category_id = request.POST.get('category_id')
                author = request.POST.get('author')
                about = request.POST.get('about')
                # rating = request.POST.get('rating')
                # total_hours = request.POST.get('total_hours')
                # total_days = request.POST.get('total_days')
                selling_price = request.POST.get('selling_price')
                # original_price = request.POST.get('original_price')
                # course_level = request.POST.get('course_level')
                # bestseller = request.POST.get('bestseller')
                link = request.POST.get('link')
                try:
                    course_file = request.FILES["course_file"]
                except:
                    course_file = None
                # category = Category.objects.get(id=category_id)
                course_serializer = CourseSerializer(data=request.POST)
                course_serializer.is_valid()
                if course_file is not None:
                    courses = Course.objects.filter(id=cid).update(course_title=course_title, author=author,
                                                   about=about, status='1',
                                                  link=link,selling_price=selling_price)
                    course = Course.objects.get(id=cid)
                    course.course_file = course_file
                    course.save()
                    course = Course.objects.get(id=cid)
                    course_serializer = CourseSerializer(course)
                    return JsonResponse(
                        {'status': True, 'message': 'Course update successfully!', 'data': course_serializer.data},
                    )
                else:
                    courses = Course.objects.filter(id=cid).update(course_title=course_title, author=author,
                                                   about=about, status='1',
                                                  link=link,selling_price=selling_price)
                    # course = Course.objects.get(id=cid)
                    # course.course_file = course_file
                    # course.save()
                    course = Course.objects.get(id=cid)
                    course_serializer = CourseSerializer(course)
                    return JsonResponse(
                        {'status': True, 'message': 'Course update successfully!', 'data': course_serializer.data},
                    )

        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def course_delete(request, cid):
    result = authorized(request)
    if result['status'] == True:
        try:
            courseDetail = Course.objects.get(id=cid)
        except Course.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Course does not exist'},
                                status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            courseDetail.delete()
            return JsonResponse({'status': True, 'message': 'Course deleted successfully!'},
                                status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse({'status': False, 'message': 'Only delete method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


@csrf_exempt
def course_changeStatus(request, cid):
    result = authorized(request)
    if result['status'] == True:
        try:
            courseDetail = Course.objects.get(id=cid)
        except Course.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The Course does not exist'}
                                )

        if request.method == 'GET':
            course = Course.objects.filter(id=cid).update(status=2)
            courses = Course.objects.get(id=cid)
            course_serializer = CourseSerializer(courses)
            return JsonResponse(
                {'status': True, 'message': 'Course status changed successfully!', 'data': course_serializer.data},
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


# category Course Functions End


# #Category Course Chapter Function
@csrf_exempt
def add_chapter(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                courseid = Course.objects.get(id=request.POST.get('course_id'))

                chapter_name = request.POST.get('chapter_name')
                # category_id = courseid.category_id
                about = request.POST.get('about')
                discussions = request.POST.get('discussions')
                bookmarks = request.POST.get('bookmarks')
                try:
                    chapter_file = request.FILES["chapter_file"]
                except:
                    chapter_file = None
                try:
                    extra_file = request.FILES["attachment"]
                except:
                    extra_file = None
                try:
                    link = request.POST.get('link')
                except:
                    link = None
                chapter_serializer = ChapterSerializer(data=request.POST)
                chapter_serializer.is_valid()
                chapter = Chapter.objects.create(chapter_name=chapter_name,
                                                 course=courseid, about=about, discussions=discussions, status='1',
                                                 bookmarks=bookmarks, chapter_file=chapter_file,link=link,extra_file=extra_file )
                id = chapter.id
                chapters = Chapter.objects.get(id=id)
                chapter_serializer = ChapterSerializer(chapters)
                return JsonResponse(
                    {'status': True, 'message': 'Chapter added successfully!', 'data': chapter_serializer.data},
                )
            else:
                return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status': False, 'Exception': str(e)})
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def chapter_list(request,course_id):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'GET':
                cid = Course.objects.get(id=course_id)
                chapter = Chapter.objects.filter(course=cid).all().order_by('id').reverse()
                chapter_serializer = ChapterSerializer(chapter, many=True)
                return JsonResponse(
                    {'status': True, 'message': 'Chapter listed successfully!', 'data': chapter_serializer.data},
                    safe=False)
            else:
                return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status': False, 'Exception':str(e)})
    return JsonResponse({'status': False, 'message': 'Something went wrong'}, safe=False)

@csrf_exempt
def chapter_client_list(request):
    result = authorized(request)
    if result['status'] == True:
        # try:
        if request.method == 'POST':
            id = request.POST.get('course_id')
            user_id = request.POST.get('user_id')
            user = User.objects.get(id=user_id)
            c_id = Course.objects.get(id=id)
            chapter1 = Chapter.objects.filter(course=c_id,).all()
            # chapter1 = Chapter.objects.filter(course=c_id,name__user_id=user).all()
            # chapter1 = Chapter.objects.filter(course=c_id,name__user_id=user).values("course","chapter_name","about","discussions","bookmarks","status","chapter_file","chapter_video","extra_file","link","name__chapter_status","name__completedVideoLenght",'name__totalVideoLength','name__is_completed')
            chapter = Chapter.objects.filter(course=c_id).values('id')
            try:
                score = Score.objects.get(user=user,course_score=c_id)
            except:
                score = None
            cid = []
            for i in chapter:
                cid.append(i['id'])
            chapter_serializer = ChapterSerializer(chapter1,many=True)
            chapter_status = ChapterStatus.objects.filter(user=user,name__in=cid).all()
            chapter_status_serializer = ChapterStatusSerializer(chapter_status,many=True)
            course_status = CourseStatus.objects.filter(name=c_id,user=user).values('course_status')
            course_status1 = course_status[0]
            if score == None:
                quiz_done = False
                ispass = False
            else:
                quiz_done = True
                ispass = score.ispass
            chapter_data = chapter_serializer.data
            chapter_status_data = chapter_status_serializer.data
            for i in chapter_data:
                i['chapter_status'] = None
                for j in chapter_status_data:
                    if i['id'] == j['name']:
                        i['chapter_status'] = j
                    else:
                        pass
            return JsonResponse(
                {'status': True, 'message': 'Chapter listed successfully!', 'chapter_data': chapter_data, 'course_status':course_status1['course_status'],'Quiz_Completed':quiz_done,'ispass':ispass},
                safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
        # except Exception as e:
        #     return JsonResponse({'status': False, 'Exception':str(e)})
    return JsonResponse({'status': False, 'message': 'Something went wrong'}, safe=False)


def all_chapter(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            chapter = Chapter.objects.all().order_by('id').reverse()
            chapter_serializer = ChapterSerializer(chapter, many=True)
            return JsonResponse(
                {'status': True, 'message': 'Chapters listed successfully!', 'data': chapter_serializer.data},
                safe=False)
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status': result['status'], 'message': result['message']}, safe=False)


def chapter_detail(request, chid):
    result = authorized(request)
    if result['status'] == True:
        try:
            chapterDetail = Chapter.objects.get(id=chid)
        except Chapter.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'The chapter does not exist'},
                                )

        if request.method == 'GET':
            chapter_serializer = ChapterSerializer(chapterDetail)

            # courseDetail = Course.objects.get(id=chapterDetail.course_id)
            # course_serializer = CourseSerializer(courseDetail)

            # categoryDetail = Category.objects.get(id=chapterDetail.category_id)
            # category_serializer = CategorySerializer(categoryDetail)
            return JsonResponse(
                {'status': True, 'message': 'chapter details get successfully!', 'data': chapter_serializer.data,
                 },
            )
        else:
            return JsonResponse({'status': False, 'message': 'Only get method is allowed'}, safe=False)

# def chapter_detail(request,chid):
#     result = authorized(request)
#     if result['status'] == True:
#         try:
#             chapterDetail = Chapter.objects.get(id=chid)
#         except Chapter.DoesNotExist:
#             return JsonResponse({'status':False,'message': 'The chapter does not exist'}, status=status.HTTP_404_NOT_FOUND)

#         if request.method == 'GET':
#             chapter_serializer = ChapterSerializer(chapterDetail)

#             courseDetail = Course.objects.get(id=chapterDetail.course_id)
#             course_serializer = CourseSerializer(courseDetail)

#             categoryDetail = Category.objects.get(id=chapterDetail.category_id)
#             category_serializer = CategorySerializer(categoryDetail)
#             return JsonResponse({'status':True,'message': 'chapter details get successfully!','data':chapter_serializer.data,'category_data':category_serializer.data,'course_data':course_serializer.data}, status=status.HTTP_201_CREATED)
#         else:
#             return JsonResponse({'status':False,'message': 'Only get method is allowed'}, safe=False)

@csrf_exempt
def chapter_edit(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            chid = request.POST.get('chapter_id')
            try:
                chapterDetail = Chapter.objects.get(id=chid)
            except Chapter.DoesNotExist:
                return JsonResponse({'status':False,'message': 'The chapter does not exist'})

            if request.method == 'POST':
                course_id = Course.objects.get(id=request.POST.get('course_id'))

                chapter_name = request.POST.get('chapter_name')
                # category_id = courseid.category_id
                about = request.POST.get('about')
                discussions = request.POST.get('discussions')
                bookmarks = request.POST.get('bookmarks')
                try:
                    chapter_file = request.FILES["chapter_file"]
                except:
                    chapter_file = None
                try:
                    extra_file = request.FILES["attachment"]
                except:
                    extra_file = None
                try:
                    link = request.POST.get('link')
                except:
                    link = None

                chapter_serializer = ChapterSerializer(data=request.POST)
                chapter_serializer.is_valid()
                if chapter_file is not None and extra_file is not None:
                    chapters = Chapter.objects.filter(id=chid).update(chapter_name = chapter_name ,course = course_id,about = about,discussions = discussions,bookmarks = bookmarks,link=link)
                    chapter = Chapter.objects.get(id=chid)
                    chapter.chapter_file = chapter_file
                    chapter.extra_file = extra_file
                    chapter.save()

                elif chapter_file is not None:
                    chapter = Chapter.objects.get(id=chid)
                    chapter.chapter_file = chapter_file
                    chapter.save()
                    chapters = Chapter.objects.filter(id=chid).update(chapter_name = chapter_name ,course = course_id,about = about,discussions = discussions,bookmarks = bookmarks,link=link)

                else:
                    chapters = Chapter.objects.filter(id=chid).update(chapter_name = chapter_name ,course = course_id,about = about,discussions = discussions,bookmarks = bookmarks,link=link)

                return JsonResponse({'status':True,'message': 'chapter update successfully!',})
            else:
                return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status':False,'Exception': str(e)}, safe=False)

    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)


@csrf_exempt
def chapter_delete(request, chid):
    result = authorized(request)
    if result['status'] == True:
        try:
            chapterDetail = Chapter.objects.get(id=chid)
        except Chapter.DoesNotExist:
            return JsonResponse({'status':False,'message': 'The chapter does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            chapterDetail.delete()
            return JsonResponse({'status':True,'message': 'Chapter deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)


@csrf_exempt
def chapter_changeStatus(request, chid):
    result = authorized(request)
    if result['status'] == True:
        try:
            chapterDetail = Chapter.objects.get(id=chid)
        except Chapter.DoesNotExist:
            return JsonResponse({'message': 'The Chapter does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            chapter = Chapter.objects.filter(id=chid).update(status = 2)
            chapters = Chapter.objects.get(id=chid)
            chapter_serializer = ChapterSerializer(chapters)
            return JsonResponse({'status':True,'message': 'Course status changed successfully!','data':chapter_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

@csrf_exempt
def get_chapter_status(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == "POST":
                user = User.objects.get(id=request.POST.get('user_id'))
                chapter = Chapter.objects.get(id=request.POST.get('chapter_id'))
                chapter_status = ChapterStatus.objects.get(name=chapter,user=user)
                chapter_status_serializer = ChapterStatusSerializer(chapter_status,)
                # chapter_status_serializer.is_valid()
                return JsonResponse({'status':True,'data':chapter_status_serializer.data})
        except Exception as e:
            return JsonResponse({'status':False,'Exception':str(e)})
    return JsonResponse({'status':False,'message':'Unauthorised User!!'})


@csrf_exempt
def send_email(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            email = request.POST.get('email')
            email_from = "noreply@i4dev.in"
            # users = User.objects.all().filter(~Q(id=1),~Q(user_role=2))
            # for user in users:
            #     recipient_list = {user.email}
            send_mail( subject, message, email_from,[email],fail_silently=False )
            return JsonResponse({'status':True,'message': 'Email Sent successfully!','data':""},)
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

# @csrf_exempt
# def forgot_password(request):
#     result = authorized(request)
#     if result['status'] == True:
#         if request.method == 'POST':
#             email = request.POST.get('email')
#             try:
#                 users = User.objects.get(email = email)
#                 otp = random.randint(1111,9999)
#                 subject = "Reset Password OTP"
#                 message = "You are receiving this mail because we got forgot password request. Please use bellow given otp to reset your password. OTP is:- "+str(otp)
#                 email_from = "noreply@i4dev.in"
#                 recipient_list = {email}
#                 send_mail(subject, message, email_from, recipient_list)
#                 # users_serializer = UserSerializer(users)
#                 return JsonResponse({'status':True,'message': 'Reset password otp has send on your email successfully!','data':"",'otp': otp}, status=status.HTTP_201_CREATED)
#             except User.DoesNotExist:
#                 return JsonResponse({'status':False,'message': "User does't exist"},)
#         else:
#             return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
#     else:
#         return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

@csrf_exempt
def forgot_password(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "POST":
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
            except:
                user = None
                return JsonResponse({'status': False, 'message': 'Email not found'})
            otp = random.randint(1111, 9999)
            gmail_user = 'amant.i4consulting@gmail.com'
            gmail_password = 'aman@@2021'

            sent_from = gmail_user
            to = email
            subject = 'OTP'
            body = 'Your otp is ' + str(otp) + ' .'

            email_text = """\
            From: %s
            To: %s
            Subject: %s

            %s
            """ % (sent_from, ", ".join(to), subject, body)

            try:
                smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                smtp_server.ehlo()
                smtp_server.login(gmail_user, gmail_password)
                smtp_server.sendmail(sent_from, to, email_text)
                smtp_server.close()
                print("Email sent successfully!")
            except Exception as ex:
                return JsonResponse({"Exception": str(ex), })
            return JsonResponse({'status': True, 'message': 'OTP sent to your email', 'otp': otp})
    return JsonResponse({'status': False, 'message': 'Unauthorised'})


@csrf_exempt
def reset_password(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            email = request.POST.get('email')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            try:
                users = User.objects.get(email = email)
                confirm_password = make_password(request.POST.get('confirm_password'))
                user = User.objects.filter(id=users.id).update(password = confirm_password)
                users = User.objects.get(id = users.id)
                users_serializer = UserSerializer(users)
                return JsonResponse({'status': True, 'message': 'Password changed successfully!', 'data': users_serializer.data}, status=status.HTTP_201_CREATED)
            except:
                return JsonResponse({'status':False,'message': "User does't exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

@csrf_exempt
def add_quiz(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                course_id = Course.objects.get(id=request.POST.get('course_id'))
                question = request.POST.get('question')
                marks = request.POST.get('marks')
                answer = request.POST.get('answer')
                option = request.POST.get('option')

                quizs = Quiz_question.objects.create(course = course_id ,marks = marks,question = question,question_status = 1,options=option)
                quizs_ans = Quiz_ques_answer.objects.create(question = quizs ,answer = answer,)
                return JsonResponse({'status':True,'message': 'Quiz added successfully!',},)
            else:
                return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status':False,'Exception':str(e)})
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

@csrf_exempt
def quiz_edit(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method == 'POST':
                id = request.POST.get('id')
                course_id = Course.objects.get(id=request.POST.get('course_id'))
                question = request.POST.get('question')
                marks = request.POST.get('marks')
                answer = request.POST.get('answer')
                option = request.POST.get('option')

                quizs = Quiz_question.objects.filter(id=id,course=course_id ,).update(marks = marks,question = question,question_status = 1,options=option)
                quizs_ans = Quiz_ques_answer.objects.filter(question=quizs).update(answer = answer,)
                return JsonResponse({'status':True,'message': 'Quiz updated successfully!',},)
            else:
                return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
        except Exception as e:
            return JsonResponse({'status':False,'Exception':str(e)})
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)


@csrf_exempt
def quiz_delete(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            pk = request.POST.get('id')
            try:
                users = Quiz_question.objects.get(id=pk)
                users.delete()
                return JsonResponse({ 'Status': True, 'message': 'Quiz deleted successfully!'})
            except:
                return JsonResponse({ 'Status': False, 'message': 'Id not found!'})
    return JsonResponse({"message": "Unauthorised User", })

def quiz_list(request,chid):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            course = Course.objects.get(id=chid)
            quiz = Quiz_question.objects.all().filter(course_id=course,question_status=1).order_by('-id')
            quiz_serializer = QuizQuestionSerializer(quiz, many=True)
            return JsonResponse({'status':True,'message': 'quiz listed successfully!','data':quiz_serializer.data}, safe=False)
        else:
            return JsonResponse({'status':False,'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

def all_quiz(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            quiz = Quiz_question.objects.all().filter(question_status=1).order_by('id').reverse()
            quiz_serializer = QuizQuestionSerializer(quiz, many=True)
            return JsonResponse({'status':True,'message': 'quiz listed successfully!','data':quiz_serializer.data}, safe=False)
        else:
            return JsonResponse({'status':False,'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)


def quiz_detail(request,quizid):
    result = authorized(request)
    if result['status'] == True:
        try:
            quizDetail = Quiz_question.objects.get(id=quizid,question_status=1)
        except Quiz_question.DoesNotExist:
            return JsonResponse({'status':False,'message': 'The quiz does not exist'})

        if request.method == 'GET':
            quiz_serializer = QuizQuestionSerializer(quizDetail)

            quiz_answer = Quiz_ques_answer.objects.all().filter(question_id=quizid,answer_status=1)
            quiz_answer_serializer = QuizQuesAnswerSerializer(quiz_answer, many=True)

            data ={'quiz_questions':quiz_serializer.data,'quiz_question_answer':quiz_answer_serializer.data}
            return JsonResponse({'status':True,'message': 'quiz details get successfully!','data':data})
        else:
            return JsonResponse({'status':False,'message': 'Only get method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)


import re
@csrf_exempt
def answer_check(request):
    result = authorized(request)
    if result['status'] == True:
        answer = request.POST.get('answers')
        t = type(answer)
        s = answer.strip('{}')
        lss = s.split(',')
        try:
            user = User.objects.get(id=request.POST.get('user_id'))
            course = Course.objects.get(id=request.POST.get('course_id'))
            answers = request.POST.get('answers').replace('\"','')
            s = answers.strip('{}')
            ls = s.split(',')
            marks = 0
            total = 0
            for i in ls:
                l = i.split(':')
                id = l[0].strip()
                answer = l[1].strip()
                question = Quiz_question.objects.get(id=int(id))
                check = Quiz_ques_answer.objects.filter(question=question).values('answer')
                check1=check[0]
                total_marks = Quiz_question.objects.filter(id=int(id)).values('marks')
                total_marks1 = total_marks[0]
                total += int(total_marks1['marks'])
                if check1['answer'] == answer:
                    m = Quiz_question.objects.filter(id=int(id)).values('marks')
                    mr = m[0]
                    mrk = int(mr['marks'])
                    marks += mrk

                else:
                    marks += 0
            if marks/total >= 0.5:
                result = True
            else:
                result = False
            score = Score.objects.filter(user=user,course_score=course).delete()
            score = Score.objects.update_or_create(user=user,course_score=course,score=marks,ispass=result)
            score = Score.objects.get(user=user,course_score=course)
            score_serializer = ScoreSerializer(score)
            return JsonResponse({'status':True,'data':score_serializer.data,'total_marks':total,})
        except Exception as e:
            return JsonResponse({'ststus':False,'Exception':str(e),"message":str(lss)})
        return JsonResponse({'status':True,'data':'CBZ'})
    return JsonResponse({'status':False,'message':'Unauthorised User'})


@csrf_exempt
def quiz_changeStatus(request,quizid):
    result = authorized(request)
    if result['status'] == True:
        try:
            quizDetail = Quiz_question.objects.get(id=quizid)
        except Quiz_question.DoesNotExist:
            return JsonResponse({'message': 'The Chapter does not exist'})

        if request.method == 'GET':
            quizquest = Quiz_question.objects.filter(id=quizid,question_status=1).update(question_status = 2)
            quizanswerquest = Quiz_ques_answer.objects.filter(question_id=quizid).update(answer_status = 2)

            quiz = Quiz_question.objects.get(id=quizid)
            quiz_serializer = QuizQuestionSerializer(quiz)

            return JsonResponse({'status':True,'message': 'Course status changed successfully!','data':quiz_serializer.data})
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

@csrf_exempt
def add_banner(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                title = request.POST.get('title')
                link = request.POST.get('link')
                image = request.FILES["image"]
                banner_serializer = BannerSerializer(data=request.POST)
                if banner_serializer.is_valid():
                    banner = Banner.objects.create(title=title,image=image,link=link)
                    return JsonResponse({'Status':True,'message': 'Banner Created Sucessfully!', 'data': banner_serializer.data})
            except:
                return JsonResponse({'Status':True,'message': 'Something went wrong!', })
        return JsonResponse(banner_serializer.errors)
    return JsonResponse({"Message":"Unauthorised User",})

def banner_list_client(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Banner.objects.all()
            banner_serializer = BannerSerializer(banner, many=True)
            return JsonResponse({'message': 'Banner listed successfully!', 'data': banner_serializer.data}, safe=False)
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def banner_edit(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                pk = request.POST.get('id')
                title = request.POST.get('title')
                link = request.POST.get('link')
                try:
                    image = request.FILES["image"]
                except:
                    image=None
                if image is not None:
                    banner_serializer = BannerSerializer(data=request.POST)
                    banner_serializer.is_valid()
                    banner = Banner.objects.filter(id=pk).update(title=title,link=link)
                    # users = Banner.objects.get(id=pk)
                    banner = Banner.objects.get(id=pk)
                    banner.image = image
                    banner.save()
                    return JsonResponse({'Status':True,'message': 'Banner update successfully!', 'data': banner_serializer.data}
                                       )
                else:
                    banner_serializer = BannerSerializer(data=request.POST)
                    banner_serializer.is_valid()
                    banner = Banner.objects.filter(id=pk).update(title=title,link=link)
                    return JsonResponse({'Status':True,'message': 'Banner update successfully!', 'data': banner_serializer.data}
                                   )
            except Exception as e:
                return JsonResponse({'Status':False,'Exception':str(e)})
        return JsonResponse({'Status':False})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def banner_delete(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            pk = request.POST.get('id')
            try:
                users = Banner.objects.get(id=pk)
                users.delete()
                return JsonResponse({ 'Status': True, 'message': 'Banner deleted successfully!'})
            except:
                return JsonResponse({ 'Status': False, 'message': 'Id not found!'})
    return JsonResponse({"message": "Unauthorised User", })

def banner_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Banner.objects.all().order_by('-id')
            banner_serializer = BannerSerializer(banner, many=True)
            return JsonResponse({'Status': True, 'message': 'Banner listed successfully!', 'data': banner_serializer.data}, safe=False)
        return JsonResponse({'Status': False, 'message': 'Something went wrong!',})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def add_event(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                title = request.POST.get('title')
                link = request.POST.get('link')
                image = request.FILES["image"]
                about = request.POST.get('about')
                banner = Upcomingevents.objects.create(title=title,image=image,link=link,about=about)
                return JsonResponse({'Status':True,'message': 'Event Created Sucessfully!',})
            except Exception as e:
                return JsonResponse({'Status':False,'Exceprion': str(e), })
        return JsonResponse({'Status': False, 'message': 'Something went wrong!',})
    return JsonResponse({"Message":"Unauthorised User",})

@csrf_exempt
def event_edit(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                pk = request.POST.get('id')
                title = request.POST.get('title')
                link = request.POST.get('link')
                about = request.POST.get('about')
                try:
                    image = request.FILES["image"]
                except:
                    image=None
                if image is not None:
                    banner = Upcomingevents.objects.filter(id=pk).update(title=title,link=link,about=about)
                    # users = Banner.objects.get(id=pk)
                    banner = Upcomingevents.objects.get(id=pk)
                    banner.image = image
                    banner.save()
                    return JsonResponse({'Status':True,'message': 'Event update successfully!',}
                                       )
                else:
                    banner = Upcomingevents.objects.filter(id=pk).update(title=title,link=link, about=about)
                    return JsonResponse({'Status':True,'message': 'Event update successfully!', }
                                   )
            except Exception as e:
                return JsonResponse({'Status':False,'Exception':str(e)})
        return JsonResponse({'Status':False})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def event_delete(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            pk = request.POST.get('id')
            try:
                users = Upcomingevents.objects.get(id=pk)
                users.delete()
                return JsonResponse({ 'Status': True, 'message': 'Event deleted successfully!'})
            except:
                return JsonResponse({ 'Status': False, 'message': 'Id not found!'})
    return JsonResponse({"message": "Unauthorised User", })

def event_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Upcomingevents.objects.all().order_by('-id')
            banner_serializer = EventSerializer(banner, many=True)
            return JsonResponse({'Status': True, 'message': 'Event listed successfully!', 'data': banner_serializer.data}, safe=False)
        return JsonResponse({'Status': False, 'message': 'Something went wrong!',})
    return JsonResponse({"message": "Unauthorised User", })

def event_list_client(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Upcomingevents.objects.all()
            banner_serializer = EventSerializer(banner, many=True)
            return JsonResponse({'message': 'Event listed successfully!', 'data': banner_serializer.data}, safe=False)
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def add_service(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                title = request.POST.get('title')
                link = request.POST.get('link')
                image = request.FILES["image"]
                banner = Services.objects.create(title=title,image=image,link=link)
                return JsonResponse({'Status':True,'message': 'Services Created Sucessfully!',})
            except Exception as e:
                return JsonResponse({'Status':False,'Exception': str(e), })
        return JsonResponse({'Status': False, 'message': 'Something went wrong!',})
    return JsonResponse({"Message":"Unauthorised User",})

def service_list_client(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Services.objects.all()
            banner_serializer = ServicesSerializer(banner, many=True)
            return JsonResponse({'message': 'Services listed successfully!', 'data': banner_serializer.data}, safe=False)
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def service_edit(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            try:
                pk = request.POST.get('id')
                title = request.POST.get('title')
                link = request.POST.get('link')
                try:
                    image = request.FILES["image"]
                except:
                    image=None
                if image is not None:
                    banner = Services.objects.filter(id=pk).update(title=title,link=link)
                    # users = Banner.objects.get(id=pk)
                    banner = Banner.objects.get(id=pk)
                    banner.image = image
                    banner.save()
                    return JsonResponse({'Status':True,'message': 'Services update successfully!',}
                                       )
                else:
                    banner = Services.objects.filter(id=pk).update(title=title,link=link)
                    return JsonResponse({'Status':True,'message': 'Services update successfully!',}
                                   )
            except Exception as e:
                return JsonResponse({'Status':False,'Exception':str(e)})
        return JsonResponse({'Status':False})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def service_delete(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            pk = request.POST.get('id')
            try:
                users = Services.objects.get(id=pk)
                users.delete()
                return JsonResponse({ 'Status': True, 'message': 'Services deleted successfully!'})
            except:
                return JsonResponse({ 'Status': False, 'message': 'Id not found!'})
    return JsonResponse({"message": "Unauthorised User", })

def service_list(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            banner = Services.objects.all().order_by('-id')
            banner_serializer = ServicesSerializer(banner, many=True)
            return JsonResponse({'Status': True, 'message': 'Services listed successfully!', 'data': banner_serializer.data}, safe=False)
        return JsonResponse({'Status': False, 'message': 'Something went wrong!',})
    return JsonResponse({"message": "Unauthorised User", })


@csrf_exempt
def buy_package(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'POST':
            user = User.objects.get(id=request.POST.get('user_id'))
            try:
                packge = Package.objects.get(id=request.POST.get('package_id'))
                package_alloted = PackageAlloted.objects.get(user=user,package_name=packge)
            except:
                package_alloted = None
            try:
                course =  Course.objects.get(id=request.POST.get('course_id'))
                course_alloted = CourseAlloted.objects.get(user=user,course_name=course)
            except:
                course_alloted = None
            if package_alloted is not None:
                return JsonResponse({'status':False,'response':'This package is already alloted to You'})
            if course_alloted is not None:
                return JsonResponse({'status':False,'response':'This course is already alloted to You'})
            amount = request.POST.get('amount')
            client = razorpay.Client(auth=("rzp_test_uyIMOvTtAIVnuN", "lj4ElrD7sKLSBczz2VqJnexz"))
            data = { "amount": int(amount)*100, "currency": "INR", "receipt": "order_rcptid_11" }
            payment = client.order.create(data=data)
        return JsonResponse({'status':True,'response':payment})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def add_certificate(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method ==  "POST":
            user = User.objects.get(id=request.POST.get("user_id"))
            course = Course.objects.get(id=request.POST.get("course_id"))
            try:
                certi = Certificate.objects.get(user=user,course_score=course)
            except:
                certi = None
            if certi == None:
                Certificate.objects.create(user=user,course_score=course)
                return JsonResponse({'status':True,})
            else:
                return JsonResponse({'status':True,})
        return JsonResponse({'Status': False, 'message': 'only post method is allowed',})
    return JsonResponse({"message": "Unauthorised User", })

@csrf_exempt
def query_form(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            if request.method ==  "POST":
                email = request.POST.get('email')
                subject = request.POST.get('subject')
                content = request.POST.get('content')
                Query.objects.create(email=email,subject=subject,content=content)
                return JsonResponse({'status':True,'message':'Query added'})
        except Exception as e:
            return JsonResponse({'status':False,"Exception": str(e), })
    return JsonResponse({"message": "Unauthorised User", })


def show_queries(request):
    result = authorized(request)
    if result['status'] == True:
        if request.method == "GET":
            query =  Query.objects.all().order_by('-id')
            queryserializer = QuerySerializer(query, many=True)
            return JsonResponse({'status':True,'data':queryserializer.data})
    return JsonResponse({"message": "Unauthorised User", })