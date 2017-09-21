#!/usr/bin/env python

import shutil
from subprocess import Popen

shutil.rmtree('docs/html', True)
Popen(['make', 'html'], cwd='docs').wait()
