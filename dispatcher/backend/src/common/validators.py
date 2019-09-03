from bson.objectid import ObjectId, InvalidId
import trafaret as t


class ObjectIdValidator(t.String):
    def check_and_return(self, value):
        try:
            return ObjectId(value)
        except InvalidId:
            self._failure('Invalid Mongo ObjectId')
