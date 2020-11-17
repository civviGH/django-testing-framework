"""
Contains all serializers needed for the API to transition between the json representation
and the database model of data
"""

from rest_framework import serializers

from dtf.functions import reference_structure_is_valid
from dtf.functions import get_project_from_data

from dtf.models import Project, TestResult, TestReference, Submission
from dtf.functions import check_result_structure

from django.core.exceptions import ObjectDoesNotExist

class ProjectSerializer(serializers.Serializer):
    """
    Serializer for projects

    Requires are name
    Providing an Id is optional
    """
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100, required=True)

    def create(self, validated_data):
        return Project.objects.create(**validated_data)

class TestReferenceSerializer(serializers.Serializer):
    """
    Serializer for references
    """
    id = serializers.IntegerField(required=False)
    test_name = serializers.CharField(max_length=100, required=True)
    references = serializers.JSONField(required=True)

    # when updating a reference, we need to know the test id which was used to do so. If we set the field to required the serializer looks for a test_id field in the TestReference Model on Deserializsation, which is why we set it to False and manually check for a valid test_id in the validate method
    test_id = serializers.IntegerField(required=False)

    # these are not saved, but rather used to make sure they are existent and valid
    project_id = serializers.IntegerField(required=False)
    project_name = serializers.CharField(required=False)

    def validate(self, data):
        """
        The incoming reference data in json format is checked for valid form

        It should be a dictionary, where the parameter name is the key, and the value contains another dictionary with value and valuetype

        We also need a project_id or project_name to create the model
        """
        if not "test_id" in data:
            raise serializers.ValidationError(\
                "No test_id submitted. Need a valid test_id to properly set the reference")
        try:
            _ = TestResult.objects.get(id=data['test_id'])
        except TestResult.DoesNotExist:
            raise serializers.ValidationError(\
                "No test found with the given test_id. Need a valid test_id to properly set the reference")

        project = get_project_from_data(data)
        if not project:
            raise serializers.ValidationError(\
                "Could not get a corresponding project. Did you provide a project_id or a project_name?")
        data['project'] = project

        reference_data_errors = ["Format in 'references' is not valid:"]
        try:
            reference_data = data['references']
            if len(reference_data) == 0:
                reference_data_errors.append(f"the 'references' dictionary is empty")
                raise serializers.ValidationError()
            if not isinstance(reference_data, dict):
                reference_data_errors.append("'references' field is not a dict")
                raise serializers.ValidationError()

            for parameter_name, parameter_values in reference_data.items():
                if not reference_structure_is_valid(parameter_values):
                    reference_data_errors.append(f"field {parameter_name}  in references does not match reference format")
                    raise serializers.ValidationError()
        except:
            raise serializers.ValidationError(reference_data_errors)

        return data

    def create(self, validated_data):
        test_reference, _ = TestReference.objects.get_or_create(
            project=validated_data['project'],
            test_name=validated_data['test_name']
        )
        test_reference.update_references(
            validated_data['references'],
            validated_data['test_id'])
        test_reference.save()
        return test_reference

class TestResultSerializer(serializers.Serializer):
    """
    Serializer for tests results

    Requires a name
    Requires a submission id
    """
    name = serializers.CharField(required=True)
    results = serializers.JSONField(required=True)
    id = serializers.IntegerField(required=False)
    first_submitted = serializers.DateTimeField(required=False)
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

class SubmissionSerializer(serializers.Serializer):

    project_id = serializers.IntegerField(required=False)
    project_name = serializers.CharField(required=False)
    info = serializers.JSONField(required=False)

    def validate(self, data):
        project = get_project_from_data(data)
        if not project:
            raise serializers.ValidationError(\
                "Could not get a corresponding project. Did you provide a project_id or a project_name?")
        data['project'] = project
        return data
    
    def create(self, validated_data):
        obj = Submission.objects.create(project=validated_data['project'])
        return obj