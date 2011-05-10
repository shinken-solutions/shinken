#!/usr/bin/python
# encoding: utf-8

import config, re, pprint, time
from lib import *


# Python 2.3 does not have 'set' in normal namespace.
# But it can be imported from 'sets'
try:
    set()
except NameError:
    from sets import Set as set



#      ____                _              _       
#     / ___|___  _ __  ___| |_ __ _ _ __ | |_ ___ 
#    | |   / _ \| '_ \/ __| __/ _` | '_ \| __/ __|
#    | |__| (_) | | | \__ \ || (_| | | | | |_\__ \
#     \____\___/|_| |_|___/\__\__,_|_| |_|\__|___/
#                                                 


g_impacts = None
g_problems = None


def load_impacts():
    global g_impacts
    g_impacts = {}
    
    # Get all critical impacts that got a critity > 2
    # TODO : filter with this fucking criticity > 2, how can we do a AND with livestatus?
    query_impacts = "GET services\nColumns: description host_name criticity source_problems service_last_state_change state icon_image_expanded plugin_output\nFilter: is_impact = 1\n"
    #html.write("Want to lunach %s<br>" % query_impacts)
    data = html.live.query(query_impacts)
    i = 0

    # Do not take OK/UP elements
    for e in [e for e in data if e[5] != 0]:
        #html.write("%s<br>" % e)
        i += 1
        impact = e[0]
        h_name = e[1]
        crit = e[2]
        # Don't know wy, but it gove me some low level impact?
        problems = e[3]
        last_state_change = e[4]
        state = e[5]
        icon = e[6]
        output = e[7]
        duration = time.time() - last_state_change
        if not crit in g_impacts:
            g_impacts[crit] = []
        g_impacts[crit].append({'type' : 'service','description': impact, 'host': h_name, 'problems' : problems, 'duration' : duration,
                                'state' : state, 'icon' : icon, 'output' : output, 'id' : i})


def load_problems():
    global g_problems
    global g_impacts
    #Will be a name indexed hash
    g_problems = {}
    for (crit, entries) in g_impacts.items():
        for entry in entries:
            problems = entry['problems']
            for p in problems:
                # Maybe this problem is common to numerous impacts
                # so skip it, we already got data
                if p in g_problems:
                    continue
                # If the problem is an host
                if not '/' in p:
                    typ = 'host'
                    query_pb = "GET hosts\nColumns: last_state_change state plugin_output is_host_acknowledged\nFilter: name = %s\n" % p
                    #html.write('I want to launch %s<br>' % query_pb)
                    data = html.live.query(query_pb)
                    #html.write("<br>I got pbb data %s<br>" % data)
                else: #it's a service
                    typ = 'service'
                    elts = p.split('/')
                    name = elts[0]
                    desc = elts[1]
                    query_pb = "GET services\nColumns: last_state_change state plugin_output is_service_acknowledged\nFilter: host_name = %s\nFilter: description = %s" % (name, desc)
                    #html.write('I want to launch %s<br>' % query_pb)
                    data = html.live.query(query_pb)
                    #html.write("<br>I got pbb data %s<br>" % data)
                data = data[0]
                last_state_change = data[0]
                state = data[1]
                output = data[2]
                is_acknowledged = data[3]
                duration = time.time() - last_state_change
                g_problems[p] = {'duration' : duration, 'state' : state, 'output' : output, 'type' : typ,
                                 'is_acknowledged' : is_acknowledged}



def print_impacts_table():
    global g_impacts
    
    div = "<div class='impacts-panel' style='min-height: 983px; '>"
    html.write(div)

    # From crit 5 to crit 3
    # for test, go to whole
    for crit in range(5, -1, -1):

        #if there is no item of this criticity, bail out
        if not g_impacts.has_key(crit):
            continue

        #for (crit, entries) in g_impacts.items():
        entries = g_impacts[crit]
        if len(entries) > 0:
            # First the line that show the criticity level
            #html.write("<table class=boxlayout><tr><td class=boxcolumn><table class=groupheader><tr class=groupheader><td>Criticity %d </td></tr></table>" % crit)
            # Then the table with all impacts from this criticities
            #html.write("<table class=services>")
            for entry in entries:
                html.write("<div class='impact' id='impacts'>")
                desc = entry['description']
                h_name = entry['host']
                problems = entry['problems']
                duration = entry['duration']
                output = entry['output']
                state = entry['state']
                typ = entry['type']
                i = entry['id']

                # Show the more link on the right
                html.write("<div class='show-problem'>")
                html.write("<div class='pblink' id='%d'> <img src='../htdocs/images/alert_start.png'> </div>" % i)
                html.write("</div>")

                # Show the icon of the service/host
                html.write("<div class='impact-icon'>")
                html.write("<img src='../htdocs/images/icons/earth.png'>")
                html.write("</div>")

                #Begin a row and Show the name
                html.write("<div class='impact-row'>")
                html.write("<span class='impact-name'>")
                html.write("%s/%s" % (h_name, desc))
                html.write("</span>") # of the impact-name
                html.write(" is ")
                # And print the state as a text
                html.write("<span class='impact-state-text'>")
                html.write(pretty_state(state, typ))
                html.write("</span>") # of the impact-state-text
                html.write("</div>") # of the impact-row for The first line

                #Begin a row with the output
                html.write("<div class='impact-row'>")
                html.write("<span class='impact-output'>")
                html.write(output)
                html.write("</span>") # of the impact output
                html.write("</div>") # of the impact-row for the output

                # Now print the duration
                html.write("<div class='impact-row'>")
                html.write("<span class='impact-duration'>")
                html.write("%s" % pretty_duration(duration))
                html.write("</span>") # of the impact duration
                html.write("</div>") # of the impact-row for the duration

                #html.write("Service %s on host %s is %s since %s due to %s" % (desc, h_name, state, duration, problems))
            #html.write("</table>")
                html.write("</div>")
    html.write("</div>")
 

def print_problems_tables():
    global g_impacts
    global g_problems
    #html.write("problems tables")

    html.write("<script language='JavaScript'> var all_ids = new Array(")
    all_ids = []
    for (crit, entries) in g_impacts.items():
        for entry in entries:
            i = entry['id']
            all_ids.append("'%d'" % i)
    html.write(",".join(all_ids))
    html.write(")</script>")
    
    div = "<div class='problems-panels'>"
    html.write(div)

    # Keep an id for ALL root problems
    pb_id = 0

    for (crit, entries) in g_impacts.items():
        for entry in entries:
            i = entry['id']
            desc = entry['description']
            h_name = entry['host']
            state = entry['state']
            typ = entry['type']

            #html.write("<dd>")
            #div = "<div class='problems-panel' style='display: none;' id='problems-%d'>" % i
            div = "<div class='problems-panel' id='problems-%d'>" % i
            html.write(div)


            html.write("<div class='right-panel-top'> <div class='pblink' id='%d'> Close </div> </div>" % i)
            html.write("<br style='clear: both'>")

            # Show the icon of the service/host
            html.write("<div class='impact-icon'>")
            html.write("<img src='../htdocs/images/icons/earth.png'>")
            html.write("</div>")


            #Begin a row and Show the name
            html.write("<div class='impact-row'>")
            html.write("<span class='impact-name'>")
            html.write("%s/%s" % (h_name, desc))
            html.write("</span>") # of the impact-name
            html.write(" is ")
            # And print the state as a text
            html.write("<span class='impact-state-text'>")
            html.write(pretty_state(state, typ))
            html.write("</span>") # of the impact-state-text
            html.write("</div>") # of the impact-row for The first line

            html.write("<br style='clear: both'>")

            problems = entry['problems']

            # first print unack problems
            unack_pbs = [p for p in problems if not g_problems[p]['is_acknowledged']]
            if len(unack_pbs) > 0:
                html.write("Root problems unamanaged :")
            #html.write("<table class=services style='display: block;'>")

            for p in unack_pbs:
                pb_id = pb_id + 1
                pb = g_problems[p]
                duration = pb['duration']
                state = pb['state']
                output = pb['output']
                typ = pb['type']
                html.write("<div class='problem' id='%d'>" % pb_id)
                html.write("<div class='%s'>" % get_div_srv_hst(state, typ))
                html.write("%s is %s since %d with output %s" % (p, pretty_state(state, typ), duration, output))
                html.write("</div>") # close the class host down and co
                html.write("<div class='problem-actions' id='actions-%d'>" % pb_id)
                #html.write("Actions : ")
                args = '%s/%s/%s' % ('fixit', 'paris', p)
                html.write("<div class='action-fixit' id='%s'><img class='icon' title='Try to fix it' src='../htdocs/images/icon_ack.gif'>Try to fix it</div>" % args)
                html.write(" ")
                args = '%s/%s/%s' % ('ack', 'paris', p)
                html.write("<div class='action-ack' id='%s'><img class='icon' title='Acknoledge it' src='../htdocs/images/link_processes.gif'>Acknoledge it</div>" % args)

                html.write("</div>") # close action part
                html.write("</div>") #close the problem

            # Then ack ones
            ack_pbs = [p for p in problems if g_problems[p]['is_acknowledged']]
            if len(ack_pbs) > 0:
                html.write("Currently managed root problems :")
            for p in ack_pbs:
                pb_id = pb_id + 1
                pb = g_problems[p]
                duration = pb['duration']
                state = pb['state']
                output = pb['output']
                typ = pb['type']
                html.write("<div class='problem' id='%d'>" % pb_id)
                html.write("<div class='%s'>" % get_div_srv_hst(state, typ))
                html.write("%s is in problem with state %s since %d with output %s" % (p, pretty_state(state, typ), duration, output))
                html.write("</div>") # end row for service host in red/yellow
                html.write("<div class='problem-actions' id='actions-%d'>" % pb_id)
                html.write("Here are my actions")
                html.write("</div>") # close action part
                html.write("</div>") #close the problem

                
            html.write("</div>") # End problem
            #html.write("</dd>")

    html.write("</div>") #we close the problems panels


# Print the right panel
def print_right_panel():
    div = "<div class='right-panel'>"
    html.write(div)
    html.write('my ass is chicken')


    html.write("<table class=\"content_center tacticaloverview\" cellspacing=2 cellpadding=0 border=0>\n")
    for t in ["host", "service"]:
        html.write("<tr><th>Serice</th><th>Problems</th><th>Unhandled</th></tr>\n")
        html.write("<tr>")
        
        html.write('<td class=total><a target="main" href="cgi/view.py?view_name=allserice">1</a></td>')
        html.write('<td class="states prob">2</td>')
        html.write("</tr>\n")
    html.write("</table>\n")
    html.write("</div>")


# The duration is in seconds, need a better looking text.
def pretty_duration(duration):
    # Look at a value in minutes
    duration = duration / 60
    # Less than 5 minutes is Just now
    if duration < 5:
        return 'Just now'
    # Between 5 and 15, need a good precision
    if duration < 15:
        return 'since %d minutes' % duration
    # For 15->30, around at 5 minutes precision
    if duration < 30: 
        return 'since %d minutes' % duration - duration % 5
    # For 30->45, say half an hour
    if duration < 45:
        return 'since half an hour'
    # For 45->60, say 45 minutes
    if duration < 60:
        return 'since 45 minutes'
    # Ok now we reach an hour (but what the admins are doing???)
    if duration < 90:
        return 'since an hour'
    if duration < 120:
        return 'since an hour and half'
    # Put duration in hours"
    duration = duration / 60
    # For 2 hours-> one day, talk in hours
    if duration < 1440:
        return 'since %d hours' % duration
    # Now talk in days
    duration = duration / 24
    # Between one day and one week, 
    if duration < 7:
        return 'since %d days' % duration
    # Now talk in weeks so...
    duration = duration / 7
    if duration < 4:
        return 'since %d weeks' % duration
    # Ok, now talks in months!
    duration = duration / 4
    if duration < 12:
        return 'since %d months' % duration
    #Ok, in years!
    duration = duration / 12
    return 'since %d years!' % duration


# Return a pretty type for state like
# Critical or Down
def pretty_state(state, typ):
    if typ == 'service':
        map = {0 : 'Ok', 1 : 'Warning', 2 : 'Critical', 3 : 'Unknown'}
        return map.get(state, 'Unknown')
    # Now a service, so an host
    map = {0 : 'Up', 1 : 'Down', 2 : 'Down', 3 : 'Down'}
    return map.get(state, 'Down')


def get_div_srv_hst(state, typ):
    if typ == 'service':
        return 'divstate%d' % state
    else: # host
        return 'divhstate%d' % state

# Load the static configuration of all services and hosts (including tags)
# without state and store it in the global variable g_services.

def load_services():
    global g_services
    g_services = {}
    html.live.set_prepend_site(True)
    data = html.live.query("GET hosts\nColumns: name custom_variable_names custom_variable_values services\n")
    html.live.set_prepend_site(False)

    for site, host, varnames, values, services in data:
        vars = dict(zip(varnames, values))
        tags = vars.get("TAGS", "").split(" ")
        g_services[(site, host)] = (tags, services)
        

#      ____                       
#     |  _ \ __ _  __ _  ___  ___ 
#     | |_) / _` |/ _` |/ _ \/ __|
#     |  __/ (_| | (_| |  __/\__ \
#     |_|   \__,_|\__, |\___||___/
#                 |___/           

# Just for debugging
def page_debug(h):
    global html
    html = h
    compile_forest()
    
    html.header("BI Debug")
    render_forest()
    html.footer()


# Just for debugging, as well
def page_all(h):
    global html
    html = h

    #div = "<div class='problems-panel' style='display: block; left: 600px;'>"
    #html.write(div)

    load_impacts()
    load_problems()

    # Got real error, be purple
#    if len(g_impacts) > 0:
#        html.define_dynamic_css(['global_critical.css'])
#    else:
#        html.define_dynamic_css(['global_ok.css'])

    html.header("All critical impacts for your business")    
    html.write("<div class='whole-page'>")
    #html.write('</div>')
    print_impacts_table()

    print_right_panel()
    
    print_problems_tables()

    # Finish the whole page
    html.write("</div>")
    #html.write(div)
    #html.write("Mon cul c'est du poulet!")
    #html.write('</div>')
    #compile_forest()
    #load_assumptions()
    #for group, trees in g_aggregation_forest.items():
    #    html.write("<h2>%s</h2>" % group)
    #    for inst_args, tree in trees:
    #        state = execute_tree(tree)
    #        debug(state)
    html.footer()


#    ____        _                                          
#   |  _ \  __ _| |_ __ _ ___  ___  _   _ _ __ ___ ___  ___ 
#   | | | |/ _` | __/ _` / __|/ _ \| | | | '__/ __/ _ \/ __|
#   | |_| | (_| | || (_| \__ \ (_) | |_| | | | (_|  __/\__ \
#   |____/ \__,_|\__\__,_|___/\___/ \__,_|_|  \___\___||___/
#                                                           

def create_aggregation_row(tree, status_info = None):
    state = execute_tree(tree, status_info)
    eff_state = state[0]
    if state[1] != None:
        eff_state = state[1]
    else:
        eff_state = state[0]
    return {
        "aggr_tree"            : tree,
        "aggr_treestate"       : state,
        "aggr_state"           : state[0],  # state disregarding assumptions
        "aggr_assumed_state"   : state[1],  # is None, if no assumptions are done
        "aggr_effective_state" : eff_state, # is assumed_state, if there are assumptions, else real state
        "aggr_name"            : state[2],
        "aggr_output"          : state[3],
        "aggr_hosts"           : state[4],
        "aggr_function"        : state[5],
    }

def table(h, columns, add_headers, only_sites, limit, filters):
    global html
    html = h
    compile_forest()
    load_assumptions() # user specific, always loaded
    # Hier müsste man jetzt die Filter kennen, damit man nicht sinnlos
    # alle Aggregationen berechnet.
    rows = []
    # Apply group filter. This is important for performance. We 
    # must not compute any aggregations from other groups and filter 
    # later out again.
    only_group = None
    only_service = None
    
    for filter in filters:
        if filter.name == "aggr_group":
            only_group = filter.selected_group()
        elif filter.name == "aggr_service":
            only_service = filter.service_spec()

    # TODO: Optimation of affected_hosts filter!

    if only_service:
        affected = g_affected_services.get(only_service)
        if affected == None:
            items = []
        else:
            by_groups = {}
            for group, aggr in affected:
                entries = by_groups.get(group, [])
                entries.append(aggr)
                by_groups[group] = entries
            items = by_groups.items()

    else:
        items = g_aggregation_forest.items()

    for group, trees in items:
        if only_group not in [ None, group ]:
            continue

        for tree in trees:
            row = create_aggregation_row(tree)
            row["aggr_group"] = group
            rows.append(row)
            if not html.check_limit(rows, limit):
                return rows
    return rows
        

# Table of all host aggregations, i.e. aggregations using data from exactly one host
def host_table(h, columns, add_headers, only_sites, limit, filters):
    global html
    html = h
    compile_forest()
    load_assumptions() # user specific, always loaded

    # Create livestatus filter for filtering out hosts. We can
    # simply use all those filters since we have a 1:n mapping between
    # hosts and host aggregations
    filter_code = ""
    for filt in filters: 
        header = filt.filter("bi_host_aggregations")
        if not header.startswith("Sites:"):
            filter_code += header

    host_columns = filter(lambda c: c.startswith("host_"), columns)
    hostrows = get_status_info_filtered(filter_code, only_sites, limit, host_columns)
    # if limit:
    #     views.check_limit(hostrows, limit)

    rows = []
    # Now compute aggregations of these hosts
    for hostrow in hostrows:
        site = hostrow["site"]
        host = hostrow["name"]
        status_info = { (site, host) : [ hostrow["state"], hostrow["plugin_output"], hostrow["services_with_info"] ] }
        for group, aggregation in g_host_aggregations.get((site, host), []):
            row = hostrow.copy()
            row.update(create_aggregation_row(aggregation, status_info))
            row["aggr_group"] = group
            rows.append(row)
            if not html.check_limit(rows, limit):
                return rows

    return rows


#     _   _      _                     
#    | | | | ___| |_ __   ___ _ __ ___ 
#    | |_| |/ _ \ | '_ \ / _ \ '__/ __|
#    |  _  |  __/ | |_) |  __/ |  \__ \
#    |_| |_|\___|_| .__/ \___|_|  |___/
#                 |_|                  

def debug(x):
    import pprint
    p = pprint.pformat(x)
    html.write("<pre>%s</pre>\n" % p)

def load_assumptions():
    global g_assumptions
    g_assumptions = config.load_user_file("bi_assumptions", {})

def save_assumptions():
    config.save_user_file("bi_assumptions", g_assumptions)

def load_treestate():
    return config.load_user_file("bi_treestate", (None, {}))

def save_treestate(current_ex_level, treestate):
    config.save_user_file("bi_treestate", (current_ex_level, treestate))

def status_tree_depth(tree):
    nodes = tree[6]
    if nodes == None:
        return 1
    else:
        maxdepth = 0
        for node in nodes:
            maxdepth = max(maxdepth, status_tree_depth(node))
        return maxdepth + 1

def is_part_of_aggregation(h, what, site, host, service):
    global html
    html = h
    compile_forest()
    if what == "host":
        return (site, host) in g_affected_hosts
    else:
        return (site, host, service) in g_affected_services

