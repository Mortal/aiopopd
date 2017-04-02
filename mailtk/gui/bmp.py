import re
import tkinter


def _bmp_replace_value(v):
    if isinstance(v, (list, tuple)):
        return type(v)(_bmp_replace_value(e) for e in v)
    elif isinstance(v, str):
        return re.sub(r'[^\u0000-\uFFFF]', '\uFFFD', v)
    return v


def _bmp_replace(args, kwargs):
    args_out = tuple(_bmp_replace_value(a) for a in args)
    kwargs_out = {k: _bmp_replace_value(v) for k, v in kwargs.items()}
    if args_out == args and kwargs_out == kwargs:
        # No change, do not retry call
        return None, None
    return args_out, kwargs_out


def bmp_call(fun, *args, **kwargs):
    try:
        return fun(*args, **kwargs)
    except tkinter.TclError:
        # Try replacing non-BMP characters with U+FFFD
        args, kwargs = _bmp_replace(args, kwargs)
        if args is not None:
            try:
                v = fun(*args, **kwargs)
                print("Non-BMP characters replaced with U+FFFD when calling",
                      fun)
                return v
            except tkinter.TclError as exn:
                pass
        # Re-raise original exception
        raise
