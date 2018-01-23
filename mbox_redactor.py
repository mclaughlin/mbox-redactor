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

def set_headers(headers, mboxfile):
    for key, value in headers:
        #print(f'{key}: {value}')
        write_mbox(f'{key}: {value}', mboxfile)

def multipart_message(msg, mboxfile):

    messages       = list(msg.walk())
    sub_msg_count  = 0
    sub_messages   = {}
    boundary_count = {}
    debugging      = False

    if debugging:
        print(100*'<')
        print(len(messages))
        print(messages)

    for part in messages:
        
        content_type = part.get_content_type()
        charset = part.get_content_charset()
        boundary = part.get_boundary()
        charset = part.get_charset()
        message_id = part['Message-ID']
        date = part['Date']

        if debugging:
            print(100*'#')
            print(f'{type(part)} - {boundary}')
            print(f'part ID: {id(part)}')
            print(f'boundary: {boundary}')
            print(f'content type: {part.get_content_type()}')
            print(f'charset: {part.get_content_charset()}')
            print(f'headers: {part.items()}')
            print(f'content_disposition: {part.get_content_disposition()}')
            print(f"message-id: {part['Message-ID']}")
            print(50*'. ')
            #print(msg)
            #print(100*'~')
            print('**OUTPUT**')

        if type(part) is mailbox.mboxMessage: 
            if message_id:
                print(f"From {message_id} {date}")
                write_mbox(f"From {message_id} {date}", mboxfile)
            set_headers(part.items(), mboxfile)
            mbox_boundary = part.get_boundary()

        elif type(part) is email.message.Message \
                and type(part.get_payload()) is list:
            sub_messages[boundary] = part.get_payload()
            print(f'--{mbox_boundary}')
            write_mbox(f'--{mbox_boundary}', mboxfile)
            set_headers(part.items(), mboxfile)

        elif type(part) is email.message.Message \
                and any(part in val for val in sub_messages.values()):
            for boundary, message_list in sub_messages.items():
                if part in message_list:
                    sub_msg_count += 1
                    print(f'--{boundary}')
                    write_mbox(f'--{boundary}', mboxfile)
                    set_headers(part.items(), mboxfile)
                    single_message(part, mboxfile)
                    
                if sub_msg_count == len(message_list):
                    print(f'--{boundary}--')
                    write_mbox(f'--{boundary}--', mboxfile)
                    sub_msg_count = 0
                    
        elif mbox_boundary \
                and (type(part) is mailbox.mboxMessage \
                or   type(part) is email.message.Message):
            print(f'\n--{mbox_boundary}')
            write_mbox(f'\n--{mbox_boundary}', mboxfile)
            set_headers(part.items(), mboxfile)
            single_message(part, mboxfile)

    #single_message(part)
    if mbox_boundary:
        print(f'--{mbox_boundary}--\n')
        write_mbox(f'--{mbox_boundary}--\n', mboxfile)
        mbox_boundary = None

    if debugging:
        print(100*'>')
        print('\n')

def single_message(msg, mboxfile):

    content_type = msg.get_content_type()
    charset = msg.get_content_charset()
    content_disposition = msg.get_content_disposition()
    payload = None

    #don't decode plain text or attachment
    if content_type == 'text/plain' or content_disposition == 'attachment':
        payload = msg.get_payload()

    #decode everything else
    else:
        payload = str(msg.get_payload(decode=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]

    if payload:
        print(f'\n{payload}\n')
        write_mbox(f'\n{payload}\n', mboxfile)

def process_message(msg, mboxfile):
    if msg.is_multipart():
        multipart_message(msg, mboxfile)
    else:
        message_id = msg['Message-ID']
        date = msg['Date']
        if message_id:
            print(f"From {message_id} {date}") 
            write_mbox(f"From {message_id} {date}", mboxfile) 
        set_headers(msg.items(), mboxfile)
        single_message(msg, mboxfile)

def write_mbox(output, mboxfile):
    with open(mboxfile, 'a') as fout:
        ouput = output.replace("\r\n", "\n")
        fout.write(output + '\n')

for filename in mbox_files:
    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.mbox'
        mbox            = mailbox.mbox(mbox_file)
        mbox_new        = mailbox.mbox(mbox_file_new)
        mbox_new.lock()

        for key, value in mbox.iteritems():
            try:
                process_message(mbox[key], mbox_file_new)

            except (AttributeError, KeyError, UnicodeEncodeError) as e:

                print(crayons.magenta(f"Error for '{mbox_file_new}' {e}"))
                continue

        mbox_new.flush
        mbox_new.unlock()
