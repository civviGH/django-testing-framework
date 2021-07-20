"""
Module containing all database definitions
"""
import collections
import json

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from dtf.validators import JSONSchemaValidator

class Membership(models.Model):
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
    )

    project = models.ForeignKey(
        "Project",
        null=False,
        blank=False,
        related_name="memberships",
        on_delete=models.CASCADE,
    )

    AVAILABLE_ROLES = [
        ("owner", "Owner"),
        ("developer", "Developer"),
        ("guest", "Guest")
    ]
    role = models.CharField(choices=AVAILABLE_ROLES, default="guest", max_length=20)

    required_project_membership_role = {
        'view'   : 'guest',
        'add'    : 'owner',
        'change' : 'owner',
        'delete' : 'owner'
    }

    class Meta:
        unique_together = ("user", "project")

class Project(models.Model):
    """
    Very simple project model

    Just stores the name of the project to be referenced in submitted test results
    """
    name = models.CharField(max_length=100, blank=False)
    slug = models.SlugField(max_length=40, blank=False, unique=True)

    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    members = models.ManyToManyField(User, related_name="projects", through=Membership, through_fields=("project", "user"))

    required_project_membership_role = {
        'view'   : 'guest',
        'change' : 'owner',
        'delete' : 'owner'
    }

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

class ProjectSubmissionProperty(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, related_name="properties")

    name = models.CharField(max_length=100, blank=False)
    required = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    display_replace = models.CharField(max_length=100, blank=True)
    display_as_link = models.BooleanField(default=False)
    influence_reference = models.BooleanField(default=False)

    required_project_membership_role = {
        'view'   : 'developer',
        'add'    : 'owner',
        'change' : 'owner',
        'delete' : 'owner'
    }

    class Meta:
        app_label = 'dtf'
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'name'], 
                name='unique_submission_property'
            )
        ]

class Submission(models.Model):
    """
    Test results get grouped in submissions.

    Basically a submission is a run of a whole test suite. Every test and parameter of that suit gets assigned to this submission
    """
    _info_json_schema = {
        'schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        "additionalProperties": { "type": "string" }
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, related_name="submissions")
    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    info = models.JSONField(null=False, default=dict, validators=[JSONSchemaValidator(schema=_info_json_schema)])

    required_project_membership_role = {
        'view'   : 'guest',
        'add'    : 'owner',
        'change' : 'owner',
        'delete' : 'owner'
    }

    def status(self):
        status = None
        for test in self.tests.all():
            test_status = test.status
            if status is None or TestResult.status_order[test_status] > TestResult.status_order[status]:
                status = test_status
        if status is None:
            return "unknown"
        return status

    class Meta:
        app_label = 'dtf'

class TestResult(models.Model):
    """
    Model to store test results and metadata
    """
    _value_json_schema = {
        '$id' : '#value',
        'type': 'object',
            'properties': {
                'data': {},
                'type': {
                    'type': 'string',
                    'enum': [
                        'integer',
                        'float',
                        'string',
                        'duration',
                        'ndarray',
                        'image'
                    ]
                },
            },
        'allOf': [
            {
                'if': {
                    'properties': {'type': {'const': 'integer'}}
                },
                'then': {
                    'properties': {'data': {'type': 'integer'}}
                }
            },
            {
                'if': {
                    'properties': {'type': {'const': 'float'}}
                },
                'then': {
                    'properties': {'data': {'type': 'number'}}
                }
            },
            {
                'if': {
                    'properties': {'type': {'const': 'string'}}
                },
                'then': {
                    'properties': {'data': {'type': 'string'}}
                }
            },
            {
                'if': {
                    'properties': {'type': {'const': 'duration'}}
                },
                'then': {
                    'properties': {
                        'data': {
                            'type': 'string',
                            # ISO 8601 duration
                            'pattern': R'^(?P<sign>[-+]?)P(?:(?P<days>\d+(\.\d+)?)D)?(?:T(?:(?P<hours>\d+(\.\d+)?)H)?(?:(?P<minutes>\d+(\.\d+)?)M)?(?:(?P<seconds>\d+(\.\d+)?)S)?)?$'
                        }
                    }
                }
            },
            {
                'if': {
                    'properties': {'type': {'const': 'ndarray'}}
                },
                'then': {
                    'properties': {'data': {
                        'type': 'object',
                        'properties': {
                            'shape': {
                                'type': 'array',
                                'items': {'type': 'integer'}
                            },
                            'entries': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/value'}
                            }
                        },
                        'required': ['shape', 'entries'],
                        'additionalProperties': False
                    }}
                }
            },
            {
                'if': {
                    'properties': {'type': {'const': 'image'}}
                },
                'then': {
                    'properties': {'data': {'type': 'string',
                                            'contentEncoding': 'base64',
                                            'contentMediaType': 'image/png'}}
                }
            },
        ],
        'required': ['data', 'type'],
        'additionalProperties': False
    }

    _results_json_schema = {
        'schema': 'http://json-schema.org/draft-07/schema#',
        'definitions': {
            'value': _value_json_schema
        },
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'name':  {
                    'type': 'string'
                },
                'value': {
                    'oneOf': [
                        {'$ref': '#/definitions/value'},
                        {'type': 'null'}
                    ]
                },
                'reference': {
                    'oneOf': [
                        {'$ref': '#/definitions/value'},
                        {'type': 'null'}
                    ]
                },
                'reference_source': {'type': 'integer'},
                'status': {
                    'type': 'string',
                    'enum': [
                        'skip',
                        'successful',
                        'unstable',
                        'unknown',
                        'failed',
                        'broken'
                    ],
                    'default': 'unknown'
                }
            },
            'additionalProperties': False,
            'required': ['name', 'value']
        }
    }

    name = models.CharField(max_length=100, blank=False, db_index=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=False, related_name="tests")
    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    results = models.JSONField(null=True, validators=[JSONSchemaValidator(schema=_results_json_schema)])

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
        "skip": 0,
        "successful": 1,
        "unknown": 2,
        "unstable": 3,
        "failed": 4,
        "broken": 5
    }

    required_project_membership_role = {
        'view'   : 'guest',
        'add'    : 'developer',
        'change' : 'developer',
        'delete' : 'owner'
    }

    def calculate_status(self):
        status = None
        for result in self.results:
            if status is None or self.status_order[result['status']] > self.status_order[status]:
                status = result['status']
        if status is None:
            self.status = "unknown"
        else:
            self.status = status

    def save(self, *args, **kwargs):
        self.calculate_status()
        super(TestResult, self).save(*args, **kwargs)

    def get_next_not_successful_test_id(self):
        same_submission_tests = self.submission.tests.all()
        not_successful = same_submission_tests.filter(
            created__gt=self.created
        ).exclude(status = "successful").order_by("created").values("id").first()
        
        if not_successful:
            return not_successful["id"]
        return None

    def __str__(self):
        if self.submission:
            return f"{self.name} [{self.submission.pk}]"
        return f"{self.name} [None]"

    class Meta:
        app_label = 'dtf'


class ReferenceSet(models.Model):

    _properties_json_schema = {
        'schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        "additionalProperties": { "type": "string" }
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, related_name="reference_sets")

    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    required_project_membership_role = {
        'view'   : 'guest',
        'add'    : 'developer',
        'change' : 'developer',
        'delete' : 'owner'
    }

    # We do use a special JSON decoder, that creates `OrderedDict` instead of `dict`
    # objects. This will allow us to sort the properties by their keys, so that the
    # ordering of entries does not mess with the `unique` database field constraint.
    class OrderedDictJSONDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            kwargs['object_pairs_hook']=collections.OrderedDict
            super().__init__(*args, **kwargs)
    property_values = models.JSONField(decoder=OrderedDictJSONDecoder, null=False, default=collections.OrderedDict, validators=[JSONSchemaValidator(schema=_properties_json_schema)])

    def save(self, *args, **kwargs):
        if not isinstance(self.property_values, collections.OrderedDict):
            self.property_values = collections.OrderedDict(sorted(self.property_values.items()))
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'dtf'

        constraints = [
            models.UniqueConstraint(
                fields=['project', 'property_values'], 
                name='unique_project_property_values'
            )
        ]

class TestReference(models.Model):
    """
    Model to store references to every test

    The project is a foreign key
    The test_name is not, since the references can be from different test result \
        objects. The test name will be the same though. The test_name must not be UNIQUE constraint though, in order to allow equally named tests from multiple projects to be saved
    """
    _references_json_schema = {
        'schema': 'http://json-schema.org/draft-07/schema#',
        'definitions': {
            'value': TestResult._value_json_schema
        },
        'type': 'object',
        'additionalProperties': {
            'type': 'object',
            'properties': {
                'value': {
                    'oneOf': [
                        {'$ref': '#/definitions/value'},
                        {'type': 'null'}
                    ]
                },
                'source': {'type': 'integer'},
            },
            'required': ['value'],
            'additionalProperties': False
        }
    }

    reference_set = models.ForeignKey(ReferenceSet, on_delete=models.CASCADE, null=False, related_name="test_references")
    test_name = models.CharField(max_length=100, blank=False)

    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    # maybe this should just have a testresult as a foreign key?
    references = models.JSONField(null=False, default=dict, validators=[JSONSchemaValidator(schema=_references_json_schema)])

    required_project_membership_role = {
        'view'   : 'guest',
        'add'    : 'developer',
        'change' : 'developer',
        'delete' : 'owner'
    }

    def update_references(self, new_references, default_source):
        for name, data in new_references.items():
            if data is not None:
                self.references[name] = {
                    'value': data['value'],
                    'source': default_source
                }
            elif name in self.references:
                del self.references[name]

    def get_reference_or_none(self, value_name):
        return self.references.get(value_name, None)

    def __str__(self):
        if self.reference_set:
            return f"{self.test_name} [{self.reference_set.project.name}]"
        return f"{self.test_name} [None]"

    class Meta:
        app_label = 'dtf'
        constraints = [
            models.UniqueConstraint(
                fields=['reference_set', 'test_name'], 
                name='unique_test_reference_property'
            )
        ]

class Webhook(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, related_name="webhooks")

    name = models.CharField(max_length=100, blank=False)
    url = models.URLField(null=False, blank=False)
    secret_token = models.CharField(max_length=200, null=False, blank=False)

    on_submission     = models.BooleanField(default=True)
    on_test_result    = models.BooleanField(default=True)
    on_reference_set  = models.BooleanField(default=True)
    on_test_reference = models.BooleanField(default=True)

    required_project_membership_role = {
        'view'   : 'developer',
        'add'    : 'owner',
        'change' : 'owner',
        'delete' : 'owner'
    }

    def most_recent_status(self):
        recent_log = WebhookLogEntry.objects.filter(webhook=self).order_by('-created').first()
        if recent_log is None:
            return None
        return recent_log.response_status

    class Meta:
        app_label = 'dtf'

class WebhookLogEntry(models.Model):
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, null=False, related_name="logs")

    created = models.DateTimeField(default=timezone.now, editable=False, blank=True)

    POSSIBLE_TRIGGERS = [
        (Submission.__name__, Submission.__name__),
        (TestResult.__name__, TestResult.__name__),
        (ReferenceSet.__name__, ReferenceSet.__name__),
        (TestReference.__name__, TestReference.__name__),
    ]

    trigger = models.CharField(choices=POSSIBLE_TRIGGERS, null=False, blank=False, max_length=20)

    request_url      = models.URLField(null=False, blank=False)
    request_data     = models.JSONField(null=False, blank=False)
    request_headers  = models.JSONField(null=False, blank=False)

    response_status  = models.IntegerField(null=False, blank=False)
    response_data    = models.TextField(null=False, blank=False)
    response_headers = models.JSONField(null=False, blank=False)

    required_project_membership_role = {
        'view'   : 'owner',
        'add'    : 'owner',
        'change' : 'owner',
        'delete' : 'owner'
    }

    class Meta:
        app_label = 'dtf'
