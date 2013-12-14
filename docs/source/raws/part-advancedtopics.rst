.. _part-advancedtopics:




=========================
Part VI. Advanced Topics 
=========================


**Table of Contents**

  * :ref:`35. External Commands <advancedtopics-extcommands>`
    * :ref:`Introduction <advancedtopics-extcommands#introduction>`
    * :ref:`Enabling External Commands <advancedtopics-extcommands#enabling_external_commands>`
    * :ref:`When Does Nagios Check For External Commands? <advancedtopics-extcommands#when_does_nagios_check_for_external_commands>`
    * :ref:`Using External Commands <advancedtopics-extcommands#using_external_commands>`
    * :ref:`Command Format <advancedtopics-extcommands#command_format>`
  * :ref:`36. Event Handlers <advancedtopics-eventhandlers>`
    * :ref:`Introduction <advancedtopics-eventhandlers#introduction>`
    * :ref:`When Are Event Handlers Executed? <advancedtopics-eventhandlers#when_are_event_handlers_executed>`
    * :ref:`Event Handler Types <advancedtopics-eventhandlers#event_handler_types>`
    * :ref:`Enabling Event Handlers <advancedtopics-eventhandlers#enabling_event_handlers>`
    * :ref:`Event Handler Execution Order <advancedtopics-eventhandlers#event_handler_execution_order>`
    * :ref:`Writing Event Handler Commands <advancedtopics-eventhandlers#writing_event_handler_commands>`
    * :ref:`Permissions For Event Handler Commands <advancedtopics-eventhandlers#permissions_for_event_handler_commands>`
    * :ref:`Service Event Handler Example <advancedtopics-eventhandlers#service_event_handler_example>`
  * :ref:`37. Volatile Services <advancedtopics-volatileservices>`
    * :ref:`Introduction <advancedtopics-volatileservices#introduction>`
    * :ref:`What Are They Useful For? <advancedtopics-volatileservices#what_are_they_useful_for>`
    * :ref:`What's So Special About Volatile Services? <advancedtopics-volatileservices#what's_so_special_about_volatile_services>`
    * :ref:`The Power Of Two <advancedtopics-volatileservices#the_power_of_two>`
  * :ref:`38. Service and Host Freshness Checks <advancedtopics-freshness>`
    * :ref:`Introduction <advancedtopics-freshness#introduction>`
    * :ref:`How Does Freshness Checking Work? <advancedtopics-freshness#how_does_freshness_checking_work>`
    * :ref:`Enabling Freshness Checking <advancedtopics-freshness#enabling_freshness_checking>`
    * :ref:`Example <advancedtopics-freshness#example>`
  * :ref:`39. Distributed Monitoring <advancedtopics-distributed>`
    * :ref:`Introduction <advancedtopics-distributed#introduction>`
    * :ref:`Goals <advancedtopics-distributed#goals>`
    * :ref:`The global architecture <advancedtopics-distributed#the_global_architecture>`
    * :ref:`The smart and automatic load balancing <advancedtopics-distributed#the_smart_and_automatic_load_balancing>`
    * :ref:`The high availability <advancedtopics-distributed#the_high_availability>`
    * :ref:`External commands dispatching <advancedtopics-distributed#external_commands_dispatching>`
    * :ref:`Different types of Pollers : poller_tag <_poller_tag>`
    * :ref:`Advanced architectures : Realms <_realms>`
  * :ref:`40. Redundant and Failover Network Monitoring <advancedtopics-redundancy>`
    * :ref:`Introduction <advancedtopics-redundancy#introduction>`
  * :ref:`41. Detection and Handling of State Flapping <advancedtopics-flapping>`
    * :ref:`Introduction <advancedtopics-flapping#introduction>`
    * :ref:`How Flap Detection Works <advancedtopics-flapping#how_flap_detection_works>`
    * :ref:`Example <advancedtopics-flapping#example>`
    * :ref:`Flap Detection for Services <advancedtopics-flapping#flap_detection_for_services>`
    * :ref:`Flap Detection for Hosts <advancedtopics-flapping#flap_detection_for_hosts>`
    * :ref:`Flap Detection Thresholds <advancedtopics-flapping#flap_detection_thresholds>`
    * :ref:`States Used For Flap Detection <advancedtopics-flapping#states_used_for_flap_detection>`
    * :ref:`Flap Handling <advancedtopics-flapping#flap_handling>`
    * :ref:`Enabling Flap Detection <advancedtopics-flapping#enabling_flap_detection>`
  * :ref:`42. Notification Escalations <advancedtopics-escalations>`
    * :ref:`Introduction <advancedtopics-escalations#introduction>`
    * :ref:`When Are Notifications Escalated? <advancedtopics-escalations#when_are_notifications_escalated>`
    * :ref:`Contact Groups <advancedtopics-escalations#contact_groups>`
    * :ref:`Overlapping Escalation Ranges <advancedtopics-escalations#overlapping_escalation_ranges>`
    * :ref:`Recovery Notifications <advancedtopics-escalations#recovery_notifications>`
    * :ref:`Notification Intervals <advancedtopics-escalations#notification_intervals>`
    * :ref:`Time Period Restrictions <advancedtopics-escalations#time_period_restrictions>`
    * :ref:`State Restrictions <advancedtopics-escalations#state_restrictions>`
  * :ref:`43. On-Call Rotations <advancedtopics-oncallrotation>`
    * :ref:`Introduction <advancedtopics-oncallrotation#introduction>`
    * :ref:`Scenario 1: Holidays and Weekends <advancedtopics-oncallrotation#scenario_1holidays_and_weekends>`
    * :ref:`Scenario 2: Alternating Days <_alternating_days>`
    * :ref:`Scenario 3: Alternating Weeks <_alternating_weeks>`
    * :ref:`Scenario 4: Vacation Days <_vacation_days>`
    * :ref:`Other Scenarios <advancedtopics-oncallrotation#other_scenarios>`
  * :ref:`44. Monitoring Service and Host Clusters <advancedtopics-clusters>`
    * :ref:`Introduction <advancedtopics-clusters#introduction>`
    * :ref:`Plan of Attack <advancedtopics-clusters#plan_of_attack>`
    * :ref:`Using the check_cluster Plugin <advancedtopics-clusters#using_the_check_cluster_plugin>`
    * :ref:`Monitoring Service Clusters <advancedtopics-clusters#monitoring_service_clusters>`
    * :ref:`Monitoring Host Clusters <advancedtopics-clusters#monitoring_host_clusters>`
  * :ref:`45. Host and Service Dependencies <advancedtopics-dependencies>`
    * :ref:`Introduction <advancedtopics-dependencies#introduction>`
    * :ref:`Service Dependencies Overview <advancedtopics-dependencies#service_dependencies_overview>`
    * :ref:`Defining Service Dependencies <advancedtopics-dependencies#defining_service_dependencies>`
    * :ref:`Example Service Dependencies <advancedtopics-dependencies#example_service_dependencies>`
    * :ref:`How Service Dependencies Are Tested <advancedtopics-dependencies#how_service_dependencies_are_tested>`
    * :ref:`Execution Dependencies <advancedtopics-dependencies#execution_dependencies>`
    * :ref:`Notification Dependencies <advancedtopics-dependencies#notification_dependencies>`
    * :ref:`Dependency Inheritance <advancedtopics-dependencies#dependency_inheritance>`
    * :ref:`Host Dependencies <advancedtopics-dependencies#host_dependencies>`
    * :ref:`Example Host Dependencies <advancedtopics-dependencies#example_host_dependencies>`
  * :ref:`46. State Stalking <advancedtopics-stalking>`
    * :ref:`Introduction <advancedtopics-stalking#introduction>`
    * :ref:`How Does It Work? <advancedtopics-stalking#how_does_it_work>`
    * :ref:`Should I Enable Stalking? <advancedtopics-stalking#should_i_enable_stalking>`
    * :ref:`How Do I Enable Stalking? <advancedtopics-stalking#how_do_i_enable_stalking>`
    * :ref:`How Does Stalking Differ From Volatile Services? <advancedtopics-stalking#how_does_stalking_differ_from_volatile_services>`
    * :ref:`Caveats <advancedtopics-stalking#caveats>`
  * :ref:`47. Performance Data <advancedtopics-perfdata>`
    * :ref:`Introduction <advancedtopics-perfdata#introduction>`
    * :ref:`Types of Performance Data <advancedtopics-perfdata#types_of_performance_data>`
    * :ref:`Plugin Performance Data <advancedtopics-perfdata#plugin_performance_data>`
    * :ref:`Processing Performance Data <advancedtopics-perfdata#processing_performance_data>`
    * :ref:`Processing Performance Data Using Commands <advancedtopics-perfdata#processing_performance_data_using_commands>`
    * :ref:`Writing Performance Data To Files <advancedtopics-perfdata#writing_performance_data_to_files>`
  * :ref:`48. Scheduled Downtime <advancedtopics-downtime>`
    * :ref:`Introduction <advancedtopics-downtime#introduction>`
    * :ref:`Scheduling Downtime <advancedtopics-downtime#scheduling_downtime>`
    * :ref:`Fixed vs. Flexible Downtime <advancedtopics-downtime#fixed_vs._flexible_downtime>`
    * :ref:`Triggered Downtime <advancedtopics-downtime#triggered_downtime>`
    * :ref:`How Scheduled Downtime Affects Notifications <advancedtopics-downtime#how_scheduled_downtime_affects_notifications>`
    * :ref:`Overlapping Scheduled Downtime <advancedtopics-downtime#overlapping_scheduled_downtime>`
  * :ref:`49. Adaptive Monitoring <advancedtopics-adaptative>`
    * :ref:`Introduction <advancedtopics-adaptative#introduction>`
    * :ref:`What Can Be Changed? <advancedtopics-adaptative#what_can_be_changed>`
    * :ref:`External Commands For Adaptive Monitoring <advancedtopics-adaptative#external_commands_for_adaptive_monitoring>`
  * :ref:`50. Predictive Dependency Checks <advancedtopics-dependencychecks>`
    * :ref:`Introduction <advancedtopics-dependencychecks#introduction>`
    * :ref:`How Do Predictive Checks Work? <advancedtopics-dependencychecks#how_do_predictive_checks_work>`
    * :ref:`Enabling Predictive Checks <advancedtopics-dependencychecks#enabling_predictive_checks>`
    * :ref:`Cached Checks <advancedtopics-dependencychecks#cached_checks>`
  * :ref:`51. Cached Checks <advancedtopics-cachedchecks>`
    * :ref:`Introduction <advancedtopics-cachedchecks#introduction>`
    * :ref:`For On-Demand Checks Only <advancedtopics-cachedchecks#for_on-demand_checks_only>`
    * :ref:`How Caching Works <advancedtopics-cachedchecks#how_caching_works>`
    * :ref:`What This Really Means <advancedtopics-cachedchecks#what_this_really_means>`
    * :ref:`Configuration Variables <advancedtopics-cachedchecks#configuration_variables>`
    * :ref:`Optimizing Cache Effectiveness <advancedtopics-cachedchecks#optimizing_cache_effectiveness>`
  * :ref:`52. Passive Host State Translation <advancedtopics-passivestatetranslation>`
    * :ref:`Introduction <advancedtopics-passivestatetranslation#introduction>`
  * :ref:`53. Service and Host Check Scheduling <advancedtopics-checkscheduling>`
    * :ref:`The scheduling <advancedtopics-checkscheduling#the_scheduling>`
  * :ref:`55. Object Inheritance <advancedtopics-objectinheritance>`
    * :ref:`Introduction <advancedtopics-objectinheritance#introduction>`
    * :ref:`Basics <advancedtopics-objectinheritance#basics>`
    * :ref:`Local Variables vs. Inherited Variables <advancedtopics-objectinheritance#local_variables_vs._inherited_variables>`
    * :ref:`Inheritance Chaining <advancedtopics-objectinheritance#inheritance_chaining>`
    * :ref:`Using Incomplete Object Definitions as Templates <advancedtopics-objectinheritance#using_incomplete_object_definitions_as_templates>`
    * :ref:`Custom Object Variables <advancedtopics-objectinheritance#custom_object_variables>`
    * :ref:`Cancelling Inheritance of String Values <advancedtopics-objectinheritance#cancelling_inheritance_of_string_values>`
    * :ref:`Additive Inheritance of String Values <advancedtopics-objectinheritance#additive_inheritance_of_string_values>`
    * :ref:`Implied Inheritance <advancedtopics-objectinheritance#implied_inheritance>`
    * :ref:`Implied/Additive Inheritance in Escalations <advancedtopics-objectinheritance#implied/additive_inheritance_in_escalations>`
    * :ref:`Multiple Inheritance Sources <advancedtopics-objectinheritance#multiple_inheritance_sources>`
    * :ref:`Precedence With Multiple Inheritance Sources <advancedtopics-objectinheritance#precedence_with_multiple_inheritance_sources>`
  * :ref:`56. Time-Saving Tricks For Object Definitions <advancedtopics-objecttricks>`
    * :ref:`Introduction <advancedtopics-objecttricks#introduction>`
    * :ref:`Regular Expression Matching <advancedtopics-objecttricks#regular_expression_matching>`
    * :ref:`Service Definitions <advancedtopics-objecttricks#service_definitions>`
    * :ref:`Service Escalation Definitions <advancedtopics-objecttricks#service_escalation_definitions>`
    * :ref:`Service Dependency Definitions <advancedtopics-objecttricks#service_dependency_definitions>`
    * :ref:`Host Escalation Definitions <advancedtopics-objecttricks#host_escalation_definitions>`
    * :ref:`Host Dependency Definitions <advancedtopics-objecttricks#host_dependency_definitions>`
    * :ref:`Hostgroups <advancedtopics-objecttricks#hostgroups>`

