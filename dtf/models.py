"""
Module containing all database definitions
"""
from django.db import models

# Create your models here.
class Project(models.Model):
    """
    Very simple project model

    Just stores the name of the project to be referenced in submitted test results
    """
    name = models.CharField(max_length=100, blank=False, unique=True)

    def get_nav_data(self, test_name, submission_id):
        nav_data = {
            "previous": {
                "exists": False
            },
            "next": {
                "exists": False
            },
            "most_recent": {
            }
        }
        
        same_project_tests = TestResult.objects.filter(
            name=test_name,
            submission__project__id=self.id
        ).order_by("id")

        # previous test
        previous_test = same_project_tests.filter(
            submission__id__lt=submission_id
        ).order_by("-id").first()
        
        if previous_test:
            nav_data["previous"]["exists"] = True
            nav_data["previous"]["id"] = previous_test.id

        # next test
        next_test = same_project_tests.filter(
            submission__id__gt=submission_id
        ).order_by("id").first()

        if next_test:
            nav_data["next"]["exists"] = True
            nav_data["next"]["id"] = next_test.id

        # most recent
        most_recent_test = same_project_tests.order_by("-submission__id").first()
        nav_data["most_recent"]["id"] = most_recent_test.id
        return nav_data

    def __str__(self):
        return f"{self.name} [id = {self.id}]"

    class Meta:
        app_label = 'dtf'

class Submission(models.Model):
    """
    Test results get grouped in submissions.

    Basically a submission is a run of a whole test suite. Every test and parameter of that suit gets assigned to this submission
    """
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    info = models.JSONField(null=False, default=dict)

    class Meta:
        app_label = 'dtf'

class TestResult(models.Model):
    """
    Model to store test results and metadata
    """
    name = models.CharField(max_length=100, blank=False, db_index=True)
    submission = models.ForeignKey(Submission, on_delete=models.SET_NULL, null=True, default=None, related_name="tests")
    first_submitted = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    results = models.JSONField(null=True)

    POSSIBLE_STATUS = [
        ("skip", "skip"),
        ("successful", "successful"),
        ("unstable", "unstable"),
        ("unknown", "unknown"),
        ("failed", "failed"),
        ("broken", "broken")
    ]

    status = models.CharField(choices=POSSIBLE_STATUS, default="unknown", max_length=20)

    status_order = {
        "skip":0,
        "successful": 10,
        "unstable": 20,
        "failed": 30,
        "unknown": 40,
        "broken": 50
    }

    def calculate_status(self):
        status = "successful"
        for result in self.results:
            if self.status_order[result['status']] > self.status_order[status]:
                status = result['status']
        self.status = status

    def save(self, *args, **kwargs):
        self.calculate_status()
        super(TestResult, self).save(*args, **kwargs)

    def get_next_not_successful_test_id(self):
        same_submission_tests = self.submission.tests.all()
        not_successful = same_submission_tests.filter(
            first_submitted__gt=self.first_submitted
        ).exclude(status = "successful").order_by("first_submitted").values("id").first()
        
        if not_successful:
            return not_successful["id"]
        return None

    def __str__(self):
        if self.submission:
            return f"{self.name} [{self.submission.pk}]"
        return f"{self.name} [None]"

    class Meta:
        app_label = 'dtf'

class TestReference(models.Model):
    """
    Model to store references to every test

    The project is a foreign key
    The test_name is not, since the references can be from different test result \
        objects. The test name will be the same though. The test_name must not be UNIQUE constraint though, in order to allow equally named tests from multiple projects to be saved
    """
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    test_name = models.CharField(max_length=100, blank=False)
    # maybe this should just have a testresult as a foreign key?
    references = models.JSONField(null=False, default=dict)

    def update_references(self, references, test_id):
        # should not be necessary anymore since we have a default value for the references field
        # if not self.references:
        #     self.references = dict
        #     return
        for k, v in references.items():
            self.references[k] = v
            self.references[k]['ref_id'] = test_id

    def get_reference_or_none(self, value_name):
        return self.references.get(value_name, None)

    def __str__(self):
        if self.project:
            return f"{self.test_name} [{self.project.name}]"
        return f"{self.test_name} [None]"

    class Meta:
        app_label = 'dtf'