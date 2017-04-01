import email.header
import email.errors
import re


def decode_any_header(value):
    '''Wrapper around email.header.decode_header to absorb all errors.'''
    value = re.sub(r'[\r\n]\s*', ' ', value)
    try:
        chunks = email.header.decode_header(value)
    except email.errors.HeaderParseError:
        chunks = [(value, None)]

    header = email.header.Header()
    for string, charset in chunks:
        if charset is not None:
            if not isinstance(charset, email.header.Charset):
                charset = email.header.Charset(charset)
        try:
            try:
                header.append(string, charset, errors='strict')
            except UnicodeDecodeError:
                header.append(string, 'latin1', errors='strict')
        except:
            header.append(string, charset, errors='replace')
    return header
