from dtf.models import Project, TestReference

def result_structure_is_valid(test_result_data):
    """
    Check if the test result structure is valid. Takes a test result as input.

    'name', 'value' and 'valuetype' fields are needed in the test result.
    If no 'reference' is supplied, the current reference for this test is used. If it does not exist, the 'reference' is None. The current reference will not be set automatically.
    If no 'margin' is supplied, the default margin of the 'valuetype' is used.
    """
    needed_fields = ['name', 'value', 'valuetype']
    for field in needed_fields:
        if field not in test_result_data:
            return False
    return True

def get_default_margin(valuetype):
    if valuetype == 'integer':
        return 0
    return None

def check_result_structure(results, test_name, submission):
    errors = ["Format in 'results' is not valid:"]
    if not isinstance(results, list):
        errors.append("'results' field is not a list")
        return None, errors

    current_reference, _ = TestReference.objects.get_or_create(
            project=submission.project,
            test_name=test_name
        )
    
    for r in results:
        if not result_structure_is_valid(r):
            errors.append(f"field {r} does not match wanted format")
        if not 'reference' in r:
            r['reference'] = current_reference.get_reference_or_none(r['name'])
        if not 'margin' in r:
            r['margin'] = get_default_margin(r['valuetype'])
        r['status'] = check_status_of_test_parameter(r.get('status'))
    return results, errors

def check_status_of_test_parameter(status):
    if not status:
        return 'unknown'
    if status not in ['successful',
                      'unstable',
                      'failed',
                      'broken',
                      'unknown',
                      'skip']:
        return 'unknown'
    return status

def reference_structure_is_valid(reference_data):
    if "value" not in reference_data.keys():
        return False
    return True

def create_view_data_from_test_references(result, reference):
    data = []
    for parameter in result:
        p_name = parameter['name']
        ref = reference.get(p_name)
        data.append(
            {
                'name':p_name,
                'test':parameter['value'],
                'reference_on_submission':parameter['reference'],
                'reference':ref['value'] if ref else None,
                'status':parameter['status'],
                'ref_id':ref['ref_id'] if ref else None,
                'valuetype':parameter['valuetype']
            }
        )
    return data

def get_project_by_id(project_id):
    """
    Retrieve a project by its Id. Returns None if no project is found.
    """
    try:
        return Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return None

def get_project_by_name(project_name):
    """
    Retrieve a project by its name. Returns None if no project is found or multiple projects with the same name exist.
    """
    try:
        return Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        return None
    except Project.MultipleObjectsReturned:
        return None

def get_project_by_slug(project_slug):
    """
    Retrieve a project by its slug. Returns None if no project is found.
    """
    try:
        return Project.objects.get(slug=project_slug)
    except Project.DoesNotExist:
        return None

def get_project_by_id_or_slug(id):
    """
    Retrieve a project by its ID or slug. Returns None if no project is found.
    """
    if id.isdigit():
        project = get_project_by_id(int(id))
    else:
        project = None

    if project is None:
        project = get_project_by_slug(id)

    return project

def get_project_from_data(data):
    """
    Get a project from json data posted to the API
    """
    if 'project_id' in data:
        return get_project_by_id(data['project_id'])
    if 'project_slug' in data:
        return get_project_by_slug(data['project_slug'])
    if 'project_name' in data:
        return get_project_by_name(data['project_name'])
    return None