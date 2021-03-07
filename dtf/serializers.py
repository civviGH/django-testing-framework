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

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'slug', 'created', 'last_updated']
        extra_kwargs = {'created': {'read_only': False, 'required':False}}

class ProjectSubmissionPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSubmissionProperty
        fields = ['project',
                  'id',
                  'name',
                  'required',
                  'display',
                  'display_replace',
                  'display_as_link',
                  'influence_reference']

class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ['project',
                  'id',
                  'name',
                  'url',
                  'secret_token',
                  'on_submission',
                  'on_test_result',
                  'on_reference_set',
                  'on_test_reference']

class ReferenceSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceSet
        fields = ['project',
                  'id',
                  'created',
                  'last_updated',
                  'property_values']
        extra_kwargs = {'created': {'read_only': False, 'required':False}}

class TestReferenceSerializer(serializers.ModelSerializer):
    # NOTE: should probably rather be named something like "default_reference_test"
    test_id = serializers.PrimaryKeyRelatedField(queryset=TestResult.objects.all(), required=False)

    class Meta:
        model = TestReference
        fields = ['reference_set',
                  'test_name',
                  'test_id',
                  'id',
                  'created',
                  'last_updated',
                  'references']
        extra_kwargs = {'created': {'read_only': False, 'required':False}}

    def validate(self, data):
        if "test_id" in data:
            default_ref_id = data['test_id'].id
            del data['test_id']
        else:
            default_ref_id = None

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

class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['name',
                  'id',
                  'results',
                  'created',
                  'last_updated',
                  'submission']
        extra_kwargs = {'created': {'read_only': False, 'required':False}}

    def validate(self, data):
        data['results'], errors = check_result_structure(
            data['results'],
            data['name'],
            data['submission'])
        if not data['results']:
            raise serializers.ValidationError(errors)
        return data

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['project',
                  'id',
                  'created',
                  'last_updated',
                  'info']
        extra_kwargs = {'created': {'read_only': False, 'required':False}}

    def validate(self, data):
        info = data.get('info', None)
        project_properties = ProjectSubmissionProperty.objects.filter(project=data['project'], required=True)
        missing_property_names = []
        for prop in project_properties:
            if not info or not prop.name in info:
                missing_property_names.append(prop.name)

        if len(missing_property_names) > 0:
            missing_properties_str = ', '.join(missing_property_names)
            raise serializers.ValidationError(f"Missing required properties '{missing_properties_str}' in submission info")

        return data

class WebhookLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookLogEntry
        fields = ['webhook',
            'created',
            'request_url', 'request_data', 'request_headers',
            'response_status', 'response_data', 'response_headers']
