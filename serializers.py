from autobahn.wamp import ApplicationError
from tortoise import Model
from tortoise.fields.relational import BackwardFKRelation, ForeignKeyFieldInstance

from models import Profile


class BaseSerializer:
    class Meta:
        pass

    def __init__(self, instance: Model = None) -> None:
        super().__init__()
        model = getattr(self.Meta, 'model', None)
        if not model:
            raise RuntimeError("Must set model class under Meta class")
        if not issubclass(model, Model):
            raise ValueError("model must be an instance of tortoise.Model")

        self.instance: Model = instance
        self.model = model
        self.write_only = getattr(self.Meta, 'write_only', ())
        self.read_only = getattr(self.Meta, 'read_only', ())
        self.fields_map = model._meta.fields_map
        self.fields_required = [key for key in self.fields_map.keys()
                                if key not in self.read_only and not self.fields_map[key].pk]
        self.fields_map_required = {key: value for key, value in self.fields_map.items() if key in self.fields_required}

    async def create(self, **kwargs):
        await self.validate(_raise=True, **kwargs)
        self.instance = await self.model.create(**kwargs)
        return await self.serialize()

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.instance, key, value)
        await self.instance.save()
        return await self.serialize()

    async def serialize(self):
        if not self.instance:
            raise RuntimeError("Cannot serialize; class not instantiated with tortoise.Model")
        return {key: getattr(self.instance, key) for key, value in self.fields_map.items()
                if key not in self.write_only and not isinstance(value, BackwardFKRelation)}

    async def validate(self, _raise=False, **kwargs):
        result = []
        for name, field in self.fields_map_required.items():
            if field.pk or hasattr(field, 'relation_field'):
                continue
            if name in kwargs:
                if type(field) == BackwardFKRelation:
                    if isinstance(kwargs[name], dict):
                        relation = field.model_class()
                        fk_res = await relation.validate(**kwargs[name])
                        if fk_res:
                            result.append("'{}' {}".format(name, fk_res))
                    else:
                        result.append("'{}' Invalid type".format(name))
                elif type(kwargs[name]) != field.field_type:
                    result.append("'{}' Invalid type".format(name))

                if field.unique:
                    obj = await self.model.filter(**{name: kwargs[name]}).first()
                    if obj:
                        result.append("'{}' must be unique".format(name))
            else:
                if not isinstance(field, ForeignKeyFieldInstance):
                    result.append("'{}' required".format(name))
                    continue
        if _raise and result:
            raise ApplicationError(ApplicationError.INVALID_ARGUMENT, ', '.join(result))
        return result

    async def validate_and_create(self, **kwargs):
        await self.validate(_raise=True, **kwargs)

        to_delay = []
        for key, value in self.fields_map_required.items():
            if key in kwargs:
                if type(value) == BackwardFKRelation:
                    to_delay.append({'data': kwargs.pop(key), 'model': value.model_class, 'rel': value.relation_field})

        main = await self.model.create(**kwargs)
        for item in to_delay:
            _obj = await item['model'].create(**{item['rel']: main.pk}, **item['data'])
        return True


class ProfileSerializer(BaseSerializer):
    class Meta:
        model = Profile
