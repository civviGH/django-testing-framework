"""
Contains all serializers needed for the API to transition between the json representation
and the database model of data
"""

import collections

from rest_framework import serializers

from dtf.functions import reference_structure_is_valid
from dtf.functions import get_project_from_data

from dtf.models import Project, TestResult, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook, WebhookLogEntry
from dtf.functions import check_result_structure

from django.core.exceptions import ObjectDoesNotExist

def _validate_project_reference(data):
    project = get_project_from_data(data)
    if not project:
        raise serializers.ValidationError(
            "Could not get a corresponding project. Did you provide a project_id, project_slug or a unique project_name?")

    data['project'] = project

    if 'project_id' in data: del data['project_id']
    if 'project_slug' in data: del data['project_slug']
    if 'project_name' in data: del data['project_name']

    return project

class ProjectSerializer(serializers.Serializer):
    """
    Serializer for projects

    Requires are name
    Providing an Id is optional
    """
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100, required=True)
    slug = serializers.SlugField(max_length=40, required=True)

    created = serializers.DateTimeField(required=False)
    last_updated = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        return Project.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.slug = validated_data.get('slug', instance.slug)
        instance.save()
        return instance

class ProjectSubmissionPropertySerializer(serializers.Serializer):

    project_id = serializers.IntegerField(required=False)
    project_slug = serializers.SlugField(required=False)
    project_name = serializers.CharField(required=False)

    id = serializers.IntegerField(required=False)

    name = serializers.CharField(max_length=100, required=True)
    required = serializers.BooleanField(default=False)
    display = serializers.BooleanField(default=True)
    display_replace = serializers.CharField(max_length=100, required=False, allow_blank=True)
    display_as_link = serializers.BooleanField(default=False)
    influence_reference = serializers.BooleanField(default=False)

    def validate(self, data):
        _validate_project_reference(data)
        return data

    def create(self, validated_data):
        obj = ProjectSubmissionProperty.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.required = validated_data.get('required', instance.required)
        instance.display = validated_data.get('display', instance.display)
        instance.display_replace = validated_data.get('display_replace', instance.display_replace)
        instance.display_as_link = validated_data.get('display_as_link', instance.display_as_link)
        instance.influence_reference = validated_data.get('influence_reference', instance.influence_reference)
        instance.save()
        return instance

class WebhookSerializer(serializers.Serializer):

    project_id = serializers.IntegerField(required=False)
    project_slug = serializers.SlugField(required=False)
    project_name = serializers.CharField(required=False)

    id = serializers.IntegerField(required=False)

    name = serializers.CharField(max_length=100, required=True)
    url = serializers.URLField(required=True)
    secret_token = serializers.CharField(max_length=200, required=True)

    on_submission     = serializers.BooleanField(default=True)
    on_test_result    = serializers.BooleanField(default=True)
    on_reference_set  = serializers.BooleanField(default=True)
    on_test_reference = serializers.BooleanField(default=True)

    def validate(self, data):
        _validate_project_reference(data)
        return data

    def create(self, validated_data):
        obj = Webhook.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.url = validated_data.get('url', instance.url)
        instance.secret_token = validated_data.get('secret_token', instance.secret_token)

        instance.on_submission = validated_data.get('on_submission', instance.on_submission)
        instance.on_test_result = validated_data.get('on_test_result', instance.on_test_result)
        instance.on_reference_set = validated_data.get('on_reference_set', instance.on_reference_set)
        instance.on_test_reference = validated_data.get('on_test_reference', instance.on_test_reference)
        instance.save()
        return instance

class ReferenceSetSerializer(serializers.Serializer):

    project_id = serializers.IntegerField(required=False)
    project_slug = serializers.SlugField(required=False)
    project_name = serializers.CharField(required=False)

    id = serializers.IntegerField(required=False)

    created = serializers.DateTimeField(required=False)
    last_updated = serializers.DateTimeField(required=False)

    property_values = serializers.JSONField(required=True)

    def validate(self, data):
        _validate_project_reference(data)
        return data

    def create(self, validated_data):
        obj = ReferenceSet.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data):
        instance.property_values = validated_data.get('property_values', instance.property_values)
        instance.save()
        return instance

class TestReferenceSerializer(serializers.Serializer):
    """
    Serializer for references
    """
    id = serializers.IntegerField(required=False)
    test_name = serializers.CharField(max_length=100, required=True)

    created = serializers.DateTimeField(required=False)
    last_updated = serializers.DateTimeField(required=False)

    references = serializers.JSONField(required=True)

    # when updating a reference, we need to know the test id which was used to do so. If we set the field to required the serializer looks for a test_id field in the TestReference Model on Deserializsation, which is why we set it to False and manually check for a valid test_id in the validate method
    test_id = serializers.IntegerField(required=False)

    # these are not saved, but rather used to make sure they are existent and valid
    reference_set_id = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        The incoming reference data in json format is checked for valid form

        It should be a dictionary, where the parameter name is the key, and the value contains another dictionary with value and valuetype

        We also need a reference_set_id to create the model
        """
        if "test_id" in data:
            try:
                _ = TestResult.objects.get(id=data['test_id'])
            except TestResult.DoesNotExist:
                raise serializers.ValidationError(\
                    "No test found with the given test_id. Need a valid test_id to properly set the reference")
            default_ref_id = data['test_id']
            del data['test_id']
        else:
            default_ref_id = None

        if not 'reference_set' in data:
            try:
                reference_set = ReferenceSet.objects.get(id=data['reference_set_id'])
            except ReferenceSet.DoesNotExist:
                raise serializers.ValidationError(\
                    "Could not get a corresponding reference set. Did you provide a reference_set_id?")
            data['reference_set'] = reference_set

        reference_data_errors = ["Format in 'references' is not valid:"]
        try:
            reference_data = data['references']
            if not isinstance(reference_data, dict):
                reference_data_errors.append("'references' field is not a dict")
                raise serializers.ValidationError()

            for parameter_name, parameter_values in reference_data.items():
                if not reference_structure_is_valid(parameter_values):
                    reference_data_errors.append(f"field {parameter_name}  in references does not match reference format")
                    raise serializers.ValidationError()
                if not 'ref_id' in parameter_values:
                    if default_ref_id is None:
                        raise serializers.ValidationError(\
                            "No test found with the given test_id. Need a valid test_id to properly set the reference")
                    parameter_values['ref_id'] = default_ref_id
        except:
            raise serializers.ValidationError(reference_data_errors)

        return data

    def create(self, validated_data):
        return TestReference.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.test_name = validated_data.get('test_name', instance.test_name)
        instance.references = validated_data.get('references', instance.references)
        instance.save()
        return instance

class TestResultSerializer(serializers.Serializer):
    """
    Serializer for tests results

    Requires a name
    Requires a submission id
    """
    name = serializers.CharField(required=True)
    results = serializers.JSONField(required=True)
    id = serializers.IntegerField(required=False)

    created = serializers.DateTimeField(required=False)
    last_updated = serializers.DateTimeField(required=False)

    submission_id = serializers.IntegerField(required=True)
    # submission = serializers.PrimaryKeyRelatedField(required=True)
    # TODO 
    # learn how to require a pk at this point to represent the submission

    # https://www.django-rest-framework.org/api-guide/serializers/#object-level-validation
    def validate(self, data):
        """
        Look for the 'results' field that contains the relevant test results

        The 'results' field must contain a list of dictionaries, where each dictionary \
            has a name, value, and valuetype field
        """
        try:
            submission = Submission.objects.get(pk=data['submission_id'])
        except ObjectDoesNotExist as error:
            raise serializers.ValidationError(error)
        data['submission'] = submission

        data['results'], errors = check_result_structure(
            data['results'],
            data['name'],
            submission)
        if not data['results']:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        obj = TestResult.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.results = validated_data.get('results', instance.results)
        instance.save()
        return instance

class SubmissionSerializer(serializers.Serializer):

    project_id = serializers.IntegerField(required=False)
    project_slug = serializers.SlugField(required=False)
    project_name = serializers.CharField(required=False)

    id = serializers.IntegerField(required=False)

    created = serializers.DateTimeField(required=False)
    last_updated = serializers.DateTimeField(required=False)

    info = serializers.JSONField(required=False)

    def validate(self, data):
        project = _validate_project_reference(data)

        info = data.get('info', None)
        project_properties = ProjectSubmissionProperty.objects.filter(project=project, required=True)
        missing_property_names = []
        for prop in project_properties:
            if not info or not prop.name in info:
                missing_property_names.append(prop.name)

        if len(missing_property_names) > 0:
            missing_properties_str = ', '.join(missing_property_names)
            raise serializers.ValidationError(f"Missing required properties '{missing_properties_str}' in submission info")

        return data

    def create(self, validated_data):
        obj = Submission.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data):
        instance.info = validated_data.get('info', instance.info)
        instance.save()
        return instance

class WebhookLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookLogEntry
        fields = ['webhook',
            'created',
            'request_url', 'request_data', 'request_headers',
            'response_status', 'response_data', 'response_headers']
