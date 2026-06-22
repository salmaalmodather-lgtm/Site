from django.db import models
from django.contrib.auth.models import User


class Teacher(models.Model):
    """ملف المعلم المرتبط بحساب اليوزر - كل يوزر له معلم واحد بس"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher")
    name = models.CharField(max_length=150, verbose_name="اسم المستر/المدرس")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    """عنصر محتوى واحد في الخطة (ميمز / ريل / كاروسيل ... الخ)"""

    TYPE_CHOICES = [
        ("meme", "🤡 ميمز"),
        ("reel", "🎬 ريل فيديو"),
        ("tiktok", "📱 تيك توك للمستر"),
        ("carousel", "📸 كاروسيل"),
        ("design", "🎨 ديزاين"),
        ("ai", "🤖 ذكاء اصطناعي"),
        ("interactive", "❓ تفاعل"),
    ]

    STATUS_CHOICES = [
        ("pending", "🎥 محتاج تصوير"),
        ("progress", "🎨 قيد العمل"),
        ("ready", "🟢 جاهز للنشر"),
    ]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="items")
    week = models.PositiveSmallIntegerField(default=1)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="meme")
    text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["week", "id"]

    def __str__(self):
        return f"[{self.week}] {self.text[:30]}"

    def to_dict(self):
        return {
            "id": self.id,
            "week": str(self.week),
            "type": self.type,
            "text": self.text,
            "status": self.status,
        }
