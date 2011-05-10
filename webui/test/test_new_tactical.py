import sys

sys.path.insert(0, '..')
print sys.path
import cgi


print cgi.__file__


# --------------------------------------------------------------
#    _____          _   _           _                             _
#   |_   _|_ _  ___| |_(_) ___ __ _| |   _____   _____ _ ____   _(_) _____      __
#     | |/ _` |/ __| __| |/ __/ _` | |  / _ \ \ / / _ \ '__\ \ / / |/ _ \ \ /\ / /
#     | | (_| | (__| |_| | (_| (_| | | | (_) \ V /  __/ |   \ V /| |  __/\ V  V /
#     |_|\__,_|\___|\__|_|\___\__,_|_|  \___/ \_/ \___|_|    \_/ |_|\___| \_/\_/
#
# --------------------------------------------------------------
def render_tactical_overview():
    host_query = \
        "GET hosts\n" \
        "Stats: state >= 0\n" \
        "Stats: state > 0\n" \
        "Stats: scheduled_downtime_depth = 0\n" \
        "StatsAnd: 2\n" \
        "Stats: state > 0\n" \
        "Stats: scheduled_downtime_depth = 0\n" \
        "Stats: acknowledged = 0\n" \
        "StatsAnd: 3\n" \
        "Filter: custom_variable_names < _REALNAME\n"

    service_query = \
        "GET services\n" \
        "Stats: state >= 0\n" \
        "Stats: state > 0\n" \
        "Stats: scheduled_downtime_depth = 0\n" \
        "Stats: host_scheduled_downtime_depth = 0\n" \
        "Stats: host_state = 0\n" \
        "StatsAnd: 4\n" \
        "Stats: state > 0\n" \
        "Stats: scheduled_downtime_depth = 0\n" \
        "Stats: host_scheduled_downtime_depth = 0\n" \
        "Stats: acknowledged = 0\n" \
        "Stats: host_state = 0\n" \
        "StatsAnd: 5\n" \
        "Filter: host_custom_variable_names < _REALNAME\n"

    # ACHTUNG: Stats-Filter so anpassen, dass jeder Host gezaehlt wird.

    try:
        hstdata = html.live.query_summed_stats(host_query)
        svcdata = html.live.query_summed_stats(service_query)
    except livestatus.MKLivestatusNotFoundError:
        html.write("<center>No data from any site</center>")
        return
    html.write("<table class=\"content_center tacticaloverview\" cellspacing=2 cellpadding=0 border=0>\n")
    for title, data, view, what in [
            ("Hosts",    hstdata, 'hostproblems', 'host'),
            ("Services", svcdata, 'svcproblems',  'service'),
            ]:
        html.write("<tr><th>%s</th><th>Problems</th><th>Unhandled</th></tr>\n" % title)
        html.write("<tr>")

        html.write('<td class=total><a target="main" href="cgi/view.py?view_name=all%ss">%d</a></td>' % (what, data[0]))
        unhandled = False
        for value in data[1:]:
            if value > 0:
                href = "cgi/view.py?view_name=" + view
                if unhandled:

                    href += "&is_%s_acknowledged=0" % what
                text = link(str(value), href)
            else:
                text = str(value)
            html.write('<td class="%s">%s</td>' % (value == 0 and " " or "states prob", text))
            unhandled = True
        html.write("</tr>\n")
    html.write("</table>\n")

sidebar_snapins["tactical_overview"] = {
    "title" : "Tactical Overview",
    "description" : "The total number of hosts and service with and without problems",
    "author" : "Mathias Kettner",
    "refresh" : 10,
    "render" : render_tactical_overview,
    "allowed" : [ "user", "admin", "guest" ],
    "styles" : """
table.tacticaloverview {
   border-collapse: separate;
   /**
    * Don't use border-spacing. It is not supported by IE8 with compat mode and older IE versions.
    * Better set cellspacing in HTML code. This works in all browsers.
    * border-spacing: 5px 2px;
    */
   width: %dpx;
   margin-top: 0;
}
table.tacticaloverview th { font-size: 7pt; text-align: left; font-weight: normal; padding: 0; padding-top: 2px; }
table.tacticaloverview td { text-align: right; border: 1px solid #444; padding: 0px; }
table.tacticaloverview td a { display: block; margin-right: 2px; }
""" % snapin_width
}
# table.tacticaloverview td.prob { font-weight: bold; }
