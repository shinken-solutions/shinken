For Developers
==================

Here is a way to setup a shinken in "raw mode" without installing it really:

Install
-------
After unpacking the tarball move the shinken directory to the desired destination
and give it to the shinken user::

	mv shinken /usr/local
	chown -R shinken:shinken /usr/local/shinken

Update / Remove
---------------
Just remove your shinken directory
	rm -rf /usr/local/shinken

Running
-------
It's easy, there is already a launch script for you::

  shinken/bin/launch_all_debug.sh

It will generate some /tmp/*debug files that you can use to debug the code :)


WebUI / Skonf
-------------
Branch: module-webui*

* If you find a bug or have feature requests for us, please go to GitHub an Open an issue. Don't forget to label it (WebUI/Skonf)!

* If you have a pull request for us, please choose the develop-webui branch as destination.

	Maintained by Andreas Karfusehr, Jean Gabès