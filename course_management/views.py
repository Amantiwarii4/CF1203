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
from course_management.models import Category, Course, Chapter, CourseAlloted, Quiz_question, Quiz_ques_answer, Package, PackageAlloted, CourseStatus, ChapterStatus, Score
from course_management.serializers import ChangePasswordSerializer, QuizQuestionSerializer, QuizQuesAnswerSerializer, \
    CourseAllotedSerializer, UserSerializer, MyTokenObtainPairSerializer, CourseSerializer, CategorySerializer, \
    ChapterSerializer, UsercourseSerializer, PackageSerializer, PackageallotedSerializer, ChapterStatusSerializer, ScoreSerializer
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
                course_id = Course.objects.get(id=request.POST.get('course_id'))
                user_id = User.objects.get(id=request.POST.get('user_id'))
                try:
                    course = CourseAlloted.objects.get(user=user_id,course_name=course_id)
                except:
                    course = None
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
                status = request.POST.get('status')
                completedVideoLenght = request.POST.get('completedVideoLenght')
                totalVideoLength = request.POST.get('totalVideoLength')
                ChapterStatus.objects.filter(name=chapter,user=user,).update(chapter_status=status,completedVideoLenght=completedVideoLenght,totalVideoLength=totalVideoLength)
                return JsonResponse({'status':True,'message':'status changed !!'})
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
                Package.objects.create(name=name,course=course,about=about,price=price,image=image)
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
                    Package.objects.filter(id=id).update(name=name,course=course,about=about,price=price,image=image)
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
                return JsonResponse({'status':True,'message':'Package alloted successfull',})
            except:
                package_alloted = None
            if package_alloted == None:
                PackageAlloted.objects.update_or_create(package_name=package,user=user)
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
                allot_courses = CourseAlloted.objects.filter(user=user).all()
                serializer = CourseAllotedSerializer(data=allot_courses,many=True)
                serializer.is_valid()
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
                    {'status': True, 'message': 'User logged in successfully!', 'data': users_serializer.data,
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
                category_id = request.POST.get('category_id')
                author = request.POST.get('author')
                about = request.POST.get('about')
                rating = request.POST.get('rating')
                total_hours = request.POST.get('total_hours')
                total_days = request.POST.get('total_days')
                selling_price = request.POST.get('selling_price')
                original_price = request.POST.get('original_price')
                course_level = request.POST.get('course_level')
                bestseller = request.POST.get('bestseller')
                link = request.POST.get('link')
                course_file = request.FILES["course_file"]
                category = Category.objects.get(id=category_id)
                course_serializer = CourseSerializer(data=request.POST)
                course_serializer.is_valid()
                course = Course.objects.create(course_title=course_title, author=author, category=category,
                                               about=about, rating=rating, status='1', total_hours=total_hours,
                                               total_days=total_days, selling_price=selling_price,
                                               original_price=original_price, course_level=course_level,
                                               bestseller=bestseller, course_file=course_file, link=link)
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

            chapter = Chapter.objects.all().filter(course_id=cid)
            chapter_serializer = ChapterSerializer(chapter, many=True)

            categoryDetail = Category.objects.get(id=courseDetail.category_id)
            category_serializer = CategorySerializer(categoryDetail)
            return JsonResponse(
                {'status': True, 'message': 'course details get successfully!', 'data': course_serializer.data,
                 'chapters': chapter_serializer.data, 'category_data': category_serializer.data},
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

        if request.method == 'POST':
            course_title = request.POST.get('course_title')
            category_id = request.POST.get('category_id')
            author = request.POST.get('author')
            about = request.POST.get('about')
            rating = request.POST.get('rating')
            total_hours = request.POST.get('total_hours')
            total_days = request.POST.get('total_days')
            selling_price = request.POST.get('selling_price')
            original_price = request.POST.get('original_price')
            course_level = request.POST.get('course_level')
            bestseller = request.POST.get('bestseller')
            try:
                course_file = request.FILES["course_file"]
            except:
                course_file = None
            category = Category.objects.get(id=category_id)
            course_serializer = CourseSerializer(data=request.POST)
            course_serializer.is_valid()
            if course_file is not None:
                courses = Course.objects.filter(id=cid).update(course_title=course_title, author=author,
                                                               category_id=category, about=about, rating=rating,
                                                               total_hours=total_hours, total_days=total_days,
                                                               selling_price=selling_price,
                                                               original_price=original_price, course_level=course_level,
                                                               bestseller=bestseller)
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
                                                               category_id=category, about=about, rating=rating,
                                                               total_hours=total_hours, total_days=total_days,
                                                               selling_price=selling_price,
                                                               original_price=original_price, course_level=course_level,
                                                               bestseller=bestseller)
                # course = Course.objects.get(id=cid)
                # course.course_file = course_file
                # course.save()
                course = Course.objects.get(id=cid)
                course_serializer = CourseSerializer(course)
                return JsonResponse(
                    {'status': True, 'message': 'Course update successfully!', 'data': course_serializer.data},
                )
        else:
            return JsonResponse({'status': False, 'message': 'Only post method is allowed'}, safe=False)
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
            email_from = "noreply@i4dev.in"
            users = User.objects.all().filter(~Q(id=1),~Q(user_role=2))
            for user in users:
                recipient_list = {user.email}
                send_mail( subject, message, email_from, recipient_list )
            return JsonResponse({'status':True,'message': 'Email Sent successfully!','data':""}, status=status.HTTP_201_CREATED)
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
        if request.method == 'POST':
            chapter_id = Chapter.objects.get(id=request.POST.get('chapter_id'))
            question = request.POST.get('question')
            marks = request.POST.get('marks')
            answer = request.POST.get('answer')
            option = request.POST.get('option')

            quiz_serializer = QuizQuestionSerializer(data=request.POST)
            quiz_serializer.is_valid()
            quizs = Quiz_question.objects.create(chapter = chapter_id ,marks = marks,question = question,question_status = 1,options=option)
            quizs_ans = Quiz_ques_answer.objects.create(question = quizs ,answer = answer,)

            # chapters = Quiz_question.objects.get(id=id)
            # quiz_serializer = QuizQuestionSerializer(chapters)
            return JsonResponse({'status':True,'message': 'Quiz added successfully!'},)
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

def quiz_list(request,chid):
    result = authorized(request)
    if result['status'] == True:
        if request.method == 'GET':
            chapter = Chapter.objects.get(id=chid)
            quiz = Quiz_question.objects.all().filter(chapter_id=chapter,question_status=1).order_by('-id')
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


@csrf_exempt
def quiz_delete(request,quizid):
    result = authorized(request)
    if result['status'] == True:
        try:
            quizDetail = Quiz_question.objects.get(id=quizid)
        except Quiz_question.DoesNotExist:
            return JsonResponse({'status':False,'message': 'The quiz does not exist'})

        if request.method == 'DELETE':
            quizDetail.delete()
            Quiz_ques_answer.objects.all().filter(question_id=quizid).delete()

            return JsonResponse({'status':True,'message': 'Quiz deleted successfully!'})
        else:
            return JsonResponse({'status':False,'message': 'Only post method is allowed'}, safe=False)
    else:
        return JsonResponse({'status':result['status'],'message': result['message']}, safe=False)

import re
@csrf_exempt
def answer_check(request):
    result = authorized(request)
    if result['status'] == True:
        try:
            user = User.objects.get(id=request.POST.get('user_id'))
            chapter = Chapter.objects.get(id=request.POST.get('chapter_id'))
            answers = request.POST.get('answers').replace('\"','')
            s = answers.strip('{}')
            ls = s.split(',')
            marks = 0

            for i in ls:
                l = i.split(':')
                id = l[0].strip()
                answer = l[1].strip()
                question = Quiz_question.objects.get(id=int(id))
                check = Quiz_ques_answer.objects.filter(question=question).values('answer')
                check1=check[0]
                if check1['answer'] == answer:
                    m = Quiz_question.objects.filter(id=int(id)).values('marks')
                    mr = m[0]
                    mrk = int(mr['marks'])
                    marks += mrk

                else:
                    marks += 0

            score = Score.objects.update_or_create(user=user,chapter_score=chapter,score=marks)
            score_serializer = ScoreSerializer(score,many=True)
            return JsonResponse({'status':True,'data':score_serializer.data,})
        except Exception as e:
            return JsonResponse({'ststus':False,'Exception':str(e)})
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