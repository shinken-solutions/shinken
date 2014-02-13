.. _securityandperformancetuning-security:




=========================
 Security Considerations 
=========================



Introduction 
=============




.. image:: /_static/images///official/images/security.png
   :scale: 90 %

 This is intended to be a brief overview of some things you should keep in mind when installing Nagios, so as set it up in a secure manner.

Your monitoring box should be viewed as a backdoor into your other systems. In many cases, the Nagios server might be allowed access through firewalls in order to monitor remote servers. In most all cases, it is allowed to query those remote servers for various information. Monitoring servers are always given a certain level of trust in order to query remote systems. This presents a potential attacker with an attractive backdoor to your systems. An attacker might have an easier time getting into your other systems if they compromise the monitoring server first. This is particularly true if you are making use of shared "SSH" keys in order to monitor remote systems.

If an intruder has the ability to submit check results or external commands to the Nagios daemon, they have the potential to submit bogus monitoring data, drive you nuts you with bogus notifications, or cause event handler scripts to be triggered. If you have event handler scripts that restart services, cycle power, etc. this could be particularly problematic.

Another area of concern is the ability for intruders to sniff monitoring data (status information) as it comes across the wire. If communication channels are not encrypted, attackers can gain valuable information by watching your monitoring information. Take as an example the following situation: An attacker captures monitoring data on the wire over a period of time and analyzes the typical CPU and disk load usage of your systems, along with the number of users that are typically logged into them. The attacker is then able to determine the best time to compromise a system and use its resources (CPU, etc.) without being noticed.

Here are some tips to help ensure that you keep your systems secure when implementing a Nagios-based monitoring solution...



Best Practices 
===============


  - **Use a Dedicated Monitoring Box**. I would recommend that you install Nagios on a server that is dedicated to monitoring (and possibly other admin tasks). Protect your monitoring server as if it were one of the most important servers on your network. Keep running services to a minimum and lock down access to it via TCP wrappers, firewalls, etc. Since the Nagios server is allowed to talk to your servers and may be able to poke through your firewalls, allowing users access to your monitoring server can be a security risk. Remember, its always easier to gain root access through a system security hole if you have a local account on a box.

.. image:: /_static/images///official/images/security3.png
   :scale: 90 %


  - **Don't Run Nagios As Root**. Nagios doesn't need to run as root, so don't do it. You can tell Nagios to drop privileges after startup and run as another user/group by using the :ref:`nagios_user <configuringshinken-configmain#configuringshinken-configmain-nagios_user>` and :ref:`nagios_group <configuringshinken-configmain#configuringshinken-configmain-nagios_group>` directives in the main config file. If you need to execute event handlers or plugins which require root access, you might want to try using `sudo`_.
  - **Lock Down The Check Result Directory**. Make sure that only the nagios user is able to read/write in the :ref:`check result path <configuringshinken-configmain#configuringshinken-configmain-check_result_path>`. If users other than nagios (or root) are able to write to this directory, they could send fake host/service check results to the Nagios daemon. This could result in annoyances (bogus notifications) or security problems (event handlers being kicked off).
  - **Lock Down The External Command File**. If you enable :ref:`External Commands <advancedtopics-extcommands>`external commands, make sure you set proper permissions on the "/usr/local/nagios/var/rw directory". You only want the Nagios user (usually nagios) and the web server user (usually nobody, httpd, apache2, or www-data) to have permissions to write to the command file. If you've installed Nagios on a machine that is dedicated to monitoring and admin tasks and is not used for public accounts, that should be fine. If you've installed it on a public or multi-user machine (not recommended), allowing the web server user to have write access to the command file can be a security problem. After all, you don't want just any user on your system controlling Nagios through the external command file. In this case, I would suggest only granting write access on the command file to the nagios user and using something like `CGIWrap`_ to run the CGIs as the nagios user instead of nobody.
  - **Use Full Paths In Command Definitions**. When you define commands, make sure you specify the full path (not a relative one) to any scripts or binaries you're executing.
  - **Hide Sensitive Information With "$USERn$" Macros**. The CGIs read the :ref:`Main Configuration File Options <configuringshinken-configmain>`main config file and :ref:`Object Configuration Overview <configuringshinken-configobject>`Object config file(s), so you don't want to keep any sensitive information (usernames, passwords, etc) in there. If you need to specify a username and/or password in a command definition use a "$USERn$" :ref:`Understanding Macros and How They Work <thebasics-macros>`macro to hide it. "$USERn$" macros are defined in one or more :ref:`resource files <configuringshinken-configmain#configuringshinken-configmain-resource_file>`. The CGIs will not attempt to read the contents of resource files, so you can set more restrictive permissions (600 or 660) on them. See the sample "resource.cfg" file in the base of the Nagios distribution for an example of how to define $USERn$ macros.
  - **Strip Dangerous Characters From Macros**. Use the :ref:`illegal_macro_output_chars <configuringshinken-configmain#configuringshinken-configmain-illegal_macro_output_chars>` directive to strip dangerous characters from the "$HOSTOUTPUT$", "$SERVICEOUTPUT$", "$HOSTPERFDATA$", and "$SERVICEPERFDATA$" macros before they're used in notifications, etc. Dangerous characters can be anything that might be interpreted by the shell, thereby opening a security hole. An example of this is the presence of backtick (`) characters in the "$HOSTOUTPUT$", "$SERVICEOUTPUT$", "$HOSTPERFDATA$", and/or "$SERVICEPERFDATA$" macros, which could allow an attacker to execute an arbitrary command as the nagios user (one good reason not to run Nagios as the root user).
  - **Secure Access to Remote Agents**. Make sure you lock down access to agents (NRPE, NSClient, "SNMP", etc.) on remote systems using firewalls, access lists, etc. You don't want everyone to be able to query your systems for status information. This information could be used by an attacker to execute remote event handler scripts or to determine the best times to go unnoticed.

.. image:: /_static/images///official/images/security1.png
   :scale: 90 %


  - **Secure Communication Channels**. Make sure you encrypt communication channels between different Nagios installations and between your Nagios servers and your monitoring agents whenever possible. You don't want someone to be able to sniff status information going across your network. This information could be used by an attacker to determine the best times to go unnoticed.

.. image:: /_static/images///official/images/security2.png
   :scale: 90 %




.. _sudo: http://www.courtesan.com/sudo/sudo
.. _CGIWrap: http://cgiwrap.sourceforge.net/