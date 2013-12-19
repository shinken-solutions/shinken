.. _the_project_vision:



The project Vision 
-------------------




What we want and how we want it 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


We are here to create an open source monitoring solution that is:

  - easy to install;
  - easy to use for new users;
  - useful for sysadmins and business types;
  - built for scalability;
  - incorporates high availability;
  - multi-platform (and not just Unix ones);
  - utf8 compliant;
  - nearly fully compatible with Nagios configuration;
  - fully compatible with its plugins and interfaces;
  - fast enough
  - centralized configuration that should be as easy as possible for the admin to manage;
  - independent from any huge monitoring solution;
  - fun to code :)

More precisely:
  * The 2 first points are to make the system accessible to more people by automating and pre-building the typical monitoring environments so that users can focus on customizing, not just getting the basics working.

  * Shinken provides a business monitoring service, not just an IT focused service. This means helping users to differentiate between real business impacting outages and minor IT related failures.

  * The next two are for the global architecture. We should be able to scale the load within minutes without losing the high availability feature. We believe this has been successfully implemented. :)

  * Multi platform is also important. If we only focused on GNU/Linux, a large user segment would be left out (Windows!). Of course, some features inherited from Nagios are Unix-only like named pipes, but we should promote other ways for users to bypass this (like commands sent to livestatus or in a web based API for example). Such "os limited" points must be *limited to modules*.

.. FIXME: * UTF8 compatible: ``¤§²`` should be a valid name for a server. Some users want to have Japanese and Chinese characters. UFT8 is not an option in the 21st century.

  * UTF8 compatible: ``§²`` should be a valid name for a server. Some users want to have Japanese and Chinese characters. UFT8 is not an option in the 21st century.

  * Nearly compatible with Nagios configuration: No mistake, __nearly__. Shinken is not a Nagios fork. It will never be 100% compatible with it, because some Nagios parameters will never be useful in our architecture like external_command_buffer_slots (why impose artificial limits?) or retained_host_attribute_mask (has anyone used these?). We could manage them. But are they useful? No. Users won't use them, so let's focus on innovation that users want. If there truly is a use case for some oddball feature, we can consider backporting, on condition it is not incompatible or rendered obsolete by the Shinken architecture. Though it will compete with other feature requests and project direction.

  * Fully compatible with plugins: plugins are the life blood of the monitoring system. There is great user value in the plugins, not so much in the legacy core. Shinken is deemed fully compatible and will remain that way. Easy plugins is one reason why Zenoss did not crush Nagios.

  * Fast enough: We've got scalability. We've got a high-level programming language that makes it easy to develop powerful networked code. It provides decent speed, making it easy for every sysadmin to have what he wants. Its the algorithms and protocols that have more impact than the actual speed of a process.

  * Independent from any huge monitoring solution provider: our goal is to provide a tool that is modular and can integrate with others through standard interfaces(local and networked APIs). We welcome all-in-one monitoring solution providers using Shinken as the core of their product, but Shinken will remain independent.

  * Fun to code: the code should be __good__ and foster innovation. While respecting that technical debt should always be paid one day.


This is what we want to have (and already have for the most part).



What we do not want 
~~~~~~~~~~~~~~~~~~~~


At the beginning of the project, we used to say that what we didn't want was our own webui. This became a requirement. Why? Because none of the current UIs truly provided the right way to prioritize and display business oriented information to the end users. Features like root problem analysis or business impact. After trying to adapt the external UIs, we had to roll our own. So we did. :)

So there is nothing we do not want, if in the end it helps Shinken's users.
