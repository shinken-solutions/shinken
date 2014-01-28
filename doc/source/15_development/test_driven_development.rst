.. _test_driven_development:


=======================
Test Driven Development
=======================

Introduction
============

Test Driven Development
-----------------------

In a strict sense TDD is: 
  * Create the test case for your new function (valid and invalid input, limits, expected output)
  * Run the test, make sure it fails as planned.
  * Code your function, run the test against it and eventually have it succeed. 
  * Once the function works, re-factor the code for efficiency, readability, comments, logging and anything else required. 
  * Any scope changes should be handled by new functions, by adding new test cases or by modifying the existing test case (dangerous for existing code). 
  * See the ` Wikipedia article about TDD`_ for more information.

There are different test levels : 
  * Commit level tests : These should be as quick as possible, so everyone can launch them in a few seconds. 
  * Integration tests : Integration tests should be more extensive and can have longer execution periods as these are launched less often (before a release, or in an integration server).




TDD in Shinken
--------------

We think all functions and features should have a test case. Shinken has a system to run automated tests that pinpoint any issues. This is used prior to commit, at regular intervals and when preparing a release.

Shinken uses Test Driven Development to achieve agility and stability in its software development process. Developers must adhere to the described methods in order to maintain a high quality standard.

We know some functions will be hard to test (databases for example), so let's do our best, we can't have 100% coverage. Tests should cover the various input and expected output of a function. Tests can also cover end-to-end cases for performance, stability and features. Test can also be classified in their time to run, quick tests for commit level validation and integration tests that go in-depth.

We are not saying "all patches should be sent with tests", but new features/functions should have tests. First, the submitter knows what his code is designed to do, second this will save us from having to create one or more test cases later on when something gets broken. Test examples can be found in the /tests/ directory of the repository or your local installation.



Add test to Shinken
===================

I guess you have come here to chew bubblegum and create tests ... and you are all out of bubblegum! Lucky you are, here is some help to create tests!



Create a test
-------------

Tests use standard python tools to run (unittest), so that they have to be well formatted. But don't worry it's quite simple. All you have to know is something (a class or a method) containing the "test" string will be run. The typical way to create a new test is to copy paste from a simple one. We suggest the test_bad_contact_call.py for example which is very small.

Here is the file : 

  
::

  from shinken_test import *
  
  class TestConfig(ShinkenTest):
  
      def setUp(self):
          self.setup_with_file('etc/nagios_bad_contact_call.cfg')
  
      def test_bad_contact_call(self):
          # The service got a unknow contact. It should raise an error
          svc = self.conf.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
          print "Contacts:", svc.contacts
          self.assert_(svc.is_correct() == False)
  
  if __name__ == '__main__':
      unittest.main()
  
  
Basically what unittest does (and nosetest too) is run every method containing "test" in all class containing "test". Here there is only one test : test_bad_contact_call
The setUp function is a special one : it is called before every test method to set up the test. You can also execute a special function after each test by defining a tearDown() method.

So the only thing you have to do is rename the function and write whatever you want to test inside! 

This is more or less the only thing you have to do if you want to write a test from scratch. See http://docs.python.org/2/library/unittest.html for more detail about unittest

If you are testing more complex stuff you may use other test as template. For example broker module tests are a lot different and need some scheduling statement to simulate real beahvior.



Executing tests 
----------------


.. important::  YOU NEED PYTHON 2.7 TO RUN THE TESTS. The test scripts use new Assert statements only available starting in Python 2.7.

Once you have done or edited the python file you have to run the test by typing :
  
::

   python test_nameofyourtest.py
   
If there is no error then everything is correct. You can try to launch it with nosetests to double check it. 

.. note::   nosetests has a different behavior than unittests, the jenkins integration is using nosetests, that's why it's a good thing to check before comminting.

The automated tests permit developers to concentrate on what they do best, while making sure they don't break anything. That's why the tests are critical to the success of the project. Shinken aims for "baseline zero bug" code and failure by design development :)
We all create bugs, it's the coders life after all, lets at least catch them before they create havoc for users! The automated tests handle regression, performance, stability, new features and edge cases.

The test is ready for commit. The last thing to do is to run the test suit to ensure you do not create code regression. This can be a long step if you have made a big change.



Shell test run 
---------------

There are basically two ways to run the test list. The first one (easiest) is to run the quick_test shell script. This will basically iterate on a bunch of python files and run them

FIXME : update test list into git and edit end to end script
  
::

  ./quick_tests.sh 
  
Then you can run the end to end one : \\
FIXME : explain what the script does
  
::

  ./test_end_to_end.sh 
  
It only takes a few seconds to run and you know that you did not break anything (or this will indicate you should run the in-depth integration level tests :) ).

If you are adhering to TDD this will validate that your function fails by design or that you have successfully built your function




Integration test run 
---------------------


The other way to do it is run the new_runtest script (which is run on the Jenkins ingration server)

.. note::   It can be difficult to make it work from scratch as the script create and install a python virtual enviromnt. On the distros, pip dependencies may be difficult to met. Don't give up and ask help on the mailing list! 

  
::

   ./test/jenkins/new_runtest ./test/jenkins/shorttests.txt ./test/moduleslist COVERAGE PYLINT PEP8
  
  
For short tests, coverage and python checking. Just put NOCOVERAGE or NOPYLINT or NOPEP8 instead to remove one.

This ensure that the Jenkins run won't fail. It's the best way to keep tests fine. 



Tests and integration servers 
------------------------------


The integration server is at http://shinken-monitoring.de:8080/

It use the following tests:

* test/jenkins/runtests[.bat]
   it takes the arguments: "file with a list of test_-scripts" [NO]COVERAGE
[NO]PYLINT
* test/test_end_to_end.sh


Other integration server is at https://test.savoirfairelinux.com/view/Shinken/

This one use the new_runtest script.



Automated test execution 
-------------------------


The Hudson automated test jobs are:

 * Shinken
  * executed after each git commit
  * runtests test/jenkins/shorttests.txt NOCOVERAGE NOPYLINT
  * the scripts in shorttests.txt take a few minutes to run
  * give the developer feedback as fast as possible (**nobody should git-commit without running tests in his private environment first**)

 * Shinken-Multiplatform
  * runs 4 times per day
  * runtests test/jenkins/longtests.txt NOCOVERAGE NOPYLINT
  * linux-python-2.4,linux-python-2.6,linux-python-2.7,windows-python-2.7
  * executes _all_ test_-scripts we have, so it takes a long time

 * Shinken-End-to-End
  * runs after each successful Shinken-Multiplatform
  * executes the test/test_end_to_end.sh script
  * try a direct launch, install then launch, and high availability environment launch.

 * Shinken-Code-Quality
  * runs once a day
  * runtests test/jenkins/longtests.txt COVERAGE PYLINT
  * collects metrics for coverage and pylint

On the Jenkins one : 

 * Shinken-Upstream-Commit-Short-Tests 	 
  * executed after each git commit
  * ./test/jenkins/new_runtests ./test/jenkins/shorttests.txt ./test/moodulelist COVERAGE PYLINT PEP8
  * test also module in a basic way.
  * the scripts in shorttests.txt take a few minutes to run
  * give the developer feedback as fast as possible (**nobody should git-commit without running tests in his private environment first**)

 * Shinken-Upstream-Daily-Full-Tests 
  * executed every 6 hours
  * ./test/jenkins/new_runtest ./test/jenkins/all_tests.txt ./test/moduleslist COVERAGE PYLINT PEP8
  * the all_test is regenerated everytime (all test_*.py)
  * run all test in all module listed
  * give a full view of shinken coverage.

.. _ Wikipedia article about TDD: http://en.wikipedia.org/wiki/Test-driven_development
