import socket
import ssl


class URL:
    def __init__(self, url):
        """
        Parameters
        ----------
        url: str
            Url for the request
        """
        # parses url, could be done with urllib
        self.url = url
        self.scheme, url = url.split('://', 1)

        if '/' not in url:
            url += '/'
        self.host, url = url.split('/', 1)

        # default port numbers
        if self.scheme == 'http':
            self.port = 80
        elif self.scheme == 'https':
            self.port = 443

        # support of custom port
        if ':' in self.host:
            self.host, port = self.host.split(':', 1)
            self.port = int(port)

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
        assert self.scheme in {'http', 'https'}

        # creates a socket
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, self.port))
        if self.scheme == 'https':
            # context for encrypted connection
            context = ssl.create_default_context()
            # encrypts a socket connection
            s = context.wrap_socket(s, server_hostname=self.host)

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

    def show(self, body):
        in_tag = False
        for character in body:
            if character == '<':
                in_tag = True
            elif character == '>':
                in_tag = False
            elif not in_tag:
                print(character, end='')

    def load(self):
        body = self.request()
        self.show(body)
