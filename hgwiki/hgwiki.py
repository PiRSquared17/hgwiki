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

import mercurial
import datetime
import web
import templates

from os import access
from os import F_OK
from os import chdir
from os import getcwd
from os import listdir
from os import mkdir
from os import remove
from os import sep

from os.path import expanduser
from os.path import isdir

from re import compile
from re import sub
from re import MULTILINE

from urllib import unquote_plus

from textile import textile
from rest import *

#######################################################################
# Global utility functions that work independent of a particular
# repository

# extensionPath is the path in which this extension is installed.
extensionPath = None
def getExtensionPath():
    """
    Finds the path associated with the current extension and returns
    it.
    """
    if extensionPath == None:
        from mercurial import hg
        for module in hg.extensions.extensions():
            if module[1].__name__ == "hgext_hgwiki":
                return module[1].__path__[0]
    else:
        return extensionPath

def getTemplate(templateName, globals=None):
    templateDir = 'templates'
    template = str(getExtensionPath()) + sep + templateDir + sep + templateName
    return web.template.frender(template, globals=globals)


def getParams():
    """
    Retrives the web.ctx.query string and parses it into a list of
    params passed to server in the last request.
    """
    import re
    tokens = re.split("[?&=]", web.ctx.query[1:])
    d = {}
    if len(tokens) == 1: return d
    def popDict(l, d):
        if len(l) != 0:
            d[l[0]] = l[1]
            return popDict(l[2:], d)
        else:
            return d
    return popDict(tokens, d)

def getParam(param, default=None):
    """
    Retrieves the given parameter, if it was specified.  If it was not
    specified, returns the provided default value.  If the default
    value was not provided, returns None.
    """
    params = getParams()
    if param in params:
        return params[param]
    else:
        return default
#######################################################################
# Classes
class StaticLibs(object):
    """
    Allows us to serve static content from the lib directory.

    TODO: abstract this into a class that serves content from the
    specified directory.
    """
    def GET(self, filename):
        assert '..' not in filename
        try:
            web.header( 'Cache-Control', 'max-age=1000000')
            f = open(str(getExtensionPath()) + "/lib/"  + str(filename))
            return f.read()
        except IOError:
            web.notfound()

class WikiContent(object):
    """
    A base class for all urls that contain wiki content.  Provides
    access to repository, ui and version objects, and provides some
    utility methods (like calling out to the markup conversion
    engine, checking for the existence of a node, etc.)
    """
    DEFAULT_PAGE = "MainPage"

    ui = None
    repo = None
    rev = None    

    @staticmethod
    def setUi(ui):
        """
        Sets the Mercurial user interface object.  We rarely use this
        because we're essentially writing a web-based ui, but it is
        needed for some operations (like committing data to the
        repository).
        """
        WikiContent.ui = ui

    @staticmethod
    def setRepo(repo):
        """
        Sets the Mercurial repository from which we will read and
        write.  
        """
        WikiContent.repo = repo
        
    @staticmethod
    def setRev(rev):
        """
        In the case the user doesn't specify a revision for a
        particular operation (which is most of the cases), this is the
        revision to use.
        Often is 'tip', the latest revision.
        """
        WikiContent.rev = rev

    def _nodeExist(self, node, rev=None):
        """
        Returns whether or not a node exists in the repository.
        """
        if rev == None:
            rev = self.rev
        return node in self.repo[rev]

    def _getNodeText(self, node, revision=None):
        """
        Returns the raw text of the specified node.  This is usually
        text in the markup language used by the wiki -- the default is
        reStructuredText, but it could be Textile, Markdown, etc.
        """
        if self._nodeExist(node, revision):
            return self.repo[revision][node].data()
        else:
            return ""

    def _toHtml(self, doc):
        """
        Returns an HTML interpretation of the node's plaintext.

        This is the place to swap out different markup engines.  The
        default is reStructuredText.
        """
        doc = html_body(unicode(doc)).encode() # docutils engine, using reST
        #doc = textile(doc)
        return doc

    def _doCommit(self, msg):
        time = datetime.datetime.now()
        time = time.replace(microsecond=0)
        mercurial.commands.commit(self.ui, self.repo, 
                                  message=msg, 
                                  date=str(time), user=self.ui.username(), logfile=None)
        # Increment the current rev, because we just altered it!
        WikiContent.rev = WikiContent.repo.changelog.nodemap[WikiContent.repo.changelog.tip()]

    def _privileged(self):
        """
        The privileged user is the user connecting from the same
        computer on which the server is located.
        """
        return web.ctx.ip == '127.0.0.1'

class ReadNode(WikiContent):
    """
    The class responsible for reading nodes and displaying them.
    """
    def GET(self, node):
        revision = getParam("rev", self.rev)
        wikipage = getTemplate('wikipage.html')

        # Sets the default document, in the case that is was not specified
        if node == "": node = self.DEFAULT_PAGE
        if node in self.repo[revision]:
            doc = self._getNodeText(node, revision)
            doc = self._toHtml(doc)
        else:
            raise web.seeother("/edit/" + node)
        return wikipage(node, doc, self._privileged())

class PrintNode(WikiContent):
    """
    Views the provided document in a from suitable for printing.
    """
    def GET(self, node):
        from docutils import core
        revision = getParam("rev", self.rev)

        # Sets the default document, in the case that is was not specified
        if node == "": node = self.DEFAULT_PAGE
        if node in self.repo[revision]:
            doc = self._getNodeText(node, revision)
            doc = core.publish_string(doc, writer_name="html4css1")
        else:
            raise web.seeother("/edit/" + node)
        return doc

class EditNode(WikiContent):
    def _clean(self, text):
        """
        Cleans up the input from the user and prepares it for writing
        to disk.

        So far, this changes Windows line breaks into Unix-style
        breaks and unquotes the text.
        """
        # Windows crap
        import string
        text = string.replace(text, '\r\n', '\n')
        text = string.replace(text, '\r', '\n')
        # Decode urlencoded string produced by the form
        content = unquote_plus(text)
        return text

    def GET(self, node):
        if node == "": node = self.DEFAULT_PAGE
        wikipage = getTemplate('wikipage.html')
        editform = getTemplate('editform.html')
        doc = editform(node, self._getNodeText(node))
        # Trap URL hacks and provide an error message.
        if not self._privileged(): doc = "You are not authorized to edit this page."
        return wikipage(node, doc, self._privileged())

    def POST(self, node):
        # Trap URL hacks and redirect.
        if not self._privileged(): raise web.seeother('/' + node)

        text = web.input().wikitext

        if node in self.repo[self.rev]:
            path = self.repo[self.rev][node].path()
        else:
            path = self.repo.root + "/" + node
        f = open(path, 'w')
        f.write(self._clean(text))
        f.close()

        msg = "Changed " + node + ". [Web Interface]"
        if not node in self.repo[self.rev]:
            mercurial.commands.add(self.ui, self.repo, path)
            msg = "Added " + node + ". [Web Interface]"

        self._doCommit(msg)
        raise web.seeother('/' + node)

class DeleteNode(WikiContent):
    def GET(self, node):
        # Trap URL hacks and redirect.
        if not self._privileged(): raise web.seeother('/' + node)

        if self._nodeExist(node):
            mercurial.commands.remove(self.ui, self.repo, node)
            self._doCommit("Removed " + node + ". [Web Interface]")
        raise web.seeother('/')

class NodeHistory(WikiContent):
    def GET(self, node):
        from datetime import datetime
        wikipage = getTemplate('wikipage.html')
        nodehistory = getTemplate('nodehistory.html')
        revs = self.repo.changelog.nodemap.values()
        revs.sort()
        revs.reverse()
        doc = nodehistory(datetime, node, revs, self.repo)
        return wikipage(node, doc, self._privileged())


class PageIndex(WikiContent):
    def GET(self):
        wikipage = getTemplate('wikipage.html')
        pageindex = getTemplate('pageindex.html')
        pages = [f for f in self.repo[self.rev]]
        doc = pageindex(pages)
        return wikipage("PageIndex", doc, self._privileged())

class RecoverNode(WikiContent):
    def GET(self, node):
        # Trap URL hacks and redirect.
        if not self._privileged(): raise web.seeother('/' + node)

        revision = getParam("rev", self.rev)
        text = self._getNodeText(node, revision)

        if node in self.repo[self.rev]:
            path = self.repo[self.rev][node].path()
        else:
            path = self.repo.root + "/" + node
        f = open(path, 'w')
        f.write(text)
        f.close()

        if not node in self.repo[self.rev]:
            mercurial.commands.add(self.ui, self.repo, path)

        msg = "Reverted " + node + " back to revision " + revision + ". [Web Interface]"
        self._doCommit(msg)
        raise web.seeother('/' + node)        

class Upload(WikiContent):
    def GET(self):
        web.header("Content-Type","text/html; charset=utf-8")
        form =  """
                 <html><head></head><body>
                 <form method="POST" enctype="multipart/form-data" action="">
                 <input type="file" name="fileupload" />
                 <br/>
                 <input type="submit" />
                 </form>
                 </body></html>
                """
        wikipage = getTemplate('wikipage.html')
        return wikipage("Upload", form, self._privileged())

    def POST(self):
        x = web.input(fileupload={})
        filedir =  self.repo.root + '/static/'

        import os
        if not os.path.exists(filedir):
            os.mkdir(filedir)

        # to check if the file-object is created
        if 'fileupload' in x:
            # replace the windows-style slashes with linux ones.
            filepath=x.fileupload.filename.replace('\\','/') 
            # split filepath the and choose the last part (the filename with extension)
            filename=filepath.split('/')[-1]
            # create the file where the uploaded file should be stored
            completepath = filedir +'/'+ filename
            fout = open(completepath, 'w')
            # write the uploaded file to the newly created file.
            fout.write(x.fileupload.file.read())
            # close the file, upload complete.
            fout.close()
            
            mercurial.commands.add(self.ui, self.repo, completepath)
            msg = "Uploaded " + filename + "."
            self._doCommit(msg)
            
        raise web.seeother('/')

class WikiConfig(WikiContent):
    def GET(self):
        pass

class Help(WikiContent):
    def GET(self):
        wikipage = getTemplate('wikipage.html')
        help = getTemplate('help.html')
        doc = help()
        return wikipage('Help', doc, self._privileged())
