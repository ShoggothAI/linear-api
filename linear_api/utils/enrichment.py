import functools

from linear_api.domain import LinearModel


def enrich_with_client(func):
    """
    Decorator for recursively adding a reference to the client to returned models.
    Avoids infinite recursion by only checking direct model attributes.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)

        def enrich_recursively(obj):
            if isinstance(obj, LinearModel):
                obj.with_client(self.client)

                # Only process direct model attributes, not properties or methods
                # and avoid visiting already processed objects
                for attr_name, attr_value in obj.__dict__.items():
                    if attr_name.startswith('_'):
                        continue

                    if isinstance(attr_value, LinearModel):
                        enrich_recursively(attr_value)
                    elif isinstance(attr_value, list):
                        for i, item in enumerate(attr_value):
                            if isinstance(item, LinearModel):
                                enrich_recursively(item)
                    elif isinstance(attr_value, dict):
                        for k, v in attr_value.items():
                            if isinstance(v, LinearModel):
                                enrich_recursively(v)

                return obj
            elif isinstance(obj, list):
                return [enrich_recursively(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: enrich_recursively(v) for k, v in obj.items()}
            else:
                return obj

        return enrich_recursively(result)

    return wrapper