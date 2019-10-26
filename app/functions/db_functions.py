"""
The purpose of this module is mainly to
contain general functions that query the
db in some way, as much should be migrated
as possible from ieddit.py
"""
import sys
import os
sys.path.append('..')
import config
from share import *


##### Sub Functions #####

@cache.memoize(config.DEFAULT_CACHE_TIME)
def is_sub_nsfw(sub):
    """
    returns a boolean if a sub obj is nsfw
    """
    s = db.session.query(Sub).filter_by(name=sub).first()
    if s.nsfw:
        return True
    return False

@cache.memoize(config.DEFAULT_CACHE_TIME)
def normalize_sub(sub):
    """
    if a subname is incorrectly capitalized, correct it
    """
    subl = db.session.query(Sub).filter(func.lower(Sub.name) == func.lower(sub)).first()
    if subl != None:
        return subl.name
    return sub
