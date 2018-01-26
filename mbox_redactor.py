#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import email
import os
import shutil
import csv

__version__ = '0.0.1'

mbox_path          = './mbox_files'
mbox_path_new      = './mbox_files_new'
redaction_file     = './redaction_words.csv'
decode_payload     = False
cli_output         = False
redact_attachments = True

if os.path.exists(mbox_path_new):
    shutil.rmtree(mbox_path_new)

os.makedirs(mbox_path_new)
mbox_files = os.listdir(mbox_path)

def set_headers(headers, mboxfile):
    for key, value in headers:
        write_mbox(f'{key}: {value}', mboxfile)
    write_mbox('\r\n', mboxfile)

def multipart_message(msg, mboxfile):

    messages       = list(msg.walk())
    sub_msg_count  = 0
    sub_messages   = {}
    boundary_count = {}

    if cli_output:
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

        if cli_output:
            print(100*'#')
            print(f'message type.......: {type(part)}')
            print(f'message object ID..: {id(part)}')
            print(f'boundary...........: {boundary}')
            print(f'content type.......: {part.get_content_type()}')
            print(f'charset............: {part.get_content_charset()}')
            print(f'headers............: {part.items()}')
            print(f'content_disposition: {part.get_content_disposition()}')
            print(f"message-id.........: {part['Message-ID']}")
            print(50*'. ')
            #print(msg)
            #print(100*'~')
            print('**OUTPUT**')

        #if part is a group of messages
        if type(part) is mailbox.mboxMessage:

            message_id = strip_tags(message_id)
            date = date.replace(',', '')
            write_mbox(f'From {message_id} {date}', mboxfile)
            set_headers(part.items(), mboxfile)
            mbox_boundary = part.get_boundary()

        #if part contains sub-messages
        elif type(part) is email.message.Message \
                and type(part.get_payload()) is list:

            sub_messages[boundary] = part.get_payload()
            write_mbox(f'--{mbox_boundary}', mboxfile)
            set_headers(part.items(), mboxfile)

        #if individiual message AND message is a submessage of another message
        elif type(part) is email.message.Message \
                and any(part in val for val in sub_messages.values()):

            for key, value in sub_messages.items():
                boundary     = key
                message_list = value

                if part in message_list:
                    sub_msg_count += 1
                    write_mbox(f'--{boundary}', mboxfile)
                    set_headers(part.items(), mboxfile)
                    single_message(part, mboxfile)

                if sub_msg_count == len(message_list):
                    write_mbox(f'--{boundary}--', mboxfile)
                    sub_msg_count = 0

        #if message is singlular and not a submessage of another message 
        elif mbox_boundary and type(part) is email.message.Message:

            write_mbox(f'--{mbox_boundary}', mboxfile)
            set_headers(part.items(), mboxfile)
            single_message(part, mboxfile)

    if mbox_boundary:
        write_mbox(f'--{mbox_boundary}--\r\n', mboxfile)
        mbox_boundary = None

    if cli_output:
        print(100*'>')
        print('\n')

def strip_tags(html):
    if html:
        for char in ['<', '>']:
            if char in html:
                html = html.replace(char, '')
    return html

def single_message(msg, mboxfile):

    content_type = msg.get_content_type()
    charset = msg.get_content_charset()
    content_disposition = msg.get_content_disposition()
    payload = None

    if not decode_payload \
            or content_type == 'text/plain' \
            or content_type == 'text/calendar' \
            or content_disposition == 'attachment':

        #get raw payload
        payload = msg.get_payload()

        if content_type == 'text/plain' \
                or  (not decode_payload \
                and (content_type != 'text/calendar' \
                and  content_disposition != 'attachment')):

            #strip equals '=' character from end of line
            payload_lines = ''
            for line in payload.splitlines():
                payload_lines += line.rstrip('=')
            payload = payload_lines

    #decode everything else
    else:
        payload = str(msg.get_payload(decode_payload=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]

    if payload:
        #all payloads (except attachments)
        if content_disposition != 'attachment':
            write_mbox(f'{payload}\r\n', mboxfile)
        #redact attachments if set
        elif content_disposition == 'attachment' \
                and redact_attachments:
            write_mbox('[ATTACHMENT REDACTED]\r\n', mboxfile)
        #don't redact attachmets
    else:
            write_mbox(f'{payload}\r\n', mboxfile, redaction=False)

def process_message(msg, mboxfile):
    if msg.is_multipart():
        multipart_message(msg, mboxfile)
    else:
        message_id = msg['Message-ID']
        date = msg['Date']
        if message_id:
            message_id = strip_tags(message_id)
            date = date.replace(',', '')
            write_mbox(f"From {message_id} {date}", mboxfile)
        set_headers(msg.items(), mboxfile)
        single_message(msg, mboxfile)

def write_mbox(output, mboxfile, redaction=True):
    with open(mboxfile, 'a') as fout:
        output = output.replace('\\r\\n','')
        output = (f'{output}\r\n')
        if redaction:
            output = redact(output, redaction_file)
        fout.write(output)

        if cli_output:
            print(f'{output}')

def redact(content, redactionfile):
    with open(redactionfile, newline='') as fin:
        redaction_words = csv.reader(fin)
        for row in redaction_words:
            for word in row:
                content = content.replace(word, '[REDACTED]')
    return content

for filename in mbox_files:
    if (filename[-4:] == 'mbox'):

        mbox_file       = f'{mbox_path}/{filename}'
        mbox_file_new   = f'{mbox_path_new}/{filename[:-5]}.new.mbox'
        mbox            = mailbox.mbox(mbox_file)

        for key, value in mbox.iteritems():
            try:
                process_message(mbox[key], mbox_file_new)

            except (AttributeError, KeyError, UnicodeEncodeError) as e:

                print(f"Error for '{mbox_file_new}' {e}")
                continue
