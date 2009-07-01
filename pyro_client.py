import Pyro.core,time

# you have to change the URI below to match your own host/port.
checks = Pyro.core.getProxyForURI("PYROLOC://localhost:7766/Checks")
i = 0
debut=time.time()
while i < 10000:
    #jokes = Pyro.core.getProxyForURI("PYROLOC://localhost:7766/jokegen")
    i = i + 1
    checks.get_checks()
fin=time.time()

print "Total 10000 =",fin-debut,"Temps moyen =",((fin-debut)/10000)*100, "ms"
