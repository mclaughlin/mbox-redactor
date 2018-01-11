#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import email
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

def set_headers(headers, msg_new):
#    print(headers)
#    input('press key')
    for key, value in headers: 
        msg_new[key] = value
#        print(f'{key}: {value}')
#        input('press key')
    return msg_new

def process_payload(headers, payload, msg_new):
    msg_new = set_headers(headers, msg_new)
    msg_new.set_payload(payload)
    return msg_new

def process_multipart(msg, msg_new):
    for part in msg.get_payload():
        msg_new = process_message(part, msg_new)
    return msg_new

def process_message(msg, msg_new):
    msg_new = set_headers(msg.items(), msg_new)

#    print(f'is_multipart: {msg.is_multipart()}')
#    print(f'content_type: {content_type}')
#    print(f'charset: {charset}')
#    input('click')
#    print(f'payload: {msg.get_payload()}')
#    input('click')

    if msg.is_multipart() and isinstance(msg, mailbox.mboxMessage):
        if not isinstance(msg, str):
            msg_new = set_headers(msg.items(), msg_new)        
        msg_new = process_multipart(msg, msg_new)
#    elif msg.is_multipart():
    else:
        #need to find out why this payload isn't being included
        msg_new = set_headers(msg.items(), msg_new)
        #for key, value in msg.items():
        #    print(f'{key} - {value}')
#        print(str(msg.get_payload()))
        
        if msg.is_multipart():
            for part in msg.get_payload():
                headers = part.items()
                msg_new = set_headers(headers, msg_new)
                #print(part.get_payload(decode=True))
                ####
                # process part here:
                content_type = part.get_content_type()
                charset = part.get_content_charset()
                if isinstance(part, email.message.Message):
                    #usually attachments
                    payload = part.get_payload(decode=True) 
                    msg_new.set_payload(payload)
                    if isinstance(payload, list):
                        for subpart in payload:
#                            print(subpart.items())
#                            print(subpart.get_payload(decode=True))
#                            input('click')
                            headers = subpart.items()
                            msg_new = set_headers(headers, msg_new)

                            payload = str(part.get_payload(decode=True))
                            if payload.startswith("b'") and payload.endswith("'"):
                                payload =  payload[2:-1]
                                msg_new.set_payload(payload)
 
                    else:
                        #this is the attachment email from Kathy
                        #why isn't this being included???
#                        print(part.items())
#                        print(payload)
                        headers = part.items()
                        msg_new = set_headers(headers, msg_new)
                        payload = str(payload)

                        if payload.startswith("b'") and payload.endswith("'"):
                            payload = payload[2:-1]
                            bob = msg_new
                            msg_new.set_payload(payload)
                            print(bob)
                            return msg_new
                        else:
                            msg_new.set_payload(payload)
                else:
                    payload = str(part.get_payload(decode=True))
                    if payload.startswith("b'") and payload.endswith("'"):
                        payload =  payload[2:-1]
                        msg_new.set_payload(payload)
                ####
        else:
            content_type = msg.get_content_type()
            charset = msg.get_content_charset()

            if not charset or content_type == 'text/plain':
                #usually attachments
                payload = msg.get_payload()
            else:
                payload = str(msg.get_payload(decode=True))
                if payload.startswith("b'") and payload.endswith("'"):
                    payload =  payload[2:-1]
            msg_new.set_payload(payload)
    return msg_new

for filename in mbox_files:
    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.mbox'
        mbox            = mailbox.mbox(mbox_file)
        mbox_new        = mailbox.mbox(mbox_file_new)
        mbox_new.lock()

        for key, value in mbox.iteritems():
            try:
                #get msg input
                msg      = mbox[key]
                unixfrom = msg.get_unixfrom()
                #headers  = msg.items()

                #output
                msg_new  = mailbox.mboxMessage()
                msg_new.set_unixfrom(unixfrom)

                if msg.is_multipart():
                    for part in msg.walk():
                        msg_new = process_message(part, msg_new)
                else:
                    msg_new = process_message(msg, msg_new)

                #write file and finish up
                mbox_new.add(msg_new)

            except (AttributeError, KeyError, UnicodeEncodeError) as e:

                print(crayons.magenta(f"Error for '{mbox_file_new}' {e}"))
                continue

        mbox_new.flush
        mbox_new.unlock()
