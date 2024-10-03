from django.shortcuts import render,redirect
from django.views import View

from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin


import django_otp
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.qr import write_qrcode_image


class IndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        if request.user.is_verified():
            print("OTP 検証済み")
        else:
            print("OTP 未検証")
            return redirect("bbs:verify_otp")

        return render(request, "bbs/index.html")

index   = IndexView.as_view()



class OtpView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "bbs/otp.html")

    def post(self, request, *args, **kwargs):

        # デバイスを追加する。
        device = TOTPDevice.objects.create(user=request.user, name='default', confirmed=False)

        # write_qrcode_image を使うことで、QRコードを生成できる。
        response = HttpResponse(content_type='image/svg+xml')
        write_qrcode_image(device.config_url, response)

        return response

otp   = OtpView.as_view()

# トークンを検証する。
class VerifyOtpView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        otp_device = TOTPDevice.objects.filter(user=request.user).first()
        
        if otp_device is None:
            print("otp デバイスなし")
            return redirect("bbs:otp")

        return render(request, "bbs/verify_otp.html")


    def post(self, request, *args, **kwargs):

        otp_device = TOTPDevice.objects.filter(user=request.user).first()
        
        if otp_device is None:
            # otpデバイスがないので、追加してもらう
            print("otp デバイスなし")
            return redirect("bbs:otp")

        # OTPのトークンを検証
        if otp_device.verify_token(request.POST.get('otp_token')):
            # 以後、request.user.is_verified() で判定できる。

            otp_device.confirmed = True
            otp_device.save()

            # OTPのログインをする
            django_otp.login(request, otp_device)


            # OTPが正しければ認証成功
            return redirect("bbs:index")  # 認証成功時のリダイレクト先


        # OTPが間違っていればエラーメッセージを表示
        print("otpが違います。")
        return redirect("bbs:verify_otp")

verify_otp = VerifyOtpView.as_view()


