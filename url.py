import socket


class URL:
    def __init__(self, url):
        """
        Parameters
        ----------
        url: str
            Url for the request
        """
        # parses url, could be done with urllib
        self.scheme, url = url.split('://', 1)
        if '/' not in url:
            url += '/'
        self.host, url = url.split('/', 1)
        self.path = '/' + url

    def request(self):
        """Makes a request and parses a response.

        Raises
        ------
        AssertionError
            If transfer-encoding or content-encoding are among
            response headers. If protocol is not http.

        Returns
        -------
        body: str
            HTML code, got from the response
        """
        # can handle only http
        assert self.scheme == 'http'

        # creates a socket
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, 80))
        s.send((f'GET {self.path} HTTP/1.0\r\n' +
                f'Host: {self.host}\r\n\r\n').encode('utf8'))

        # gets and handles response
        response = s.makefile('r', encoding='utf8', newline='\r\n')
        status_line = response.readline()
        version, status, explanation = status_line.split(' ')

        response_headers = {}
        while True:
            line = response.readline()
            if line == '\r\n':
                break
            header, value = line.split(':', 1)
            response_headers[header.casefold()] = value.strip()

        # unusual cases
        assert 'transfer-encoding' not in response_headers
        assert 'content-encoding' not in response_headers

        # reads the rest of response
        body = response.read()
        s.close()

        return body
