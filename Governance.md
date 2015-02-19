# Project vision and Governance


## Project Vision

The project targeted admin sake, and especially the large IT environments. It has been launched and mainly enhanced by administrators. They are and will remain the main focus of this project.

It is meant to be easy to maintain, testable, extensible and hackable by its main users. 

The framework should ease the setup of global solution built by linking together configuration management tools (Chef/Puppet/Glpi and so on...), metrology tools (Graphite/Pnp4angios/Influxdb) and service discovery tools (Kunai/Consul/Etcd/...).

Its installation should be as easy as possible.

Features should not be set in stone. If a feature usage is too limited, hard to use or maintain, or a monitoring community tool is doing better with an easier solution, we should deprecate it and remove it.

If possible, features should be exported into modules rather than introduced into the core in order to reduce its size and enhance its maintenability for everyone.

Code simplicity and efficiency should always be preferred to "purity" code (a bit like in the Python Zen). If a code does not add any user value or a truly verified maintenance enhancement in the long term, it won't be in the scope of the project. [Over Engineered](http://en.wikipedia.org/wiki/Overengineering) code and features should be avoided (and removed if found), as it raises the entry level for new coders without adding real user value.


Below are described the rule leading patches integration priority:

   Bug fix > Feature > Refactoring


## Release cycle

The project will follow a fixed release cycle of 3 months. It is the project leader responsibility to find code name (a stupid one, like in the past, if possible ^^). Each cycle will be split into 3 phases:

   * refactoring and technical dept paid
   * features
   * freeze, so bug fix only

Features and enhancements proposed during the freeze period should be kept as pull requests. Bug fix should always be accepted what ever the cycle.


## Governance

Everyone is welcome to participate, assuming project vision and governance rules agreement.

The project leader is the referent of the project vision, governance and code quality and efficiency. 

This text is to be accepted by all contributors and will be the reference regarding the project future evolutions.
