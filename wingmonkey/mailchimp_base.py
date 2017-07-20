from pprint import pformat


class MailChimpData(object):
    """
    Base class mailchimp data container
    """
    __slots__ = ()

    @property
    def empty_fields(self):
        """
        :return: tuple: keys of fields with empty values
        """
        empty = []

        try:
            self.__getattribute__('__dict__')
        except AttributeError:
            for attribute in self.__slots__:
                if not self.__getattribute__(attribute):
                    empty.append(attribute)
        else:
            for key, value in self.__dict__.items():
                if value is None:
                    empty.append(key)

        return tuple(empty)

    def __repr__(self):
        repr_dict = {}
        try:
            repr_dict = self.__getattribute__('__dict__')
        except AttributeError:
            for attribute in self.__slots__:
                repr_dict.update({attribute: self.__getattribute__(attribute)})
        return pformat(repr_dict, indent=4)
