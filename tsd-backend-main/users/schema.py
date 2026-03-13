
def generate_field_docs():
    """Генерирует документацию для всех полей в формате OpenAPI"""
    fields = [
        {
            'name': 'first_name',
            'filter_ops': ['eq', 'ne', 'contains', 'startswith', 'endswith'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'last_name',
            'filter_ops': ['eq', 'ne', 'contains', 'startswith', 'endswith'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'job_title',
            'filter_ops': ['eq', 'ne', 'contains', 'startswith', 'endswith'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'is_active',
            'filter_ops': ['eq', 'ne'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'hiring_date',
            'filter_ops': ['eq', 'ne', 'gt', 'lt', 'ge', 'le'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'team',
            'filter_ops': ['eq', 'ne', 'contains'],
            'sort_ops': ['asc', 'desc']
        },
        {
            'name': 'desk',
            'filter_ops': ['eq', 'ne'],
            'sort_ops': ['asc', 'desc']
        }
    ]

    description = "The query's available parameters:\n\n"

    for field in fields:
        description += f"<details><summary>The '{field['name']}' parameter:</summary>\n"
        description += "<ul>\n"
        description += "<li><b>Filter operators:</b>\n<ul>\n"
        for op in field['filter_ops']:
            description += f"<li>-{op}-</li>\n"
        description += "</ul>\n</li>\n"
        description += "<li><b>Sort operators:</b>\n<ul>\n"
        for op in field['sort_ops']:
            description += f"<li>-{op}-</li>\n"
        description += "</ul>\n</li>\n"
        description += "</ul>\n</details>\n\n"

    return description


FIELD_DOCS = generate_field_docs()

FILTER_DESCRIPTION = f"""
The filter query that excludes parameters from a response.
Example of usage: <mark><i>first_name-eq-John</i></mark>

{FIELD_DOCS}
"""

SORT_DESCRIPTION = """
The sort query that sort responses' data according to specified parameters.
Example of usage: <mark><i>hiring_date-desc</i></mark>
"""