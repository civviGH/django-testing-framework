from django.contrib import admin

from dtf.models import Project, ProjectSubmissionProperty, TestResult, ReferenceSet, TestReference, Submission, Webhook

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass

@admin.register(ProjectSubmissionProperty)
class ProjectSubmissionPropertyAdmin(admin.ModelAdmin):
    pass

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    pass

@admin.register(ReferenceSet)
class ReferenceSetAdmin(admin.ModelAdmin):
    pass

@admin.register(TestReference)
class TestReferenceAdmin(admin.ModelAdmin):
    pass

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    pass