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
    for key, value in headers: 
        msg_new[key] = value
    return msg_new

#you might have to break each loop into a seperate function
def multipart_message(msg, msg_new):
    for part in msg.get_payload():
        headers = msg.items()
        set_headers(headers, msg_new)
        if isinstance(part, email.message.Message):
            if part.is_multipart():           
                msg_new = multipart_message(part, msg_new)
            else:
                #todo!
                #rather than assign the output of single_message()
                #to msg_new, add it to a dictionary. Then loop
                #through that dictionary at the end under main()
                #and add it to mbox_new

                #payload is a string()
                #print(type(part.get_payload()))
                msg_new = single_message(part, msg_new)
                print(100*'#')
                print(msg_new)
                #input('click')
        else:
            msg_new = single_message(part, msg_new)
    #print(75*'#')
    #print(msg_new)
    return msg_new

def single_message(msg, msg_new):
 
    content_type = msg.get_content_type()
    charset = msg.get_content_charset() 
    headers = msg.items() 
    set_headers(headers, msg_new)
 
    if not charset or content_type == 'text/plain':
        #usually attachments
        payload = msg.get_payload()
    else:
        payload = str(msg.get_payload(decode=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]

    #print(type(payload))
    if payload:
        msg_new.set_payload(payload)
    return msg_new

 
def process_message(msg, msg_new):
    #if msg and msg_new:
    if msg.is_multipart():
        msg_new = multipart_message(msg, msg_new)
    else:
        msg_new = single_message(msg, msg_new)
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
                msg      = mbox[key]
                msg_new  = mailbox.mboxMessage()

                unixfrom = msg.get_unixfrom()
                if unixfrom:
                    msg_new = msg_new.set_unixfrom(unixfrom)

                msg_new = process_message(msg, msg_new)

                #todo!
                #check to see if mbox_new is a dictionary, if so, loop
                #through the array and add each element to mbox_new

                mbox_new.add(msg_new)

            except (AttributeError, KeyError, UnicodeEncodeError) as e:

                print(crayons.magenta(f"Error for '{mbox_file_new}' {e}"))
                continue

        mbox_new.flush
        mbox_new.unlock()
