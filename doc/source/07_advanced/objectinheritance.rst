.. _advanced/objectinheritance:




====================
 Object Inheritance
====================



Introduction
=============


This documentation attempts to explain object inheritance and how it can be used in your :ref:`object definitions <configuration/objectdefinitions>`.

If you are confused about how recursion and inheritance work after reading this, take a look at the sample object config files provided in the Shinken distribution. If that still doesn't help, have a look to the :ref:`shinken resources for help <contributing/how-to-contribute>`.



Basics
=======


There are three variables affecting recursion and inheritance that are present in all object definitions. They are indicated in red as follows...


::

  define someobjecttype{
         object-specific variables ...
         name            template_name
         use             name_of_template_to_use
         register        [0/1]
         }

The first variable is "name". Its just a "template" name that can be referenced in other object definitions so they can inherit the objects properties/variables. Template names must be unique amongst objects of the same type, so you can't have two or more host definitions that have "hosttemplate" as their template name.

The second variable is "use". This is where you specify the name of the template object that you want to inherit properties/variables from. The name you specify for this variable must be defined as another object's template named (using the name variable).

The third variable is "register". This variable is used to indicate whether or not the object definition should be "registered" with Shinken. By default, all object definitions are registered. If you are using a partial object definition as a template, you would want to prevent it from being registered (an example of this is provided later). Values are as follows: 0 = do NOT register object definition, 1 = register object definition (this is the default). This variable is NOT inherited; every (partial) object definition used as a template must explicitly set the "register" directive to be 0. This prevents the need to override an inherited "register" directive with a value of 1 for every object that should be registered.



Local Variables vs. Inherited Variables
========================================


One important thing to understand with inheritance is that “local" object variables always take precedence over variables defined in the template object. Take a look at the following example of two host definitions (not all required variables have been supplied):


::

  define host{
         host_name               bighost1
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         name                    hosttemplate1
         }

  define host{
         host_name               bighost2
         max_check_attempts      3
         use                     hosttemplate1
         }

You'll note that the definition for host *bighost1* has been defined as having *hosttemplate1* as its template name. The definition for host *bighost2* is using the definition of *bighost1* as its template object. Once Shinken processes this data, the resulting definition of host *bighost2* would be equivalent to this definition:


::

  define host{
         host_name               bighost2
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      3
         }

You can see that the "check_command" and "notification_options" variables were inherited from the template object (where host *bighost1* was defined). However, the *host_name* and *max_check_attempts* variables were not inherited from the template object because they were defined locally. Remember, locally defined variables override variables that would normally be inherited from a template object. That should be a fairly easy concept to understand.

If you would like local string variables to be appended to inherited string values, you can do so. Read more about how to accomplish this :ref:`below <advanced/objectinheritance#add_string>`.



Inheritance Chaining
=====================


Objects can inherit properties/variables from multiple levels of template objects. Take the following example:


::

  define host{
         host_name               bighost1
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         name                    hosttemplate1
         }

  define host{
         host_name               bighost2
         max_check_attempts      3
         use                     hosttemplate1
         name                    hosttemplate2
         }

  define host{
         host_name               bighost3
         use                     hosttemplate2
         }

You'll notice that the definition of host *bighost3* inherits variables from the definition of host *bighost2*, which in turn inherits variables from the definition of host *bighost1*. Once Shinken processes this configuration data, the resulting host definitions are equivalent to the following:


::

  define host{
         host_name               bighost1
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         }

  define host{
         host_name               bighost2
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      3
         }

  define host{
         host_name               bighost3
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      3
         }

There is no inherent limit on how “deep" inheritance can go, but you'll probably want to limit yourself to at most a few levels in order to maintain sanity.



Using Incomplete Object Definitions as Templates
=================================================


It is possible to use incomplete object definitions as templates for use by other object definitions. By "incomplete" definition, I mean that all required variables in the object have not been supplied in the object definition. It may sound odd to use incomplete definitions as templates, but it is in fact recommended that you use them. Why? Well, they can serve as a set of defaults for use in all other object definitions. Take the following example:


::

  define host{
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         name                    generichosttemplate
         register                        0
         }

  define host{
         host_name               bighost1
         address                 192.168.1.3
         use                     generichosttemplate
         }

  define host{
         host_name               bighost2
         address                 192.168.1.4
         use                     generichosttemplate
         }

Notice that the first host definition is incomplete because it is missing the required "host_name" variable. We don't need to supply a host name because we just want to use this definition as a generic host template. In order to prevent this definition from being registered with Shinken as a normal host, we set the "register" variable to 0.

The definitions of hosts *bighost1* and *bighost2* inherit their values from the generic host definition. The only variable we've chosed to override is the "address" variable. This means that both hosts will have the exact same properties, except for their "host_name" and "address" variables. Once Shinken processes the config data in the example, the resulting host definitions would be equivalent to specifying the following:


::

  define host{
         host_name               bighost1
         address                 192.168.1.3
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         }

  define host{
         host_name               bighost2
         address                 192.168.1.4
         check_command           check-host-alive
         notification_options    d,u,r
         max_check_attempts      5
         }

At the very least, using a template definition for default variables will save you a lot of typing. It'll also save you a lot of headaches later if you want to change the default values of variables for a large number of hosts.



Custom Object Variables
========================


Any :ref:`custom object variables <configuration/customobjectvars>` that you define in your host, service, or contact definition templates will be inherited just like other standard variables. Take the following example:


::

  define host{
         _customvar1             somevalue  ; <-- Custom host variable
         _snmp_community         public  ; <-- Custom host variable
         name                    generichosttemplate
         register                        0
         }

  define host{
         host_name               bighost1
         address                 192.168.1.3
         use                     generichosttemplate
         }

The host *bighost1* will inherit the custom host variables "_customvar1" and "_snmp_community", as well as their respective values, from the *generichosttemplate* definition. The effective result is a definition for *bighost1* that looks like this:


::

  define host{
         host_name               bighost1
         address                 192.168.1.3
         _customvar1             somevalue
         _snmp_community         public
         }



Cancelling Inheritance of String Values
========================================


In some cases you may not want your host, service, or contact definitions to inherit values of string variables from the templates they reference. If this is the case, you can specify **“null"** (without quotes) as the value of the variable that you do not want to inherit. Take the following example:


::

          define host{
                 event_handler           my-event-handler-command
                 name                    generichosttemplate
                 register                0
                 }

          define host{
                 host_name               bighost1
                 address                 192.168.1.3
                 event_handler           null
                 use                     generichosttemplate
                 }

In this case, the host *bighost1* will not inherit the value of the "event_handler" variable that is defined in the *generichosttemplate*. The resulting effective definition of *bighost1* is the following:


::

          define host{
                 host_name               bighost1
                 address                 192.168.1.3
                 }



.. _advanced/objectinheritance#add_string:

Additive Inheritance of String Values
======================================


Shinken gives preference to local variables instead of values inherited from templates. In most cases local variable values override those that are defined in templates. In some cases it makes sense to allow Shinken to use the values of inherited and local variables together.

This "additive inheritance" can be accomplished by prepending the local variable value with a plus sign (+). This features is only available for standard (non-custom) variables that contain string values. Take the following example:


::

  define host{
         hostgroups              all-servers
         name                    generichosttemplate
         register                0
         }

  define host{
         host_name              linuxserver1
         hostgroups             +linux-servers,web-servers
         use                    generichosttemplate
         }

In this case, the host *linuxserver1* will append the value of its local "hostgroups" variable to that from generichosttemplate. The resulting effective definition of *linuxserver1* is the following:


::

  define host{
         host_name              linuxserver1
         hostgroups             all-servers,linux-servers,web-servers
         }

.. important::  If you use a field twice using several templates, the value of the field will be the first one found!
   In the example above, fields values in all-servers won't we be replaced. Be careful with overlaping field!



Implied Inheritance
====================


Normally you have to either explicitly specify the value of a required variable in an object definition or inherit it from a template. There are a few exceptions to this rule, where Shinken will assume that you want to use a value that instead comes from a related object. For example, the values of some service variables will be copied from the host the service is associated with if you don't otherwise specify them.

The following table lists the object variables that will be implicitly inherited from related objects if you don't explicitly specify their value in your object definition or inherit them from a template.



======================= ============================================================ =====================================================
Object Type             Object Variable                                              Implied Source
**Services**            *contact_groups*                                             *contact_groups* in the associated host definition
*notification_interval* *notification_interval* in the associated host definition
*notification_period*   *notification_period* in the associated host definition
*check_period*          *check_period* in the associated host definition
**Host Escalations**    *contact_groups*                                             *contact_groups* in the associated host definition
*notification_interval* *notification_interval* in the associated host definition
*escalation_period*     *notification_period* in the associated host definition
**Service Escalations** *contact_groups*                                             *contact_groups* in the associated service definition
*notification_interval* *notification_interval* in the associated service definition
*escalation_period*     *notification_period* in the associated service definition
======================= ============================================================ =====================================================



Implied/Additive Inheritance in Escalations
============================================


Service and host escalation definitions can make use of a special rule that combines the features of implied and additive inheritance. If escalations 1) do not inherit the values of their "contact_groups" or "contacts" directives from another escalation template and 2) their "contact_groups" or "contacts" directives begin with a plus sign (+), then the values of their corresponding host or service definition's "contact_groups" or "contacts" directives will be used in the additive inheritance logic.

Confused? Here's an example:


::

  define host{
         name                    linux-server
         contact_groups          linux-admins
         ...
         }

  define hostescalation{
         host_name               linux-server
         contact_groups          +management
         ...
         }

This is a much simpler equivalent to:


::

  define hostescalation{
         host_name               linux-server
         contact_groups          linux-admins,management
         ...
         }



Multiple Inheritance Sources
=============================


Thus far, all examples of inheritance have shown object definitions inheriting variables/values from just a single source. You are also able to inherit variables/values from multiple sources for more complex configurations, as shown below.


::

  # Generic host template

  define host{
         name                    generic-host
         active_checks_enabled   1
         check_interval          10
         register                0
         }


::

  # Development web server template
  define host{
         name                    development-server
         check_interval          15
         notification_options    d,u,r
         ...
         register                0
         }


::

  # Development web server
  define host{
         use                    generic-host,development-server
         host_name              devweb1
         ...
         }



.. image:: /_static/images///official/images/multiple-templates1.png
   :scale: 90 %



In the example above, devweb1 is inheriting variables/values from two sources: generic-host and development-server. You'll notice that a check_interval variable is defined in both sources. Since generic-host was the first template specified in devweb1's use directive, its value for the "check_interval" variable is inherited by the devweb1 host. After inheritance, the effective definition of devweb1 would be as follows:



::

  # Development web serve
  define host{
         host_name               devweb1
         active_checks_enabled   1
         check_interval          10
         notification_options    d,u,r
         ...
         }



Precedence With Multiple Inheritance Sources
=============================================


When you use multiple inheritance sources, it is important to know how Shinken handles variables that are defined in multiple sources. In these cases Shinken will use the variable/value from the first source that is specified in the use directive. Since inheritance sources can themselves inherit variables/values from one or more other sources, it can get tricky to figure out what variable/value pairs take precedence.



Consider the following host definition that references three templates:

::

  # Development web server
  define host{
         use        1, 4, 8
         host_name  devweb1
         ...
  }

If some of those referenced templates themselves inherit variables/values from one or more other templates, the precendence rules are shown below. Testing, trial, and error will help you better understand exactly how things work in complex inheritance situations like this. :-)

.. image:: /_static/images///official/images/multiple-templates2.png
   :scale: 90 %



Inheritance overriding
=======================


Inheritance is a core feature allowing to factorize configuration. It is possible from a host or a service template to build a very large set of checks with relatively few lines. The drawback of this approach is that it requires all hosts or services to be consistent. But if it is easy to instanciate new hosts with their own definitions attributes sets, it is generally more complicated with services, because the order of magnitude is larger (hosts * services per host), and because few attributes may come from the host. This is is especially true for packs, which is a generalization of the inheritance usage.

If some hosts require special directives for the services they are hosting (values that are different from those defined at template level), it is generally necessary to define new service.

Imagine two web servers clusters, one for the frontend, the other for the backend, where the frontend servers should notify any HTTP service in ``CRITICAL`` and ``WARNING`` state, and backend servers should only notify on ``CRITICAL`` state.

To implement this configuration, we may define 2 different HTTP services with different notification options.

Example:

::

  define service {
         service_description     HTTP Front
         hostgroup_name          front-web
         notification_options    c,w,r
              ...
  }

  define service {
         service_description     HTTP Back
         hostgroup_name          front-back
         notification_options    c,r
            ...
  }

  define host {
         host_name               web-front-01
         hostgroups              web-front
         ...
  }
  ...

  define host {
         host_name               web-back-01
         hostgroups              web-back
         ...
  }
  ...


Another way is to inherit attributes on the service side directly from the host: some service attributes may be inherited directly from the host if not defined on the service template side (see `Implied Inheritance`_), but not all. Our ``notification_options`` in our example cannot be picked up from the host.

If the attribute you want to be set a custom value cannot be inherited from the host, you may use the ``service_overrides`` host directive. Its role is to enforce a service directive directly from the host. This allows to define specific service instance attributes from a same generalized service definition.

Its syntax is:

::

  service_overrides xxx,yyy zzz

It could be summarized as "*For the service bound to me, named ``xxx``, I want the directive ``yyy`` set to ``zzz`` rather tran the inherited value*"

The service description selector (represented by ``xxx`` in the previous example) may be:

A service name (default)
  The ``service_description`` of one of the services attached to the host.

``*`` (wildcard)
  Means *all the services attached to the host*

A regular expression
  A regular expression against the ``service_description`` of the services attached to the host (it has to be prefixed by ``r:``).


Example:

::

  define service {
         service_description     HTTP
         hostgroup_name          web
         notification_options    c,w,r
         ...
  }

  define host {
         host_name               web-front-01
         hostgroups              web
         ...
  }
  ...

  define host {
         host_name               web-back-01
         hostgroups              web
         service_overrides       HTTP,notification_options c,r
         ...
  }
  ...
  define host {
         host_name               web-back-02
         hostgroups              web
         service_overrides       *,notification_options c
         ...
  }
  ...
  define host {
         host_name               web-back-03
         hostgroups              web
         service_overrides       r:^HTTP,notification_options r
         ...
  }
  ...

In the previous example, we defined only one instance of the HTTP service, and we enforced the service ``notification_options`` for some web servers composing the backend. The final result is the same, but the second example is shorter, and does not require the second service definition.

Using packs allows an even shorter configuration.

Example:

::

  define host {
         use                     http
         host_name               web-front-01
         ...
  }
  ...

  define host {
         use                     http
         host_name               web-back-01
         service_overrides       HTTP,notification_options c,r
         ...
  }
  ...
  define host {
         use                     http
         host_name               web-back-02
         service_overrides       HTTP,notification_options c
         ...
  }
  ...
  define host {
         use                     http
         host_name               web-back-03
         service_overrides       HTTP,notification_options r
         ...
  }
  ...

In the packs example, the web server from the front-end cluster uses the value defined in the pack, and the one from the backend cluster has its HTTP service (inherited from the HTTP pack also) enforced its ``notification_options`` directive.

.. important:: The service_overrides attribute may himself be inherited from an upper host template. This is a multivalued attribute wchich syntax requires that each value is set on its own line. If you add a line on a host instance, it will not add it to the ones defined at template level, it will overlobad them. If some of the values on the template level are needed, they have to be explicitely copied.

Example:

::

  define host {
         name                    web-front
         service_overrides       HTTP,notification_options c,r
         ...
         register                0
  }
  ...

  define host {
         use                     web-fromt
         host_name               web-back-01
         hostgroups              web
         service_overrides       HTTP,notification_options c,r
         service_overrides       HTTP,notification_interval 15
         ...
  }
  ...



Inheritance exclusions
=======================

Packs and hostgroups allow de factorize the configuration and greatly reduce the amount of configuration to write to describe infrastructures. The drawback is that it forces hosts to be consistent, as the same configuration is applied to a possibly very large set of machines.

Imagine a web servers cluster. All machines except one should be checked its managenent interface (ILO, iDRAC). In the cluster, there is one virtual server that should be checked the exact same services than the others, except the management interface (as checking it on a virtual server has no meaning). The corresponding service comes from a pack.

In this situation, there is several ways to manage the situation:

- create in intermadiary template on the pack level to have the management interface check attached to an upper level template

- re define all the services for the specifed host.

- use service overrides to set a dummy command on the corresponding service.

None of these options are satisfying.

There is a last solution that consists of excluding the corresponding service from the specified host. This may be done using the ``service_excludes`` directive.

Its syntax is:

::

  service_excludes xxx

The service description selector (represented by ``xxx`` in the previous example) may be:

A service name (default)
  The ``service_description`` of one of the services attached to the host.

``*`` (wildcard)
  Means *all the services attached to the host*

A regular expression
  A regular expression against the ``service_description`` of the services attached to the host (it has to be prefixed by ``r:``).

Example:


::

  define host {
         use                     web-front
         host_name               web-back-01
         ...
  }

  define host {
         use                     web-front
         host_name               web-back-02    ; The virtual server
         service_excludes        Management interface
         ...
  }
  ...
  define host {
         use                     web-front
         host_name               web-back-03    ; The virtual server
         service_excludes        *
         ...
  }
  ...
  define host {
         use                     web-front
         host_name               web-back-04    ; The virtual server
         service_excludes        r^Management
         ...
  }
  ...


In the case you want the opposite (exclude all except) you can use the ``service_includes`` directive which is its corollary.
