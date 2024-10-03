from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse_lazy
from django.http import HttpResponseNotAllowed, HttpResponse

from django.contrib.auth.views import LoginView,LogoutView,PasswordChangeView,PasswordChangeDoneView,PasswordResetView,PasswordResetDoneView,PasswordResetConfirmView,PasswordResetCompleteView
from django.views.generic import CreateView
from django.views import View

from django.core.mail import send_mail

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.mixins import LoginRequiredMixin

from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import SignupForm


# DjangoのPasswordリセットトークンジェネレーターを流用し、メールアドレスの確認用トークンを作る。
class ActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.id}{timestamp}{user.is_active}"

activation_token = ActivationTokenGenerator()


class SignupView(CreateView):
    
    form_class      = SignupForm
    success_url     = reverse_lazy("login")
    template_name   = "registration/signup.html"

    # 認証済みの状態でリクエストした時、LOGIN_REDIRECT_URL へリダイレクトさせる
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)


    # ここで、アカウント作成時に、メール確認を行う。
    def form_valid(self, form):
        user = form.save()

        uid             = urlsafe_base64_encode(force_bytes(user.id))
        token           = activation_token.make_token(user)

        subject         = "メールの確認をしましょう。"
        message         = f"http://{ self.request.get_host() }{ reverse_lazy('activate', kwargs={'uidb64':uid, 'token':token} ) }"

        # TODO:ここでDjango側のメールアドレスを指定しておく。
        from_email      = "huga@gmail.com"
        recipient_list  = [ user.email ]

        send_mail(subject, message, from_email, recipient_list)

        return HttpResponse("メールへ確認用のURLを送りました。")

signup  = SignupView.as_view()


# メールの確認用URLをチェックするビュークラス
class ActivateView(View):

    def get(self, request, *args, **kwargs):
        try:
            uid     = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
            user    = get_user_model().objects.get(pk=uid)
        except:
            return HttpResponse("メールの確認用URLに問題があります。")

        if not activation_token.check_token(user, kwargs["token"]):
            return HttpResponse("メールの確認用URLに問題があります。")

        # メール確認完了(このフィールドを追加しておく。)
        user.email_verified = True
        user.save()

        return HttpResponse("メールの確認ありがとうございます。")

activate    = ActivateView.as_view()


# メールの確認用URLを再度生成するビュー(URLの含んだメールを紛失した時用)
class RegenerateTokenView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        
        uid             = urlsafe_base64_encode(force_bytes(request.user.id))
        token           = activation_token.make_token(request.user)

        subject         = "メールの確認をしましょう。"
        message         = f"http://{ self.request.get_host() }{ reverse_lazy('activate', kwargs={'uidb64':uid, 'token':token} ) }"

        # TODO:ここでDjango側のメールアドレスを指定しておく。
        from_email      = "huga@gmail.com"
        recipient_list  = [ request.user.email ]

        send_mail(subject, message, from_email, recipient_list)

        return HttpResponse("メールへ確認用のURLを送りました。")

regenerate_token    = RegenerateTokenView.as_view()


class CustomLoginView(LoginView):

    # 認証済みの状態でリクエストした時、LOGIN_REDIRECT_URL へリダイレクトさせる
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

login   = CustomLoginView.as_view()

# LogoutViewのGETメソッドを無効化する。(すでにDjango4.1で非推奨。5.0で削除される見通し)
# https://docs.djangoproject.com/ja/4.2/topics/auth/default/#django.contrib.auth.views.LogoutView
class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(permitted_methods=['POST'])

logout  = CustomLogoutView.as_view()


password_change             = PasswordChangeView.as_view()
password_change_done        = PasswordChangeDoneView.as_view()
password_reset              = PasswordResetView.as_view()
password_reset_done         = PasswordResetDoneView.as_view()
password_reset_confirm      = PasswordResetConfirmView.as_view()
password_reset_complete     = PasswordResetCompleteView.as_view()




