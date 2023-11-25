import sys
from url import URL

if __name__ == '__main__':
    URL.load(URL(sys.argv[1] if len(sys.argv) > 1 else None))
