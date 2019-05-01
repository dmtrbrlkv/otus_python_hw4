from const import UNKNOWN


class Request():
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.parsed = False
        self._url = ""
        self._method = ""

    def parse_data(self):
        splited_data = self.raw_data.split()
        if len(splited_data) < 2:
            method = UNKNOWN
            url = UNKNOWN
        else:
            method = splited_data[0]
            url = splited_data[1]

        self.method = method
        self.url = url

        self.parsed = True

    @property
    def url(self):
        if not self.parsed:
            self.parse_data()

        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def method(self):
        if not self.parsed:
            self.parse_data()

        return self._method

    @method.setter
    def method(self, value):
        self._method = value
