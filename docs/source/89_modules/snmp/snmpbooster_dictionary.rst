.. _snmpbooster_dictionary:



SnmpBooster reference dictionary 
---------------------------------

  * Jump back to :ref:`SnmpBooster documentation index <setup_active_module_checks>`



SnmpBooster.ini dictionary 
~~~~~~~~~~~~~~~~~~~~~~~~~~~


There are five dictionaries:
  * [DATASOURCE]
  * [DSTEMPLATE]
  * [MAP]
  * [TRIGGER]
  * [TRIGGERGROUP]



DATASOURCE DICTIONARY 
**********************


OidVariableName refers to an actual OID that can be queries using SNMP against the device on the network.

[VariableName] refers to a Datasource and all the information required to gather and prepare the data using SNMP
ds_type refers to how the data should be prepared
ds_calc refers to any scaling manipulations to make the data more understandable. This is an RPN expression, where the first variable is omitted, as it is always the $OidVariable
ds_oid refers to the actual $OidVariable name. An instance identifier can be appended to the name to signify that an instance is provided by the Shinken service definition. This information is passed when the check is called.
...



DSTEMPLATE DICTIONNARY 
***********************

[DsTemplateName] refers to the name of the DSTEMPLATE that will be referred to in the Shinken service definitions.
ds refers to the list of DATASOURCES to be collected. If an instance is expected for the list of DATASOURCES, it MUST be the same instance for all Oids. If a different instance is required, use a second DSTEMPLATE.



TRIGGER DICTIONNARY 
********************


..



TRIGGERGROUP DICTIONNARY 
*************************


..



MAP DICTIONNARY 
****************





SnmpBooster.ini example configuration 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This example definition will be used to explain each section.

[DATASOURCE]
  
::

    OidmyOidDefinition = .1.3.6.1.45.0
    [myOidDefinition] ; Use the same name as the myOidDeiniftion, but omit the leading "Oid"
        ds_type = DERIVE
        ds_calc = 8,*  ; RPN expression : Oid, 8, *  Which means Oid * 8 = Total
        ds_oid = $OidmyOidDefinition
[DSTEMPLATE]
  
::

    [myCiscoRouter]
        ds = myOidDefinition
[TRIGGER]
  
::

    [trigger1]
        warning = RPN expression
        critical = RPN expression
    [trigger2]
        warning = RPN expression
        critical = RPN expression
[TRIGGERGROUP]
  
::

    [CiscoRouterTriggers]
        triggers = trigger1, trigger2
        
  


SnmpBooster.ini configuring SNMP Datasources 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



The first location is generic data related to SNMP parameters.
  * DATASOURCE information
    * SNMP OID
    * Type of data and how can it be interpreted (GAUGE, COUNTER, COUNTER64, DERIVE, DERIVE64, TEXT, TIMETICK)
    * Data format preparation (Scaling the data for example bits to bytes)
    * Is there an instance to append to the
  * Instance MAP function
    * Mapping the instance dynamically using a function
    * Data or rules related to the mapping function



SnmpBooster.ini configuring SNMP DSTEMPLATES 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  * DSTEMPLATEs to associate DATASOURCE to actual device classes
    * List of DATASOURCES associated with a, for example, Cisco 1900 router. Which in turn can be applied to a Shinken service



SnmpBooster.ini setting triggers/thresholds 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  * TRIGGER and TRIGGERGROUPS to apply thresholding rules
    * Define triggers and associate them with a TRIGGERGROUP name that can be applied to a Shinken Service