import os
import sys
import struct

from ._compat import raw_input, PY2, text_type, string_types, \
     get_best_encoding
from .utils import echo
from .exceptions import Abort, UsageError
from .types import convert_type


# The prompt functions to use.  The doc tools currently override these
# functions to customize how they work.
visible_prompt_func = raw_input


def hidden_prompt_func(prompt):
    import getpass
    return getpass.getpass(prompt)


def _build_prompt(text, suffix, show_default=False, default=None):
    prompt = text
    if default is not None and show_default:
        prompt = '%s [%s]' % (prompt, default)
    return prompt + suffix


def prompt(text, default=None, hide_input=False,
           confirmation_prompt=False, type=None,
           value_proc=None, prompt_suffix=': ', show_default=True):
    """Prompts a user for input.  This is a convenience function that can
    be used to prompt a user for input later.

    If the user aborts the input by sending a interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the text to show for the prompt.
    :param default: the default value to use if no input happens.  If this
                    is not given it will prompt until it's aborted.
    :param hide_input: if this is set to true then the input value will
                       be hidden.
    :param confirmation_prompt: asks for confirmation for the value.
    :param type: the type to use to check the value against.
    :param value_proc: if this parameter is provided it's a function that
                       is invoked instead of the type conversion to
                       convert a value.
    :param prompt_suffix: a suffix that should be added to the prompt.
    :param show_default: shows or hides the default value in the prompt.
    """
    result = None

    def prompt_func(text):
        f = hide_input and hidden_prompt_func or visible_prompt_func
        try:
            return f(text)
        except (KeyboardInterrupt, EOFError):
            raise Abort()

    if value_proc is None:
        value_proc = convert_type(type, default)

    prompt = _build_prompt(text, prompt_suffix, show_default, default)

    while 1:
        while 1:
            value = prompt_func(prompt)
            if value:
                break
            # If a default is set and used, then the confirmation
            # prompt is always skipped because that's the only thing
            # that really makes sense.
            elif default is not None:
                return default
        try:
            result = value_proc(value)
        except UsageError as e:
            echo('Error: %s' % e.message)
            continue
        if not confirmation_prompt:
            return result
        while 1:
            value2 = prompt_func('Repeat for confirmation: ')
            if value2:
                break
        if value == value2:
            return result
        echo('Error: the two entered values do not match')


def confirm(text, default=False, abort=False, prompt_suffix=': ',
            show_default=True):
    """Prompts for confirmation (yes/no question).

    If the user aborts the input by sending a interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the question to ask.
    :param default: the default for the prompt.
    :param abort: if this is set to `True` a negative answer aborts the
                  exception by raising :exc:`Abort`.
    :param prompt_suffix: a suffix that should be added to the prompt.
    :param show_default: shows or hides the default value in the prompt.
    """
    prompt = _build_prompt(text, prompt_suffix, show_default,
                           default and 'Yn' or 'yN')
    while 1:
        try:
            value = visible_prompt_func(prompt).lower().strip()
        except (KeyboardInterrupt, EOFError):
            raise Abort()
        if value in ('y', 'yes'):
            rv = True
        elif value in ('n', 'no'):
            rv = False
        elif value == '':
            rv = default
        else:
            echo('Error: invalid input')
            continue
        break
    if abort and not rv:
        raise Abort()
    return rv


def get_terminal_size():
    """Returns the current size of the terminal as tuple in the form
    ``(width, height)`` in columns and rows.
    """
    # If shutil has get_terminal_size() (Python 3.3 and later) use that
    if sys.version_info >= (3, 3):
        import shutil
        shutil_get_terminal_size = getattr(shutil, 'get_terminal_size', None)
        if shutil_get_terminal_size:
            sz = shutil_get_terminal_size()
            return sz.columns, sz.lines

    def ioctl_gwinsz(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack(
                'hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except Exception:
            return
        return cr

    cr = ioctl_gwinsz(0) or ioctl_gwinsz(1) or ioctl_gwinsz(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            try:
                cr = ioctl_gwinsz(fd)
            finally:
                os.close(fd)
        except Exception:
            pass
    if not cr or not cr[0] or not cr[1]:
        cr = (os.environ.get('LINES', 25),
              os.environ.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])


def echo_via_pager(text):
    """This function takes a text and shows it via an environment specific
    pager on stdout.

    :param text: the text to page.
    """
    if not isinstance(text, string_types):
        text = text_type(text)

    if PY2 and isinstance(text, text_type):
        encoding = get_best_encoding(sys.stdout)
        text = text.encode(encoding, 'replace')

    # Pydoc's pager is badly broken with LANG=C on Python 3 to the point
    # where it will corrupt the terminal.  http://bugs.python.org/issue21398
    # I don't feel like reimplementing it given that it works on Python 2
    # and seems reasonably stable otherwise.
    import pydoc
    pydoc.pager(text)
