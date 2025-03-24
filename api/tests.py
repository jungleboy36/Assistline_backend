from django.core.mail import send_mail
from django.conf import settings

settings.configure()

send_mail(
    subject="Test Email",
    message="This is a test email from Django via OVH",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["achrafhafsia36@gmail.com"],
    fail_silently=False
)
