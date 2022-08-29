from ninja import Schema

class SuccessOut(Schema):
    message: str = "success"

class AlreadyExistsOut(Schema):
    message: str = 'already exists'

class NotFoundOut(Schema):
    message: str = 'not found'

class BadRequestOut(Schema):
    message: str = 'bad request'

class InvalidUserOut(Schema):
    message: str = 'invalid user'