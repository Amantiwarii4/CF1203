from django.conf.urls import url
from django.urls import path
from course_management import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    url(r'authcheck',views.authorized),
    # url(r'^api/users/all_delete$', views.all_user_delete),
    url(r'dashboard$', views.admin_dashboard),
    url(r'allot/course$', views.allot_course),
    url(r'course/allot/completed/(?P<allotid>[0-9]+)$', views.courseAllot_completed),
    url(r'course/allot/list$', views.courseAllot_list),
    url(r'send_email$', views.send_email),

    #user auth functionality
    url(r'user/login$', views.user_login),
    url(r'check_token$', views.check_token),
    url(r'change/password$', views.change_password),
    url(r'forgot/password$', views.forgot_password),
    url(r'reset/password$', views.reset_password),

    #user apis
    url(r'user/add$', views.add_user),
    url(r'users$', views.user_list),
    url(r'users/detail/(?P<uid>[0-9]+)$', views.user_detail),
    url(r'users/edit$', views.user_edit),
    url(r'user/delete/(?P<uid>[0-9]+)$', views.user_delete),
    url(r'user/change/status/(?P<uid>[0-9]+)$', views.user_changeStatus),


    #caregories apis
    url(r'category/add$', views.add_category),
    url(r'category/list$', views.category_list),
    url(r'category/detail/(?P<catid>[0-9]+)$', views.category_detail), #category id
    url(r'category/edit$', views.category_edit), #category id
    url(r'category/delete/(?P<catid>[0-9]+)$', views.category_delete), #category id
    url(r'category/change/status/(?P<catid>[0-9]+)$', views.category_changeStatus), #category id


    #course apis
    url(r'course/add$', views.add_course),
    url(r'course/list/(?P<catid>[0-9]+)$', views.course_list), #category id
    url(r'course$', views.all_course),
    url(r'course/detail/(?P<cid>[0-9]+)$', views.course_detail), #course id
    url(r'course/edit$', views.course_edit), #course id
    url(r'course/delete/(?P<cid>[0-9]+)$', views.course_delete), #course id
    url(r'course/change/status/(?P<cid>[0-9]+)$', views.course_changeStatus), #course id
    path('change_course_status/', views.change_course_status, name="Change Status of Course"),

    # #course chapter apis
    url(r'chapter/add$', views.add_chapter),
    url(r'chapter/list/(?P<course_id>[0-9]+)$', views.chapter_list), #course id
    url(r'chapter$', views.all_chapter),
    url(r'chapter/detail/(?P<chid>[0-9]+)$', views.chapter_detail), #chapter id
    url(r'chapter/edit$', views.chapter_edit), #chapter id
    url(r'chapter/delete/(?P<chid>[0-9]+)$', views.chapter_delete), #chapter id
    url(r'chapter/change/status/(?P<chid>[0-9]+)$', views.chapter_changeStatus), #chapter id
    path('change_chapter_status/', views.change_chapter_status, name="Change Status of Chapter"),
    path('get_chapter_status/', views.get_chapter_status, name="Get Status of Chapter"),

    # #quiz on bases of chapter apis
    url(r'quiz/add$', views.add_quiz),
    url(r'quiz/list/(?P<chid>[0-9]+)$', views.quiz_list), #course id
    url(r'quiz$', views.all_quiz),
    url(r'quiz/detail/(?P<quizid>[0-9]+)$', views.quiz_detail), #chapter id
    url(r'quiz/delete/(?P<quizid>[0-9]+)$', views.quiz_delete), #chapter id
    url(r'quiz/change/status/(?P<quizid>[0-9]+)$', views.quiz_changeStatus), #chapter id
    # url(r'quiz/edit/(?P<quizid>[0-9]+)$', views.quiz_edit), #chapter id
    path('answer_check/', views.answer_check, name="answer_check"),

    # Package apis
    path('add_package/', views.add_package, name="Add Package"),
    path('edit_package/', views.edit_package, name="Edit Package"),
    path('show_package/', views.show_package, name="Show Package"),
    path('delete_package/', views.delete_package, name="Delete Package"),
    path('allot_package/', views.allot_package, name="Allot Package"),
    path('show_allotpackage/', views.show_allotpackage, name="Show Allot Package"),
    path('show_client_package/<int:user_id>/', views.show_client_package, name="show_client_package"),
]

urlpatterns = format_suffix_patterns(urlpatterns)