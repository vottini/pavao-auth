#!/usr/bin/python3

#import os
#import time
#import sys

#import importlib.machinery
#import importlib.util

#if len(sys.argv) > 1:
#	scripts = [ f"{file}.py" for file in sys.argv[1:] ]

#else:
#	files = os.listdir('scripts')
#	filtered = filter(lambda file : file.startswith("T"), files)
#	scripts = list(filtered)
#	scripts.sort()

#for script in scripts: 
#	if not script.startswith("T"):
#		continue

#	loader = importlib.machinery.SourceFileLoader('test', f'scripts/{script}')
#	spec = importlib.util.spec_from_loader('test', loader)
#	test = importlib.util.module_from_spec(spec)
#	loader.exec_module(test)
	
#	for attr in dir(test):
#		if attr.startswith("test_"):
#			print(f"{script}: ", end="")
#			func = getattr(test, attr)
#			func()

#	time.sleep(1)

import common

print(common.login_userdata('gustavo.venturini', 'Trento12'))
