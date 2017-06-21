from json import loads, dumps


class SerializerMixin:
    """
    Mixin to provide simple json serialization and deserialization functions for an object
    """

    def serialize(self, indent=None, strip_empty=False):
        """
        Serializes object to json
        Removing empty values before serialization is useful when doing a post call 
        as we can not know the correct values of certain keys yet before creation on the API side( eg id ). 
        It also prevents unwanted overwriting. 
        
        :param indent: Int:spaces for pretty print indentation
        :param strip_empty: Bool: Remove all None values before serializing if True
        :return: json representation of object
        """
        return dumps(self, default=self._serializable(strip_empty), indent=indent)

    def _serializable(self, strip_empty=False):
        """
        :param strip_empty: Bool: Remove all None values from serializable representation if True
        :return: function returning serializable version of object
        """
        if strip_empty:
            return lambda obj: {k: v for k, v in obj.__dict__.items() if v is not None}
        else:
            return lambda obj: obj.__dict__

    def deserialize(self, json_string):
        """
        Deserializes json string to object
        
        :param json_string: json representation of object to be deserialized
        :return: Bool
        """
        dictionary = loads(json_string)
        for key in self.__dict__.keys():
            self.__dict__[key] = dictionary[key]
        return True

    def __repr__(self):
        return self.serialize(indent=4)
