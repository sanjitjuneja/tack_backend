def _setup_filters(**kwargs):
    filters = dict()
    for key, value in kwargs.items():
        if value:
            filters[key] = value
    return filters
