#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import os

__version__ = '0.0.1'

mbox_path  = './mbox_files/'
mbox_files = os.listdir(mbox_path)

for filename in mbox_files:

    if (filename[-4:] == 'mbox'):

        mbox_file = f'{mbox_path}/{filename}'
        mbox = mailbox.mbox(mbox_file)

        for msg in mbox:
            print(msg['subject'])


