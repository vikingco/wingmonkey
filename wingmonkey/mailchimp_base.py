from pprint import pformat


class MailChimpData(object):
    """
    Base class mailchimp data container
    """
    @property
    def empty_fields(self):
        """
        :return: tuple: keys of fields with empty values
        """
        empty = []
        for key, value in self.__dict__.items():
            if value is None:
                empty.append(key)
        return tuple(empty)

    def __repr__(self):
        return pformat(self.__dict__, indent=4)
