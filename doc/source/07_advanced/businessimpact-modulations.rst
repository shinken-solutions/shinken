.. _advanced/businessimpact-modulations:

==========================
Businessimpact modulations
==========================


How businessimpact modulations works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on your configuration you may want to change the business impact of a specific host during the night.
For example you don't consider a specific application as critical for business during night because there are no users, so impact is lower on errors.



How to define a businessimpact_modulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  define businessimpactmodulation{
    business_impact_modulation_name  LowImpactOnNight
    business_impact                  1
    modulation_period                night
  }



  define service{
    check_command                  check_crm_status
    check_period                   24x7
    host_name                      CRM
    service_description            CRM_WEB_STATUS
    use                            generic-service
    business_impact                3
    businessimpactmodulations      LowImpactOnNight
  }

Here the business impact will be modulated to 1 during night for the service CRM_WEB_STATUS.