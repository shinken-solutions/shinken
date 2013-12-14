.. _part-thebasics:




===================
Part V. The Basics 
===================


**Table of Contents**

  * :ref:`23. Nagios/Shinken Plugins <thebasics-plugins>`
    * :ref:`Introduction <thebasics-plugins#introduction>`
    * :ref:`What Are Plugins? <thebasics-plugins#what_are_plugins>`
    * :ref:`Plugins As An Abstraction Layer <thebasics-plugins#plugins_as_an_abstraction_layer>`
    * :ref:`What Plugins Are Available? <thebasics-plugins#what_plugins_are_available>`
    * :ref:`Obtaining Plugins <thebasics-plugins#obtaining_plugins>`
    * :ref:`How Do I Use Plugin X? <thebasics-plugins#how_do_i_use_plugin_x>`
    * :ref:`Plugin API <thebasics-plugins#plugin_api>`
  * :ref:`24. Understanding Macros and How They Work <thebasics-macros>`
    * :ref:`Macros <thebasics-macros#macros>`
    * :ref:`Macro Substitution - How Macros Work <thebasics-macros#macro_substitution_-_how_macros_work>`
    * :ref:`Example 1: Host Address Macro <_host_address_macro>`
    * :ref:`Example 2: Command Argument Macros <_command_argument_macros>`
    * :ref:`On-Demand Macros <thebasics-macros#on-demand_macros>`
    * :ref:`On-Demand Group Macros <thebasics-macros#on-demand_group_macros>`
    * :ref:`Custom Variable Macros <thebasics-macros#custom_variable_macros>`
    * :ref:`Macro Cleansing <thebasics-macros#macro_cleansing>`
    * :ref:`Macros as Environment Variables <thebasics-macros#macros_as_environment_variables>`
    * :ref:`Available Macros <thebasics-macros#available_macros>`
  * :ref:`25. Standard Macros in Shinken/Nagios <thebasics-macrolist>`
    * :ref:`Macro Validity <thebasics-macrolist#macro_validity>`
    * :ref:`Macro Availability Chart <thebasics-macrolist#macro_availability_chart>`
    * :ref:`Macro Descriptions <thebasics-macrolist#macro_descriptions>`
    * :ref:`Notes <thebasics-macrolist#notes>`
  * :ref:`26. Host Checks <thebasics-hostchecks>`
    * :ref:`Introduction <thebasics-hostchecks#introduction>`
    * :ref:`When Are Host Checks Performed? <thebasics-hostchecks#when_are_host_checks_performed>`
    * :ref:`Cached Host Checks <thebasics-hostchecks#cached_host_checks>`
    * :ref:`Dependencies and Checks <thebasics-hostchecks#dependencies_and_checks>`
    * :ref:`Parallelization of Host Checks <thebasics-hostchecks#parallelization_of_host_checks>`
    * :ref:`Host States <thebasics-hostchecks#host_states>`
    * :ref:`Host State Determination <thebasics-hostchecks#host_state_determination>`
    * :ref:`Host State Changes <thebasics-hostchecks#host_state_changes>`
  * :ref:`27. Service Checks <thebasics-servicechecks>`
    * :ref:`Introduction <thebasics-servicechecks#introduction>`
    * :ref:`When Are Service Checks Performed? <thebasics-servicechecks#when_are_service_checks_performed>`
    * :ref:`Cached Service Checks <thebasics-servicechecks#cached_service_checks>`
    * :ref:`Dependencies and Checks <thebasics-servicechecks#dependencies_and_checks>`
    * :ref:`Parallelization of Service Checks <thebasics-servicechecks#parallelization_of_service_checks>`
    * :ref:`Service States <thebasics-servicechecks#service_states>`
    * :ref:`Service State Determination <thebasics-servicechecks#service_state_determination>`
    * :ref:`Services State Changes <thebasics-servicechecks#services_state_changes>`
  * :ref:`28. Active Checks <thebasics-activechecks>`
    * :ref:`Introduction <thebasics-activechecks#introduction>`
    * :ref:`How Are Active Checks Performed? <thebasics-activechecks#how_are_active_checks_performed>`
    * :ref:`When Are Active Checks Executed? <thebasics-activechecks#when_are_active_checks_executed>`
  * :ref:`29. Passive Checks <thebasics-passivechecks>`
    * :ref:`Introduction <thebasics-passivechecks#introduction>`
    * :ref:`Uses For Passive Checks <thebasics-passivechecks#uses_for_passive_checks>`
    * :ref:`How Passive Checks Work <thebasics-passivechecks#how_passive_checks_work>`
    * :ref:`Enabling Passive Checks <thebasics-passivechecks#enabling_passive_checks>`
    * :ref:`Submitting Passive Service Check Results <thebasics-passivechecks#submitting_passive_service_check_results>`
    * :ref:`Submitting Passive Host Check Results <thebasics-passivechecks#submitting_passive_host_check_results>`
    * :ref:`Passive Checks and Host States <thebasics-passivechecks#passive_checks_and_host_states>`
    * :ref:`Submitting Passive Check Results From Remote Hosts <thebasics-passivechecks#submitting_passive_check_results_from_remote_hosts>`
  * :ref:`30. State Types <thebasics-statetypes>`
    * :ref:`Introduction <thebasics-statetypes#introduction>`
    * :ref:`Service and Host Check Retries <thebasics-statetypes#service_and_host_check_retries>`
    * :ref:`Soft States <thebasics-statetypes#soft_states>`
    * :ref:`Hard States <thebasics-statetypes#hard_states>`
    * :ref:`Example <thebasics-statetypes#example>`
  * :ref:`31. Time Periods <thebasics-timeperiods>`
    * :ref:`Introduction <thebasics-timeperiods#introduction>`
    * :ref:`Precedence in Time Periods <thebasics-timeperiods#precedence_in_time_periods>`
    * :ref:`How Time Periods Work With Host and Service Checks <thebasics-timeperiods#how_time_periods_work_with_host_and_service_checks>`
    * :ref:`How Time Periods Work With Contact Notifications <thebasics-timeperiods#how_time_periods_work_with_contact_notifications>`
    * :ref:`How Time Periods Work With Notification Escalations <thebasics-timeperiods#how_time_periods_work_with_notification_escalations>`
    * :ref:`How Time Periods Work With Dependencies <thebasics-timeperiods#how_time_periods_work_with_dependencies>`
  * :ref:`32. Determining Status and Reachability of Network Hosts <thebasics-networkreachability>`
    * :ref:`Introduction <thebasics-networkreachability#introduction>`
    * :ref:`Example Network <thebasics-networkreachability#example_network>`
    * :ref:`Defining Parent/Child Relationships <thebasics-networkreachability#defining_parent/child_relationships>`
    * :ref:`Reachability Logic in Action <thebasics-networkreachability#reachability_logic_in_action>`
    * :ref:`UNREACHABLE States and Notifications <thebasics-networkreachability#unreachable_states_and_notifications>`
  * :ref:`33. Notifications <thebasics-notifications>`
    * :ref:`Introduction <thebasics-notifications#introduction>`
    * :ref:`When Do Notifications Occur? <thebasics-notifications#when_do_notifications_occur>`
    * :ref:`Who Gets Notified? <thebasics-notifications#who_gets_notified>`
    * :ref:`What Filters Must Be Passed In Order For Notifications To Be Sent? <thebasics-notifications#what_filters_must_be_passed_in_order_for_notifications_to_be_sent>`
    * :ref:`Program-Wide Filter: <>`
    * :ref:`Service and Host Filters: <>`
    * :ref:`Contact Filters: <>`
    * :ref:`Notification Methods <thebasics-notifications#notification_methods>`
    * :ref:`Notification Type Macro <thebasics-notifications#notification_type_macro>`
    * :ref:`Helpful Resources <thebasics-notifications#helpful_resources>`


