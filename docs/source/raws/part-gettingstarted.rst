.. _part-gettingstarted:




=========================
Part II. Getting Started 
=========================


**Table of Contents**

  * :ref:`3. Advice for Beginners <gettingstarted-beginners>`
  * :ref:`4. Quickstart Installation Guides <gettingstarted-quickstart>`
    * :ref:`Guides <gettingstarted-quickstart#guides>`
    * :ref:`Post-Installation Modifications <gettingstarted-quickstart#post-installation_modifications>`
  * :ref:`5. Ubuntu Quickstart <gettingstarted-quickstart-gnulinux>`
    * :ref:`Prerequisites <gettingstarted-quickstart-gnulinux#prerequisites>`
    * :ref:`Create Account Information <gettingstarted-quickstart-gnulinux#create_account_information>`
    * :ref:`Download Shinken and the Plugins <gettingstarted-quickstart-gnulinux#download_shinken_and_the_plugins>`
    * :ref:`Install Shinken <gettingstarted-quickstart-gnulinux#install_shinken>`
    * :ref:`Customize Configuration <gettingstarted-quickstart-gnulinux#customize_configuration>`
    * :ref:`Install the Nagios Plugins to use with Shinken <gettingstarted-quickstart-gnulinux#install_the_nagios_plugins_to_use_with_shinken>`
    * :ref:`Start Shinken <gettingstarted-quickstart-gnulinux#start_shinken>`
    * :ref:`Other Modifications <gettingstarted-quickstart-gnulinux#other_modifications>`
  * :ref:`5.5 Nokia N900 Quickstart <gettingstarted-quickstart-nokia>`
  * :ref:`6. Windows Quickstart <gettingstarted-quickstart-windows>`
    * :ref:`What You'll End Up With <gettingstarted-quickstart-windows#what_you'll_end_up_with>`
    * :ref:`Prerequisites <gettingstarted-quickstart-windows#prerequisites>`
    * :ref:`Download Shinken and the Plugins <gettingstarted-quickstart-windows#download_shinken_and_the_plugins>`
    * :ref:`Install Shinken as a Service <gettingstarted-quickstart-windows#install_shinken_as_a_service>`
    * :ref:`Customize Configuration <gettingstarted-quickstart-windows#customize_configuration>`
    * :ref:`Compile and Install the Nagios Plugins <gettingstarted-quickstart-windows#compile_and_install_the_nagios_plugins>`
    * :ref:`Start Shinken <gettingstarted-quickstart-windows#start_shinken>`
    * :ref:`Other Modifications <gettingstarted-quickstart-windows#other_modifications>`
    * :ref:`You're Done <gettingstarted-quickstart-windows#you're_done>`
  * :ref:`7. Upgrading Shinken <ch07>`
    * :ref:`Upgrading From Previous Shinken Releases <ch07#upgrading_from_previous_shinken>`
    * :ref:`Upgrading From Nagios 3.x <ch07#upgrading_from_nagios_3.x>`
    * :ref:`Upgrading From an RPM Installation <ch07#upgrading_from_an_rpm_installation>`
  * :ref:`8. Monitoring Windows Machines <gettingstarted-monitoring-windows>`
    * :ref:`Introduction <gettingstarted-monitoring-windows#introduction>`
    * :ref:`Overview <gettingstarted-monitoring-windows#overview>`
    * :ref:`Steps <gettingstarted-monitoring-windows#steps>`
    * :ref:`What's Already Done For You <gettingstarted-monitoring-windows#what's_already_done_for_you>`
    * :ref:`Prerequisites <gettingstarted-monitoring-windows#prerequisites>`
    * :ref:`Installing the Windows Agent <gettingstarted-monitoring-windows#installing_the_windows_agent>`
    * :ref:`Configuring Shinken <gettingstarted-monitoring-windows#configuring_shinken>`
    * :ref:`Password Protection <gettingstarted-monitoring-windows#password_protection>`
    * :ref:`Restarting Shinken <gettingstarted-monitoring-windows#restarting_shinken>`
  * :ref:`9. Monitoring Linux/Unix Machines <gettingstarted-monitoring-linux>`
    * :ref:`Introduction <gettingstarted-monitoring-linux#introduction>`
    * :ref:`Overview <gettingstarted-monitoring-linux#overview>`
  * :ref:`11. Monitoring Network Printers <gettingstarted-monitoring-printers>`
    * :ref:`Introduction <gettingstarted-monitoring-printers#introduction>`
    * :ref:`Overview <gettingstarted-monitoring-printers#overview>`
    * :ref:`Steps <gettingstarted-monitoring-printers#steps>`
    * :ref:`What's Already Done For You <gettingstarted-monitoring-printers#what's_already_done_for_you>`
    * :ref:`Prerequisites <gettingstarted-monitoring-printers#prerequisites>`
    * :ref:`Configuring Shinken <gettingstarted-monitoring-printers#configuring_shinken>`
    * :ref:`Restarting Shinken <gettingstarted-monitoring-printers#restarting_shinken>`
  * :ref:`12. Monitoring Routers and Switches <gettingstarted-monitoring-routers>`
    * :ref:`Introduction <gettingstarted-monitoring-routers#introduction>`
    * :ref:`Overview <gettingstarted-monitoring-routers#overview>`
    * :ref:`Steps <gettingstarted-monitoring-routers#steps>`
    * :ref:`What's Already Done For You <gettingstarted-monitoring-routers#what's_already_done_for_you>`
    * :ref:`Prerequisites <gettingstarted-monitoring-routers#prerequisites>`
    * :ref:`Configuring Shinken <gettingstarted-monitoring-routers#configuring_shinken>`
    * :ref:`Monitoring Services <gettingstarted-monitoring-routers#monitoring_services>`
    * :ref:`Monitoring Packet Loss and RTA <gettingstarted-monitoring-routers#monitoring_packet_loss_and_rta>`
    * :ref:`Monitoring SNMP Status Information <gettingstarted-monitoring-routers#monitoring_snmp_status_information>`
    * :ref:`Monitoring Bandwidth / Traffic Rate <gettingstarted-monitoring-routers#monitoring_bandwidth_/_traffic_rate>`
    * :ref:`Restarting Shinken <gettingstarted-monitoring-routers#restarting_shinken>`
  * :ref:`13. Monitoring Publicly Available Services <gettingstarted-monitoring-publicservices>`
    * :ref:`Introduction <gettingstarted-monitoring-publicservices#introduction>`
    * :ref:`Plugins For Monitoring Services <gettingstarted-monitoring-publicservices#plugins_for_monitoring_services>`
    * :ref:`Creating A Host Definition <gettingstarted-monitoring-publicservices#creating_a_host_definition>`
    * :ref:`Creating Service Definitions <gettingstarted-monitoring-publicservices#creating_service_definitions>`
    * :ref:`Monitoring HTTP <gettingstarted-monitoring-publicservices#monitoring_http>`
    * :ref:`Monitoring FTP <gettingstarted-monitoring-publicservices#monitoring_ftp>`
    * :ref:`Monitoring SSH <gettingstarted-monitoring-publicservices#monitoring_ssh>`
    * :ref:`Monitoring SMTP <gettingstarted-monitoring-publicservices#monitoring_smtp>`
    * :ref:`Monitoring POP3 <gettingstarted-monitoring-publicservices#monitoring_pop3>`
    * :ref:`Monitoring IMAP <gettingstarted-monitoring-publicservices#monitoring_imap>`
    * :ref:`Restarting Shinken <gettingstarted-monitoring-publicservices#restarting_shinken>`

