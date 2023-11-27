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

        # dict of used schemes
        self.schemes = dict.fromkeys(SCHEMES, False)

        # sockets to keep alive
        self.alive_sockets = set()

        if url is None:
            url = DEFAULT_URL

        # support for data scheme
        if url.startswith('data:'):
            self.scheme, url = url.split(':', 1)
            self.content_type, self.text = url.split(',', 1)

        else:
            # support for view-source scheme
            if url.startswith('view-source'):
                self.schemes['view-source'] = True
                _, url = url.split(':', 1)

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
        # default body value
        body = ''
        # handles http request and response
        if self.scheme in {'http', 'https'}:

            s.connect((self.host, self.port))
            # encrypts connection
            if self.scheme == 'https':
                s = self.encrypted_connect(s)

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

            # changes encoding it is not UTF-8
            encoding = self.find_encoding(response_headers['content-type'])
            if encoding:
                response = s.makefile('r', encoding=encoding, newline='\r\n')

            # reads the rest of response
            body = response.read()
            self.alive_sockets.add(s)

            # unusual cases
            # assert 'transfer-encoding' not in response_headers
            # assert 'content-encoding' not in response_headers

        # handles file request and response
        elif self.scheme == 'file':
            with open(self.path[1:], 'r') as response:
                body = response.read()

        elif self.scheme == 'data':
            if self.content_type == 'text/html':
                body = f'''
                <!doctype html>
                <html>
                <head></head>
                <body>
                {self.text}
                </body>
                </html>'''

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

    def encrypted_connect(self, s):
        """Encrypts a socket object for https

        Parameters
        ----------
        s: socket.socket
            Object to be encrypted

        Returns
        -------
        s: socket.socket
            Encrypted object
            """
        # context for encrypted connection
        context = ssl.create_default_context()
        # encrypts a socket connection
        return context.wrap_socket(s, server_hostname=self.host)

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
        # support of html escape characters
        escape_characters = {
            '&lt;': '<',
            '&gt;': '>'
        }
        max_esc_char = 5
        in_tag = False
        i = 0
        while i < len(body):
            if body[i] == '&':
                esc_seq = ''
                for j in range(max_esc_char):
                    esc_seq += body[i + j]
                    if i + j == len(body):
                        i += 1
                        continue
                    if esc_seq in escape_characters:
                        i += j + 1
                        print(escape_characters[esc_seq], end='')
                        continue

            if body[i] == '<' and not self.schemes['view-source']:
                in_tag = True
            elif body[i] == '>' and not self.schemes['view-source']:
                in_tag = False
            elif not in_tag:  # print if not inside tag marks (if not an html tag)
                print(body[i], end='')
            i += 1

    def load(self):
        body = self.request()
        self.show(body)
