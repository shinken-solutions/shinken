Exceptions
==========

Exception class diagram in Shinken
-----------------------------------

Simple Exception class diagram :

.. inheritance-diagram:: __builtin__.Exception
                        shinken.http_daemon.InvalidWorkDir  shinken.http_daemon.PortNotFree
                        shinken.http_client.HTTPException  shinken.satellite.NotWorkerMod
                        shinken.webui.bottlecore.BottleException  shinken.webui.bottlecore.HTTPResponse
                        shinken.webui.bottlecore.HTTPError  shinken.webui.bottlecore.RouteError
                        shinken.webui.bottlecore.RouteReset  shinken.webui.bottlecore.RouteSyntaxError
                        shinken.webui.bottlecore.RouteBuildError  shinken.webui.bottlecore.TemplateError
                        shinken.webui.bottlewebui.BottleException  shinken.webui.bottlewebui.HTTPResponse
                        shinken.webui.bottlewebui.HTTPError  shinken.webui.bottlewebui.RouteError
                        shinken.webui.bottlewebui.RouteReset  shinken.webui.bottlewebui.RouteSyntaxError
                        shinken.webui.bottlewebui.RouteBuildError  shinken.webui.bottlewebui.TemplateError
                        shinken.daemon.InvalidPidFile
   :parts: 3
