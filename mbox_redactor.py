#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import os
import shutil
import crayons

__version__ = '0.0.1'

mbox_path     = './mbox_files/'
mbox_path_new = './mbox_files_new/'
mbox_files    = os.listdir(mbox_path)

if os.path.exists(mbox_path_new):
    shutil.rmtree(mbox_path_new)

os.makedirs(mbox_path_new)

def print_headers(headers):
    for key, value in headers:
        print(f'Key: {key} \nValue: {value}')

def set_headers(headers, message_new):
    for key, value in headers:
        message_new[key] = value
    return message_new

def process_message(message, message_new):
    if message.is_multipart():

        multipart_payload = message.get_payload()
#        print(crayons.yellow(f'multipart payload: {multipart_payload}'))

        for payload in multipart_payload:

            payload_decoded = payload.get_payload(decode=True)

            print(crayons.yellow(40*'-'))
#            print_headers(payload.items())
#            print(crayons.cyan(payload_decoded))

            #set output
            message_new = set_headers(payload.items(), message_new)
            message_new.set_payload(payload_decoded)
            print(50*'%')
            
    else:

        message_new = set_headers(headers, message_new)
#        print(crayons.green(f'NEW HEADERS: {message_new}'))
        payload = message.get_payload(decode=True)

#        print(payload)
#        print(40*'#')

        #set output
        message_new.set_payload(payload)

    return message_new


for filename in mbox_files:

    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.box'

        mbox            = mailbox.mbox(mbox_file)
        mbox_new        = mailbox.mbox(mbox_file_new)
        mbox_new.lock()

        for key, value in mbox.iteritems():

            try:

                #get message input
                message     = mbox[key]
                unixfrom    = message.get_unixfrom()
                headers     = message.items()
#                values      = message.values()

                #terminal output
#                print('\n\n')
#                print(f'Message #: {crayons.red(str(key))}')
#                print(crayons.green(f'filename: {filename}'))
#                print(f'unixfrom: {unixfrom}')
#                print_headers(headers)

                #output
                message_new = mailbox.mboxMessage()
                message_new.set_unixfrom(unixfrom)
                message_new = process_message(message, message_new)
                print(message_new.items())
                
                #write file and finish up
                mbox_new.add(message_new)
                mbox_new.flush
                mbox.unlock()

            except (KeyError) as e:
                print(e)
                pass
 

