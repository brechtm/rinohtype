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


def run_apple_script(script):
    with open(os.devnull, 'w') as devnull:
        return subprocess.call(['osascript', '-e', script],
                               stdout=devnull, stderr=devnull)


if __name__ == '__main__':
    if run_apple_script(SCRIPT) == 0:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        rinoh_path = os.path.join(script_dir, 'rinoh.sh')
        link_path = os.path.join(TARGET_DIR, 'rinoh')
        create_link = ('mkdir -p {} && ln -sfh {} {}'
                       .format(TARGET_DIR, rinoh_path, link_path))
        run_apple_script('do shell script "{}" with administrator privileges'
                         .format(create_link))
