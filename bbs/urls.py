from django.urls import path
from . import views

app_name    = "bbs"
urlpatterns = [ 
    path("", views.index, name="index"),
    path("otp/", views.otp, name="otp"),
    path("verify_otp/", views.verify_otp, name="verify_otp"),
]


