from pprint import PrettyPrinter


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
        pretty = str(PrettyPrinter(indent=4).pprint(self.__dict__))
        return pretty
