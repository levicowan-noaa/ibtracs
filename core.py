__all__ = ['Database', 'Storm', 'save_database']

from datetime import datetime
import numpy as np
import os
from pytoolbox.geospatial import earthdist

workdir = os.path.join(os.environ['HOME'], 'work/ibtracs')


##########################
#    Helper Functions    #
##########################
def save_database():
    """
    Initialize the database and save it to disk
    """
    import pickle

    I = Database()
    f = open('ibtracs.pkl', 'wb')
    pickle.dump(I, f, pickle.HIGHEST_PROTOCOL)
    f.close()
