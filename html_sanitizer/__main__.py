import sys

from .sanitizer import Sanitizer


sanitizer = Sanitizer()

if len(sys.argv) > 1:
    for filename in sys.argv[1:]:
        with open(filename) as f:
            print(sanitizer.sanitize(f.read()))
else:
    print(sanitizer.sanitize(sys.stdin.read()).encode("utf-8"))
