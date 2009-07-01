import Pyro.core

# finds object automatically if you're running the Name Server.
jokes = Pyro.core.getProxyForURI("PYRONAME://jokegen")

print jokes.joke("Irmen")

