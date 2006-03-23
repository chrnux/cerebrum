Installation instructions for Cereweb (Cerebrum web interface)
==============================================================

Requirements
============

* Python 2.2 or newer

* omniORB

* Cheetah 1.0
  http://www.cheetahtemplate.org/

* CherryPy 2.1
  http://www.cherrypy.org/

* forgetHTML
  http://forgethtml.sourceforge.net/

Install
=======
Run "./configure" from your cerebrum cvs-root to generate makefiles.

Run "make" or "gmake" in your cereweb directory to generate css and python
files from the cheetah templates.

Run "python cereweb.py" from your cereweb directory to start the server.

Configuration
=============

cherrypy.conf
* configurartion for cherrypy

cereweb.conf
* configuration for cereweb

..
   arch-tag: db563948-ba6f-11da-9e2e-bb4ae4157da0
