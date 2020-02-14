import re
import subprocess


def echo_and_run(*args):
    command = ' '.join(args)
    print('  ' + command)
    subprocess.call(args)


versions = []
with open('.python-version') as python_version:
    for line in python_version:
        version = line.strip()
        if version:
            versions.append(version)

versions.remove('rinoh-tox')

RE_STABLE = re.compile(r'^\d\.\d+\.\d+$')
latest_stable_parts = (0, 0, 0)

for version in versions:
    print('Installing {} using pyenv...'.format(version))
    echo_and_run('pyenv', 'install', '--skip-existing', version)
    if RE_STABLE.match(version):
        parts = tuple(int(num) for num in version.split('.'))
        latest_stable_parts = max(parts, latest_stable_parts)

latest_stable = '.'.join(str(num) for num in latest_stable_parts)
print("Now you can set up the 'rinoh-tox' pyenv virtualenv:")
print('  pyenv virtualenv {} rinoh-tox'.format(latest_stable))
print('  pip install -r rinoh-tox.txt')
