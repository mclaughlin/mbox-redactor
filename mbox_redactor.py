#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import os
import crayons

__version__ = '0.0.1'

mbox_path  = './mbox_files/'
mbox_files = os.listdir(mbox_path)

def print_headers(headers):
    for key, value in headers:
        print(f'Key: {key} \nValue: {value}')


for filename in mbox_files:

    if (filename[-4:] == 'mbox'):

        mbox_file = f'{mbox_path}/{filename}'
        mbox = mailbox.mbox(mbox_file)

        for key, value in mbox.iteritems():

            print(crayons.red(str(key)))
            message = mbox[key]
            unix_from = message.get_unixfrom()
            headers = message.items()
            values  = message.values()

            print('\n\n')
            print(crayons.green(f'filename: {filename}'))
            print(f'unixfrom: {unix_from}')
            print_headers(headers)

            if message.is_multipart():

                multipart_payload = message.get_payload()

                print(crayons.yellow(f'multipart payload: {multipart_payload}'))

                for payload in multipart_payload:

                    print(crayons.yellow(40*'-'))
                    print_headers(payload.items())
                    print(crayons.cyan(payload.get_payload(decode=True)))
                    
            else:

                payload = message.get_payload(decode=True)

                print(payload)
                print(40*'#')



