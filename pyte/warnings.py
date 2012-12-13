
import warnings
from warnings import formatwarning as standard_formatwarning
from warnings import showwarning as standard_showwarning


class PyteWarning(Warning):
    pass


def warn(message):
    warnings.warn(PyteWarning(message))


def formatwarning(message, category, filename, lineno, line=None):
    if category == PyteWarning:
        return '{}\n'.format(message.args[0])
    else:
        return standard_formatwarning(message, category, filename, lineno, line)


warnings.formatwarning = formatwarning
