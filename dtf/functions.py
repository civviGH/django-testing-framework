from dtf.models import Project, TestReference

def get_default_margin(valuetype):
    if valuetype == 'integer':
        return 0
    return None

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
        if not 'margin' in result:
            result['margin'] = get_default_margin(result['valuetype'])
        if not 'status' in result:
            result['status'] = 'unknown'
    return results

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
