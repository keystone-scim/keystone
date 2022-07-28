class ResourceNotFound(Exception):
    def __init__(self, resource_type: str, resource_id: str, *args):
        super(ResourceNotFound, self).__init__(*args)
        self.resource_type = resource_type
        self.resource_id = resource_id

    def __str__(self):
        return f"{self.resource_type} {self.resource_id} could not be found"


class ResourceAlreadyExists(Exception):
    def __init__(self, resource_type: str, resource_id: str, *args):
        super(ResourceAlreadyExists, self).__init__(*args)
        self.resource_type = resource_type
        self.resource_id = resource_id

    def __str__(self):
        return f"{self.resource_type} {self.resource_id} already exists in the target SCIM tenant"


class UnauthorizedRequest(Exception):
    pass
