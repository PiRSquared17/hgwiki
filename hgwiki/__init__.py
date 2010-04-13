#!/usr/bin/env python

# hgwiki, Copyright (c) 2010, R. P. Dillon <rpdillon@etherplex.org>
# This file is part of hgwiki.
#
# hgwiki is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
hgwiki - Provides a distributed wiki backed by merurial.
'''
import web
from hgwiki import WikiContent, ReadNode, EditNode, PageIndex, DeleteNode, NodeHistory, StaticLibs, RecoverNode, Help
from hgwiki import getExtensionPath

def hgwiki(ui, repo, **opts):
    """
    Invokes web.py to serve content using the WikiContentEngine.
    """

    urls = (
        '/PageIndex',    'PageIndex',
        '/Help',         'Help',
        '/history/(.*)', 'NodeHistory',
        '/delete/(.*)',  'DeleteNode',
        '/recover/(.*)', 'RecoverNode',
        '/edit/(.*)',    'EditNode',
        '/lib/(.*)',     'StaticLibs',
        '/(.*)',         'ReadNode'
    )

    from mercurial import hg
    import sys
    sys.path.append("C:\\Python26\\lib")
    sys.path.append(getExtensionPath())

    if opts['rev'] == '':
        rev = repo.changelog.nodemap[repo.changelog.tip()]
    else:
        rev = opts['rev']

    #Set up the content engine
    WikiContent.setUi(ui)
    WikiContent.setRepo(repo)
    WikiContent.setRev(rev)

    # Hack to avoid web.py parsing mercurial's command-line args
    app = web.application(urls, globals())
    import sys
    sys.argv = ['hgwiki', opts['port']] # Hack to avoid web.py parsing mercurial's command-line args
    app.run()

cmdtable = {
    "wiki": (hgwiki,
             [('r', 'rev', '', 'The revision of the repository to serve.'),
              ('p', 'port', '8080', 'The port on which to serve.')],
             "hg wiki [options]")
}
