from omniORB import CORBA, sslTP
import CosNaming

import cereconf
import Cerebrum_core

_orb = None
def get_orb(args=[]):
    global _orb
    if _orb is None:
        # Set up the SSL context
        sslTP.certificate_authority_file(cereconf.SSL_CA_FILE)
        sslTP.key_file(cereconf.SSL_KEY_FILE)
        sslTP.key_file_password(cereconf.SSL_KEY_FILE_PASSWORD)

        # Initialize the ORB
        _orb = CORBA.ORB_init(args, CORBA.ORB_ID)
    return _orb


def connect(args=[]):
    """ 
    Method for connecting to a CORBA name service
    and fetch the Gro object. The method prefers
    SSL connections.
    """
    orb = get_orb()
    # Get the name service and narrow the root context
    obj = orb.resolve_initial_references("NameService")
    rootContext = obj._narrow(CosNaming.NamingContext)

    if rootContext is None:
        raise Exception("Could not narrow the root naming context")

    # Fetch gro using the name service
    name = [CosNaming.NameComponent(cereconf.GRO_CONTEXT_NAME, cereconf.GRO_SERVICE_NAME),
            CosNaming.NameComponent(cereconf.GRO_OBJECT_NAME, "")]

    obj = rootContext.resolve(name)

    gro = obj._narrow(Cerebrum_core.Gro)
    if gro is None:
        raise Exception("Could not narrow the gro object")
    return gro

def string_to_object(string):
    return get_orb().string_to_object(string)

# arch-tag: 614754e4-465c-47ce-92a0-c375e476d563
