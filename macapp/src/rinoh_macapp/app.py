import os
import subprocess


TARGET_DIR = '/usr/local/bin'

DIALOG_TITLE = 'Install rinoh command line tool'
DIALOG_MESSAGE = ("Install the 'rinoh' command line tool to {target_dir}?\n"
                  "\n"
                  "Afterwards, you can run \'rinoh\' from the command line"
                  .format(target_dir=TARGET_DIR))

SCRIPT = ('tell app "System Events" to'
          '  display dialog "{message}" '
          '    with title "{title}"'
          .format(title=DIALOG_TITLE, message=DIALOG_MESSAGE))


if __name__ == '__main__':
    with open(os.devnull, 'w') as devnull:
        rc = subprocess.call(['osascript', '-e', SCRIPT],
                             stdout=devnull, stderr=devnull)
    if rc == 0:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        rinoh_path = os.path.join(script_dir, 'rinoh.sh')
        link_path = os.path.join(TARGET_DIR, 'rinoh')
        if os.path.lexists(link_path):
            os.remove(link_path)
        os.symlink(rinoh_path, link_path)
