from tortoise.models import Model
from tortoise import fields


class Profile(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(255, unique=True)
    age = fields.CharField(255)
    height = fields.CharField(255)

    def __str__(self):
        return self.name
