# Overview #

hgwiki is an extension to mercurial that provides a new command: hg wiki.  This command starts a web server that exposes the contents of your mercurial repository as a wiki -- a collection of web pages that can be edited in a browser.

## Status ##
hgwiki is under active development, and I am currently following the "release early, release often" model, so there are bugs and it is not at all feature complete.  Comments and patches are welcome!

# Distributed Wiki? #

Normal wikis are hosted on servers somewhere on a network, through which clients may connect to them, and that is really the only way to access their contents.

hgwiki is a distributed wiki, in the same way that Mercurial is distributed revision control; that is, every user that can edit the wiki has a complete copy of the entire wiki's contents, and can edit the wiki through their browser even when they are not online.  Users can then sync their changes using normal Mercurial commands, like `hg pull` and `hg push`.

# Features #

What makes this approach useful?

  * The wiki is just a Mercurial repository, so your data is accessible as a collection of text files
  * The server is part of the mercurial extension, so you can use the wiki even if you are offline, and operations occur very quickly
  * hgwiki can be embedded in a Mercurial repository, so end users don't need to have anything more than Python and Mercurial on their system for it to work
  * All transformation of markup occurs on-the-fly, so you don't have to store separate versions to be served

# Getting Started #

  * Prerequisites
    * **For Windows**:
      * Install Python 2.6 from http://python.org (hgwiki has not yet been tested with Python 3.x)
      * Install Mercurial from http://selenic.com/mercurial
      * See note below if you installed Python in a location other than `C:\Python26`
    * **For OS X**:
      * Install Mercurial using either Macports, Fink, Homebrew or directly from http://selenic.com/mercurial
    * **For GNU/Linux**:
      * Use your package manager to install Mercurial
        * e.g. `sudo apt-get install mercurial`
        * e.g. `sudo yum install mercurial`
  * To install, check out or download a tarball of the current version
    * e.g. `hg clone https://hgwiki.googlecode.com/hg/ hgwiki`
  * Modify your `.hgrc` or `mercurial.ini` file:
```
   [extensions]
   hgwiki=/path/to/hgwiki/directory/hgwiki
```
  * Create a new Mercurial repository and run `hg wiki`:
```
   mkdir mywiki
   cd mywiki
   hg init
   hg wiki
```
  * Visit http://localhost:8080 in your browser, and start editing your wiki
  * The wiki uses [reStructuredText](http://docutils.sourceforge.net/rst.html) -- a [quick start guide](http://docutils.sourceforge.net/docs/user/rst/quickstart.html) is available, as is a more comprehensive [user reference](http://docutils.sourceforge.net/docs/user/rst/quickref.html).

## Note for users of Microsoft Windows ##

If you install Mercurial using the default Windows installer from the Mercurial website, it will install its own, stripped down, version of Python that lacks some of the libraries necessary to make hgwiki work.  To fix this:
  * Download Python 2.6 from http://python.org
  * Install it (it should be installed in C:\python26)
  * Open `hgwiki/__init__.py`and make sure that the location where you installed it is present in that file around line 44, with the `\\lib` directory following it.  The line should look something like this, with the path Python was installed to in place of the `C:\\Python26`:
> > `sys.path.append("C:\\Python26\\lib")`

There is an outstanding work item to automate this, but we're not there yet.

# Credit Where Credit is Due #

hgwiki is a mashup of a variety of very cool projects:

  * Mercurial (http://selenic.com/mercurial)
  * Aaron Swartz's webpy web framework (http://webpy.org)
  * The DocUtils package, providing reStucturedText markup for the wiki (http://docutils.sourceforge.net/)
  * The Dojo Toolkit, providing easy web UI primitives (http://dojotoolkit.org)
  * PyTextile, as a prototyping/backup markup engine (http://code.google.com/p/pytextile/)

# Related Projects #

Wikis backed by distributed revision control systems are not my idea (though I am a fan of the idea!)  There are several other (older, more mature) projects that provide similar functionality to hgwiki that are worth your attention if you find the idea interesting.  With the exception of Fossil SCM, none of these seem to focus on the distributed aspect of a wiki (no central site hosting the "canonical" copy), which is why I created hgwiki.

[ikiwiki](http://ikiwiki.info/) may be one of the most well known, supporting several revision control backends and compiling files to HTML to be served statically.

[Fossil SCM](http://fossil-scm.org/index.html/doc/tip/www/index.wiki) provides a revision control system rolled up with issue tracking and a wiki in a cross-platform ~300kb exectuable written in C.

[Gitit](http://github.com/jgm/gitit) is a highly modular, mature wiki engine supporting a variety of revision control backends, markup languages, and export options.