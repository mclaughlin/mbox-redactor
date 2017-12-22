#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import os
import crayons

__version__ = '0.0.1'

def print_headers(headers):
    for key, value in headers:
        print(f'Key: {key} \nValue: {value}')

def set_headers(headers, mbox_new):
    for key, value in headers:
        mbox_new[key] = value

mbox_path     = './mbox_files/'
mbox_path_new = './mbox_files_new/'
mbox_files    = os.listdir(mbox_path)

if not os.path.exists(mbox_path_new):
    os.makedirs(mbox_path_new)

for filename in mbox_files:

    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.box'

        mbox            = mailbox.mbox(mbox_file)
        mbox_new        = mailbox.mbox(mbox_file_new)
        mbox_new.lock()

        for key, value in mbox.iteritems():

            #get message input
            message     = mbox[key]
            unixfrom    = message.get_unixfrom()
            headers     = message.items()
            values      = message.values()

            #terminal output
            print('\n\n')
            print(f'Message #: {crayons.red(str(key))}')
            print(crayons.green(f'filename: {filename}'))
            print(f'unixfrom: {unixfrom}')
            print_headers(headers)

            #set output
            message_new = mbox_new[key]
            message_new.set_unixfrom(unixfrom)
            set_headers(headers, mbox_new)

            if message.is_multipart():

                multipart_payload = message.get_payload()

                print(crayons.yellow(f'multipart payload: {multipart_payload}'))

                for payload in multipart_payload:

                    payload_decoded = payload.get_payload(decode=True)

                    print(crayons.yellow(40*'-'))
                    print_headers(payload.items())
                    print(crayons.cyan(payload_decoded))

                    #set output
                    set_headers(payload.items(), mbox_new)
                    message_new.set_payload(payload_decoded)
                    
            else:

                payload = message.get_payload(decode=True)

                print(payload)
                print(40*'#')

                #set output
                message_new.set_payload(payload)

        #write file and finish up
        mbox_new.add(message_new)
        mbox_new.flush
        mbox_new.unlock


