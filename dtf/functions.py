from dtf.models import Project, TestReference

def create_reference_query(project, query_params):
    queries = {}
    for prop in project.properties.all():
        if prop.influence_reference:
            prop_value = query_params.get(prop.name, None)
            if not prop_value is None:
                queries['property_values__' + prop.name] = prop_value
    return queries

def fill_result_default_values(results, test_name, submission):
    reference_query = create_reference_query(submission.project, submission.info)
    reference_set = submission.project.reference_sets.filter(**reference_query).first()

    if reference_set is not None:
        current_reference = reference_set.test_references.filter(test_name=test_name).first()
    else:
        current_reference = None

    for result in results:
        if not 'reference' in result:
            if current_reference is not None:
                result['reference'] = current_reference.get_reference_or_none(result['name'])
            else:
                result['reference'] = None
        if not 'status' in result:
            result['status'] = 'unknown'
    return results

def create_view_data_from_test_references(test_results, global_references):
    view_data = []
    for item in test_results:

        if 'value' in item and item['value'] is not None:
            test = {
                'value': item['value']
            }
        else:
            test = None

        reference_on_submission = None
        if 'reference' in item and item['reference'] is not None:
            if reference_on_submission is None:
                reference_on_submission = {}
            reference_on_submission['value'] = item['reference']
        if 'reference_source' in item and item['reference_source'] is not None:
            if reference_on_submission is None:
                reference_on_submission = {}
            reference_on_submission['source'] = item['reference_source']

        global_reference = global_references.get(item['name'])
        if global_reference is not None:
            reference  = {
                'value': global_reference['value']
            }
            if 'source' in global_reference:
                reference['source'] = global_reference['source']
        else:
            reference = None

        view_data.append({
            'name': item['name'],
            'status': item['status'],
            'test': test,
            'reference_on_submission': reference_on_submission,
            'reference': reference,
        })

    return view_data

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
