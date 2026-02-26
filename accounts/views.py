from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import re

from django.utils import timezone
from .models import CustomUser, OTPLog
import random

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'accounts/signup.html')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        send_otp_email(user)
        request.session['signup_email'] = email
        messages.success(request, 'OTP sent to your email')
        return redirect('otp_verify')
    
    return render(request, 'accounts/signup.html')

def send_otp_email(user, subject="Verify Your Email - T-Shirt Store"):
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        OTPLog.objects.create(user=user, otp=otp)
        
        # Send email
        send_mail(
            'Verify Your Email - T-Shirt Store',
            f'Your OTP is: {otp}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

def resend_otp(request):
    email = request.GET.get('email') 
    if not email: 
        messages.error(request, "No email provided")
        return redirect('signup')
    user = CustomUser.objects.filter(email=email).first() 
    if not user:
        messages.error(request, "User not found")
        return redirect('signup')
    send_otp_email(user, subject="Resend OTP - T-Shirt Store")
    messages.success(request, "New OTP sent to your email")
    return redirect('otp_verify')

def otp_verify(request):
    email = request.session.get('signup_email')
    if not email:
        return redirect('signup')
    
    if request.method == 'POST':
        otp = request.POST['otp']
        user = get_object_or_404(CustomUser, email=email)
        
        if not user.otp_created_at:
            messages.error(request, "Invalid OTP request")
        elif (timezone.now() - user.otp_created_at).total_seconds() > 300:
            messages.error(request, 'OTP expired')
            return render(request, 'accounts/otp.html')
        
        if user.otp == otp:
            user.is_email_verified = True
            user.otp = ''
            user.save()
            del request.session['signup_email']
            messages.success(request, 'Email verified successfully')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP')
    
    return render(request, 'accounts/otp.html', {'email': email})

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        if user and user.is_email_verified:
            login(request, user)
            request.session['user_id'] = user.id
            messages.success(request, 'Logged in successfully')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials or email not verified')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('home')

def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login first')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
