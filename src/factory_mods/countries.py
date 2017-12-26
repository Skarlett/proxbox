#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from __init__ import data_folder, path
import json

data_file = path.join(data_folder, path.split(__file__.split('.')[0]+'.json')[1])
USE = True


def _c(catagory):
  with open(data_file) as f:
    return json.load(f)[catagory]

def country_full(): return _c('full')
def country_abrv(): return _c('abbr')

def setup(interpreter):
  interpreter.active_funcs.add(country_abrv)
  interpreter.active_funcs.add(country_full)