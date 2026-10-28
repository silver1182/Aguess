import thsdk, pkgutil
print([m.name for m in pkgutil.iter_modules(thsdk.__path__)])
import thsdk.api as api
print([n for n in dir(api) if not n.startswith('_')][:50])
