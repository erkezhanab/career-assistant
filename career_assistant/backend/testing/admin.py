from django.contrib import admin
from .models import TestCategory, TestQuestion, UserCertificate, TestSession


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'question_type', 'question_text_short', 'difficulty', 'is_active')
    list_filter = ('category', 'question_type', 'difficulty', 'is_active')
    search_fields = ('question_text', 'explanation')
    
    def question_text_short(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    question_text_short.short_description = 'Вопрос'


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'issuer', 'issue_date', 'is_verified')
    list_filter = ('is_verified', 'issue_date')
    search_fields = ('user__email', 'title', 'issuer')


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'status', 'score', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('user__email',)