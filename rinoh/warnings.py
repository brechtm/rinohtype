
import warnings
from warnings import formatwarning as standard_formatwarning
from warnings import showwarning as standard_showwarning


class RinohWarning(Warning):
    pass


def warn(message):
    warnings.warn(RinohWarning(message))


def formatwarning(message, category, filename, lineno, line=None):
    if category == RinohWarning:
        return '{}\n'.format(message.args[0])
    else:
        return standard_formatwarning(message, category, filename, lineno, line)


warnings.formatwarning = formatwarning
