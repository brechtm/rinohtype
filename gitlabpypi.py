# A simple PyPI-compatible index server allowing installation of releases
# uploaded to GitLab (under tags)

import os
import re

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import loads
from threading import Thread
from urllib.request import build_opener


PORT_NUMBER = 8080


class GitLabPyPIRequestHandler(BaseHTTPRequestHandler):
    RE_MARKDOWNLINK = re.compile(r'\[(.*)\]\((.*)\)')

    def do_GET(self):
        package = self.path.strip('/')
        projects = self.server.projects
        if package not in ('', 'shutdown') and package not in projects:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html>')
        if self.path == '/':
            self.wfile.write(b'<head><title>GitLab PyPI</title></head>')
            self.wfile.write(b'<body>')
            for package in projects:
                self.wfile.write('<a href="{0}">{0}</a><br/>'
                                 .format(package).encode('utf-8'))
            self.wfile.write(b'</body>')
        elif self.path == '/shutdown':
            self.wfile.write(b'<head><title>GitLab PyPI</title></head>')
            self.wfile.write(b'<body>Shutting down...</body>')
            self.wfile.write(b'</html>')
            Thread(target=self.server.shutdown, daemon=True).start()
        else:
            package = self.path.strip('/')
            try:
                project_id, project_url = projects[package]
            except KeyError:
                self.send_response(404)
                self.end_headers()
                return
            self.wfile.write(b'<head>')
            self.wfile.write('<title>GitLab PyPI - {}</title></head>'
                             .format(package).encode('utf-8'))
            self.wfile.write(b'<meta name="api-version" value="2" />')
            self.wfile.write(b'<body>')
            opener = self.server.opener
            res = opener.open('https://gitlab.com/api/v3/projects/{}'
                              '/repository/tags'.format(project_id))
            for tag in loads(res.read().decode('utf-8')):
                release = tag['release']
                if release is None:
                    continue
                description = release['description']
                for match in self.RE_MARKDOWNLINK.finditer(description):
                    fname, link = match.groups()
                    gitlab_token = self.server.gitlab_token
                    self.wfile.write('<a href="{}/{}?private_token={}">{}</a>'
                                     '<br/>'.format(project_url, link,
                                                    gitlab_token, fname)
                                     .encode('utf-8'))
            self.wfile.write(b'</body>')
        self.wfile.write(b'</html>')


class GitLabPyPIServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        try:
            self.gitlab_token = os.environ['GITLAB_TOKEN']
        except KeyError:
            raise SystemExit('Fatal error: the GITLAB_TOKEN environment '
                             'variable is not set. Aborting.')
        self.opener = build_opener()
        self.opener.addheaders = [('PRIVATE-TOKEN', self.gitlab_token)]
        res = self.opener.open('https://gitlab.com/api/v3/projects')
        self.projects = {project['name']: (project['id'], project['web_url'])
                         for project in loads(res.read().decode('utf-8'))}
        super().__init__(*args, **kwargs)


@contextmanager
def gitlab_pypi_server():
    server = GitLabPyPIServer(('localhost', PORT_NUMBER),
                              GitLabPyPIRequestHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    print('Started GitLab PyPI server on port ', PORT_NUMBER)
    yield 'http://{}:{}'.format(*server.server_address)
    print('Shutting down the GitLab PyPI server')
    Thread(target=server.shutdown, daemon=True).start()


if __name__ == '__main__':
    print('GitLab PyPI server test')
    with gitlab_pypi_server() as url:
        print(url)
        print('Press <return> to shut down the server')
        input()
    input('Press <return> to exit')
