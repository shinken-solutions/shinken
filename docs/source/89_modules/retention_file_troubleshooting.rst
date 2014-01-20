.. _retention_file_troubleshooting:


Retention troubleshooting
=========================

The retention file contains the state of your host and services, so that they are kept when shinken is restarted.

Sometimes you'll want to inspect (and possibly fix) the retention file, in case you need to work-around a bug or simply better understand what is stored there.

When you use the PickleRetention module in the scheduler (cf. ''define scheduler'' in ''shinken-specific.cfg''), you can simply manipulate the retention file using Python.

For this you can use the following code.
  * It assumes Shinken is installed in ''/opt/shinken'' with the retention file in ''/tmp/retention.dat'':
  * Run and play with it interactively using ''ipython -i inspect_retention.py''.
  
::

  
  #!/usr/bin/python
  import pickle
  import sys
  sys.path.append('/opt/shinken')
  import shinken
  
  r = pickle.load(file('/tmp/retention.dat'))
  h = r['hosts']
  
  # Example:
  # [(k,v) for (k,v) in h['your_host'].items() if k.find('downtime') >= 0]
  # 
  # del h['your_host']
  # 
  # for k,v in r['services'].items():
  #     if 'your_host' in k:
  #         del r['services'][k]


To save your changes:
  * Stop Shinken: ''service shinken stop''
  * Save the pickle: ''pickle.dump(r, open('/tmp/retention.dat', 'w'))''
  * Start Shinken: ''service shinken start''
