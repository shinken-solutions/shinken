.. _programming_rules:



Shinken Programming Guidelines 
-------------------------------


The Shinken project aims to have good code quality. This is to the benefit of all. Easy to understand code, that is efficient and well documented can do wonders to introduce new developers to a great system and keep existing one happy!

During scores of secret meetings at undisclosed locations in the heart of Eurodisney, the following guidelines were documented.

So here's the how to keep the developers happy! **__Follow these guidelines__**



The python style guide 
~~~~~~~~~~~~~~~~~~~~~~~


The python style guide provides coding conventions for Python programmers covering topics such as:

  * Whitespace
  * Comments
  * Imports
  * Classes
  * Naming conventions

Keep it as a handy reference: ` PEP8 - Python Style guide`_



Reference book 
~~~~~~~~~~~~~~~


The Art of Readable Code, is a great book that provides a fast read and an immense value in improving the readability and maintainability of code.



Pyro remote Object Library 
~~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken uses Pyro extensively to create its cloud-like architecture.:ref:`You can learn more about Pyro <//pypi.python.org/pypi/Pyro4>` if you wish to develop new features that need to use inter-process communications.



The python docstring guide 
~~~~~~~~~~~~~~~~~~~~~~~~~~~


The Python docstring guide provides insight in how to format and declare *docstrings* which are used to document classes and functions.

Read through it to provide better understanding for yourself and others: ` Python docstring guide`_




Logging is your friend 
~~~~~~~~~~~~~~~~~~~~~~~


Shinken provides a logger module, that acts as a wrapper to the Python logging facilities. This provides valuable feedback to users, power users and developers.

The logging functions also provide different levels to distinguish the type logging level at which the messages should appear. This is similar to how syslog classifies messages based on severity levels.

Some log messages will not get the level printed, these are related to state data.
Logging levels for logs generated at system startup and displayed in STDOUT are set by default to display all messages. This is normal behaviour. Once logging is initialized buffered messages are logged to the appropriate level defined in the daemon INI files. (ex. reactionnerd.ini, brokerd.ini, etc.)

Some test cases depend on logging output, so change existing logging messages to your hearts content, but validate all changes against the FULL test suite. :ref:`Learn more about using the Shinken test suite <test_driven_development>`.

**Debug:**
This is the most verbose logging level (maximum volume setting). Consider Debug to be out-of-bounds for a production system and used it only for development and testing. I prefer to aim to get my logging levels just right so I have just enough information and endeavor to log this at the Information level or above.

**Information:**
The Information level is typically used to output information that is useful to the running and management of your system. Information would also be the level used to log Entry and Exit points in key areas of your application. However, you may choose to add more entry and exit points at Debug level for more granularity during development and testing.

**Warning:**
Warning is often used for handled 'exceptions' or other important log events. For example, if your application requires a configuration setting but has a default in case the setting is missing, then the Warning level should be used to log the missing configuration setting.

**Error:**
Error is used to log all unhandled exceptions. This is typically logged inside a catch block at the boundary of your application.

**Critical:**
Critical is reserved for special exceptions/conditions where it is imperative that you can quickly pick out these events. I normally wouldn't expect Fatal to be used early in an application's development. It's usually only with experience I can identify situations worthy of the FATAL moniker experience do specific events become worth of promotion to Critical. After all, an error's an error.

**log:**
This level has been deprecated for NON NAGIOS/SHINKEN STATE messages and should be replaced with one of the approved logging levels listed above. The STATE messages are easy recognize as they are ALL CAPS. Do not mess with these unless you know what you are doing.



Technical debt must be paid 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Coding in Shinken should be fun and rewarding.

"Technical debt": all little hacks here and there. __There comes a time, technical debt must be paid__. We can have new features very quickly, if authors do not have to bypass numerous hack. We must take some time before each release to pay all technical debt we can. __The less we've got, the easier it is to service and extend the code__.

It's the same for the core architecture. A solid and stable architecture allows developers to build on it and add value. A good example is being able to add a parameter with only a single line :)

We must be responsible with new features, if it means they can be used to build more innovation in the future without hacks :)



Where does the fun happen 
~~~~~~~~~~~~~~~~~~~~~~~~~~


` GitHub offers great facilities to fork, test, commit, review and comment anything related to Shinken`_. 

You can also follow the project progress in real time.
.. _ GitHub offers great facilities to fork, test, commit, review and comment anything related to Shinken: https://github.com/naparuba/shinken 
.. _ Python docstring guide: http://www.python.org/dev/peps/pep-0257/ 
.. _ PEP8 - Python Style guide: http://www.python.org/dev/peps/pep-0008/ 