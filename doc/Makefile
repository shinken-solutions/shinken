XMLSOURCE=About/about.xml About/whatsnew.xml About.xml AdvancedTopics/adaptive.xml AdvancedTopics/cachedchecks.xml AdvancedTopics/cgiincludes.xml AdvancedTopics/checkscheduling.xml AdvancedTopics/clusters.xml AdvancedTopics/dependencies.xml AdvancedTopics/dependencychecks.xml AdvancedTopics/distributed.xml AdvancedTopics/downtime.xml AdvancedTopics/embeddedperl.xml AdvancedTopics/escalations.xml AdvancedTopics/eventhandlers.xml AdvancedTopics/extcommands.xml AdvancedTopics/flapping.xml AdvancedTopics/freshness.xml AdvancedTopics/objectinheritance.xml AdvancedTopics/objecttricks.xml AdvancedTopics/oncallrotation.xml AdvancedTopics/passivestatetranslation.xml AdvancedTopics/perfdata.xml AdvancedTopics/redundancy.xml AdvancedTopics/stalking.xml AdvancedTopics/volatileservices.xml AdvancedTopics.xml ConfiguringNagios/cgiauth.xml ConfiguringNagios/config.xml ConfiguringNagios/configcgi.xml ConfiguringNagios/configmain.xml ConfiguringNagios/configobject.xml ConfiguringNagios/customobjectvars.xml ConfiguringNagios/objectdefinitions.xml ConfiguringNagios.xml Development/epnplugins.xml Development/pluginapi.xml Development.xml GettingStarted/beginners.xml GettingStarted/monitoring-linux.xml GettingStarted/monitoring-netware.xml GettingStarted/monitoring-printers.xml GettingStarted/monitoring-publicservices.xml GettingStarted/monitoring-routers.xml GettingStarted/monitoring-windows.xml GettingStarted/quickstart-fedora.xml GettingStarted/quickstart-opensuse.xml GettingStarted/quickstart-ubuntu.xml GettingStarted/quickstart.xml GettingStarted/upgrading.xml GettingStarted.xml IntegrationWithOtherSoftware/int-snmptrap.xml IntegrationWithOtherSoftware/int-tcpwrappers.xml IntegrationWithOtherSoftware/integration.xml IntegrationWithOtherSoftware.xml NagiosAddons/addons.xml NagiosAddons.xml RunningNagios/startstop.xml RunningNagios/verifyconfig.xml RunningNagios.xml SecurityAndPerformanceTuning/cgisecurity.xml SecurityAndPerformanceTuning/faststartup.xml SecurityAndPerformanceTuning/largeinstalltweaks.xml SecurityAndPerformanceTuning/mrtggraphs.xml SecurityAndPerformanceTuning/nagiostats.xml SecurityAndPerformanceTuning/security.xml SecurityAndPerformanceTuning/tuning.xml SecurityAndPerformanceTuning.xml TheBasics/activechecks.xml TheBasics/cgis.xml TheBasics/hostchecks.xml TheBasics/macrolist.xml TheBasics/macros.xml TheBasics/networkreachability.xml TheBasics/notifications.xml TheBasics/passivechecks.xml TheBasics/plugins.xml TheBasics/servicechecks.xml TheBasics/statetypes.xml TheBasics/timeperiods.xml TheBasics.xml nagios.xml

all:html/index.html pdf/nagios-dblatex.pdf pdf/nagios-db2latex.pdf pdf/nagios-fop.pdf dvi/nagios.dvi

html/index.html:$(XMLSOURCE)
	xmlto -o html/ html nagios.xml	
	
pdf/nagios-dblatex.pdf:$(XMLSOURCE)
	dblatex nagios.xml -o pdf/nagios-dblatex.pdf

pdf/nagios-db2latex.pdf:$(XMLSOURCE)
	dblatex nagios.xml -o pdf/nagios-db2latex.pdf -T db2latex

pdf/nagios-fop.pdf:$(XMLSOURCE)
	xmlto -o pdf --with-fop pdf nagios.xml
	mv pdf/nagios.pdf pdf/nagios-fop.pdf

dvi/nagios.dvi:$(XMLSOURCE)
	xmllint --xinclude --postvalid  nagios.xml --output nagios-big.xml
	docbook2dvi -o dvi nagios-big.xml
	mv dvi/nagios-big.dvi dvi/nagios.dvi
	rm nagios-big.xml

clean:
	rm -f pdf/nagios-dblatex.pdf pdf/nagios-db2latex.pdf pdf/nagios-fop.pdf nagios-big.xml dvi/nagios.dvi html/*.html
