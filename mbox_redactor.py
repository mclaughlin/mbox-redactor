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

def multipart_message(msg, msg_new):
    print(100*'<')
    messages = list(msg.walk())
    print(len(messages))
    print(messages)
    for part in messages:
        print(100*'#')
        payload = None
        set_headers(part.items(), msg_new)
        content_type = part.get_content_type()
        charset = part.get_content_charset()
        boundary = part.get_boundary()
        charset = part.get_charset()

        print(f'{type(part)} - {boundary}')
        print(f'part ID: {id(part)}')
        print(f'boundary: {boundary}')
        print(f'content type: {part.get_content_type()}')
        print(f'charset: {part.get_content_charset()}')
        print(f'headers: {part.items()}')
        print(f'content_disposition: {msg.get_content_disposition()}')

        print(100*'~')
        print(msg)

        if type(part) is email.message.Message:
            if boundary and part is not messages \
                    and type(part.get_payload()) is list:
                nested_message(part, msg_new)
            else:
                single_message(part, msg_new)

    print(100*'>')
    print('\n')
    return msg_new

def nested_message(part, msg_new):
    sub_messages = list(part.walk())
    for subpart in sub_messages:

        boundary = subpart.get_boundary()
        subpart_payload = subpart.get_payload()

        print(f'subpart ID: {id(subpart)}')
        print(f'boundary: {boundary}')
        print(f'content type: {subpart.get_content_type()}')
        print(f'charset: {part.get_content_charset()}')
        print(f'content_disposition: {msg.get_content_disposition()}')
        print(50*'^')

        if type(subpart) is mailbox.mboxMessage:
            multipart_message(subpart, msg_new)
        if type(subpart) is email.message.Message:
            if boundary and subpart is not part \
                    and type(subpart.get_payload()) is list:
                nested_message(subpart, msg_new)
            else:
                single_message(subpart, msg_new)
    return msg_new

def single_message(msg, msg_new):

    content_type = msg.get_content_type()
    charset = msg.get_content_charset()
    content_disposition = msg.get_content_disposition()
    payload = None

    if content_type != 'text/plain' \
            and content_disposition != 'attachment':
        payload = str(msg.get_payload(decode=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]
    else:
        #usually attachments
        payload = msg.get_payload()
    add_payload(payload, msg_new)
    return msg_new

def add_payload(payload, msg_new):
    if payload:
        msg_new.set_payload(payload)
    if msg_new:
        mbox_new.add(msg_new)


def process_message(msg, msg_new):
    if msg.is_multipart():
        #if isinstance(msg, mailbox.mboxMessage):
        #    set_headers(msg.items(), msg_new)
        multipart_message(msg, msg_new)
    else:
        set_headers(msg.items(), msg_new)
        single_message(msg, msg_new)
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
                msg     = mbox[key]
                msg_new = mailbox.mboxMessage()
                msg_new = process_message(msg, msg_new)



            except (AttributeError, KeyError, UnicodeEncodeError) as e:

                print(crayons.magenta(f"Error for '{mbox_file_new}' {e}"))
                continue

        mbox_new.flush
        mbox_new.unlock()
