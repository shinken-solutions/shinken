rem Stopping the services
net stop "Shinken Arbiter"
net stop "Shinken Broker"
net stop "Shinken Poller"
net stop "Shinken Reactionner"
net stop "Shinken Receiver"
net stop "Shinken Scheduler"
rem Deleting the services (registry store)
sc delete "ShinkenArbiter_service"
sc delete "ShinkenBroker_service"
sc delete "ShinkenPoller_service"
sc delete "ShinkenReactionner_service"
sc delete "ShinkenReceiver_service"
sc delete "ShinkenScheduler_service"