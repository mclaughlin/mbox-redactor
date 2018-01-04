#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import os
import shutil
import crayons

__version__ = '0.0.1'

mbox_path     = './mbox_files'
mbox_path_new = './mbox_files_new'
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

def process_payload(message_new, headers, payload):
    message_new = set_headers(headers, message_new)
    message_new.set_payload(payload)
    return message_new

def process_multipart(message, message_new):

    multipart_payload = message.get_payload()

    for part in multipart_payload:
        
        message_new = set_headers(part.items(), message_new)
        payload = part.get_payload(decode=True)
        charset = part.get_content_charset()
        content_type = part.get_content_type()

        headers = part.items()
        message_new = set_headers(headers, message_new) 

        if payload:

            if not charset:
                #usually attachments
                payload = str(part.get_payload())
            else:
                payload = str(payload)
                if payload.startswith("b'") and payload.endswith("'"):
                    payload =  payload[2:-1]
            message_new.set_payload(payload.encode('utf-8'))

        elif part.is_multipart():

            #add processing of multi-part headers/payload here

            #recursive call
            message_new = process_multipart(part, message_new)

    return message_new

def process_message(message, message_new):

    if message.is_multipart():

        new_message = process_multipart(message, message_new)

    else:

        message_new = set_headers(message.items(), message_new)
        payload = message.get_payload(decode=True)
        charset = message.get_content_charset()
        #payload = payload.decode(charset)

        #set output
        message_new.set_payload(payload)

    return message_new


for filename in mbox_files:

    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.mbox'

        mbox            = mailbox.mbox(mbox_file)
        mbox_new        = mailbox.mbox(mbox_file_new)
        mbox_new.lock()

        for key, value in mbox.iteritems():

            try:

                #get message input
                message     = mbox[key]
                unixfrom    = message.get_unixfrom()
                headers     = message.items()

                #output
                message_new = mailbox.mboxMessage()
                message_new.set_unixfrom(unixfrom)
                message_new = set_headers(headers, message_new)
                message_new = process_message(message, message_new)

                #write file and finish up
                mbox_new.add(message_new)

            except (KeyError, UnicodeEncodeError) as e:

                print(crayons.magenta(f"Error for '{mbox_file_new}' {e}"))
                continue

        mbox_new.flush
        mbox_new.unlock()


 

