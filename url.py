import socket
import ssl
import string

from const import DEFAULT_URL, SCHEMES


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

        if url is None:
            url = DEFAULT_URL

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

        self.headers = {
            '1.0': {
                'Host': self.host
            },
            '1.1': {
                'Host': self.host,
                'Connection': 'close',
                'User-agent': 'Rety'
            }
        }

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
        # can handle following schemes
        assert self.scheme in SCHEMES

        # creates a socket
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        # handles http request and response
        if self.scheme in {'http', 'https'}:

            s.connect((self.host, self.port))
            if self.scheme == 'https':
                # context for encrypted connection
                context = ssl.create_default_context()
                # encrypts a socket connection
                s = context.wrap_socket(s, server_hostname=self.host)

            s.send(self.compose_request().encode('utf8'))

            # gets and handles response
            response = s.makefile('r', encoding='UTF-8', newline='\r\n')
            status_line = response.readline()
            state = status_line.split(' ')  # version, status, explanation, etc

            response_headers = {}
            while True:
                line = response.readline()
                if line == '\r\n':
                    break
                header, value = line.split(':', 1)
                response_headers[header.casefold()] = value.strip()

            encoding = self.find_encoding(response_headers['content-type'])
            if encoding:
                response = s.makefile('r', encoding=encoding, newline='\r\n')

            # reads the rest of response
            body = response.read()
            s.close()

            # unusual cases
            # assert 'transfer-encoding' not in response_headers
            # assert 'content-encoding' not in response_headers

        # handles file request and response
        elif self.scheme in {'file'}:
            with open(self.path[1:], 'r') as response:
                body = response.read()

        return body

    def compose_request(self, scheme='1.1'):
        """Composes request message to send to a server

        Parameters
        ----------
        scheme: str
            is either 1.0 or 1.1 for http

        Returns
        -------
        msg: str
            Request message for a server
        """
        msg = f'GET {self.path} HTTP/{scheme}\r\n'
        headers = self.headers[scheme]
        for header in headers:
            msg += f'{header}: {headers[header]}\r\n'
        return msg + '\r\n'

    def find_encoding(self, content_type):
        """Fetches encoding from content-type of response if it is provided

        Parameters
        ----------
        content_type: str
            All properties of content-type as string

        Returns
        -------
        str
            encoding scheme if any
        """
        if 'charset' in content_type:
            properties = content_type.split(' ')
            for p in properties:
                if 'charset=' in p:
                    encoding = p.split('=')[-1].strip(string.punctuation + ' ')
                    return encoding
        return None

    def show(self, body):
        """Shows (prints) raw text of html file (without tags)

        Parameters
        ----------
        body: str
            HTML raw text

        Returns
        -------
        None
        """
        in_tag = False
        for character in body:
            if character == '<':
                in_tag = True
            elif character == '>':
                in_tag = False
            elif not in_tag:  # print if not inside tag marks (if not an html tag)
                print(character, end='')

    def load(self):
        body = self.request()
        self.show(body)
