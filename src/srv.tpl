define service{
        use                             local-service         ; Name of service template to use
        host_name                       localhost
        service_description             srv-ZZ
        check_command                   check_http
        notifications_enabled           0
        _httpstink                      yesindead
        }

