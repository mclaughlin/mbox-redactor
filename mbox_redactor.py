#!/usr/bin/env python

"""
Script used to redact words from email in mbox format
"""

import mailbox
import email
import os
import shutil
import csv
import configparser
import time
import re
import nltk
from nltk.corpus import stopwords


__version__ = '0.0.1'

def set_headers(headers, mboxfile, cfg):
    for key, value in headers:
        if key is not 'subject':
            redaction=False
        else:
            redaction=True
        write_mbox(f'{key}: {value}', mboxfile, cfg, redaction)
    write_mbox('\r\n', mboxfile, cfg)

def multipart_message(msg, mboxfile, stop, cfg):

    messages       = list(msg.walk())
    sub_msg_count  = 0
    sub_messages   = {}
    boundary_count = {}

    if cfg['cli_output']:
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

        if cfg['cli_output']:
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
            write_mbox(f'From {message_id} {date}', mboxfile, cfg)
            set_headers(part.items(), mboxfile, cfg)
            mbox_boundary = part.get_boundary()

        #if part contains sub-messages
        elif type(part) is email.message.Message \
                and type(part.get_payload()) is list:

            sub_messages[boundary] = part.get_payload()
            write_mbox(f'--{mbox_boundary}', mboxfile, cfg)
            set_headers(part.items(), mboxfile, cfg)

        #if individiual message AND message is a submessage of another message
        elif type(part) is email.message.Message \
                and any(part in val for val in sub_messages.values()):

            for key, value in sub_messages.items():
                boundary     = key
                message_list = value

                if part in message_list:
                    sub_msg_count += 1
                    write_mbox(f'--{boundary}', mboxfile, cfg)
                    set_headers(part.items(), mboxfile, cfg)
                    single_message(part, mboxfile, stop, cfg)

                if sub_msg_count == len(message_list):
                    write_mbox(f'--{boundary}--', mboxfile, cfg)
                    sub_msg_count = 0

        #if message is singlular and not a submessage of another message 
        elif mbox_boundary and type(part) is email.message.Message:

            write_mbox(f'--{mbox_boundary}', mboxfile, cfg)
            set_headers(part.items(), mboxfile, cfg)
            single_message(part, mboxfile, stop, cfg)

    if mbox_boundary:
        write_mbox(f'--{mbox_boundary}--\r\n', mboxfile, cfg)
        mbox_boundary = None

    if cfg['cli_output']:
        print(100*'>')
        print('\n')

def single_message(msg, mboxfile, stop, cfg):

    content_type = msg.get_content_type()
    charset = msg.get_content_charset()
    content_disposition = msg.get_content_disposition()
    payload = None

    if not cfg['decode_payload'] \
            or content_type == 'text/plain' \
            or content_type == 'text/calendar' \
            or content_disposition == 'attachment':

        #get raw payload
        payload = msg.get_payload()

        if content_type == 'text/plain' \
                or  (not cfg['decode_payload'] \
                and (content_type != 'text/calendar' \
                and  content_disposition != 'attachment')):

            #strip equals '=' character from end of line
            payload_lines = ''
            for line in payload.splitlines():
                payload_lines += line.rstrip('=')
            payload = payload_lines

    #decode everything else
    else:
        payload = str(msg.get_payload(decode=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]

    if payload:
        #all payloads (except attachments)
        if content_disposition != 'attachment':
            write_mbox(f'{payload}\r\n', mboxfile, cfg)
            write_names(payload, stop, cfg)
        #redact attachments if set
        elif content_disposition == 'attachment' \
                and cfg['redact_attachments']:
            write_mbox('[ATTACHMENT REDACTED]\r\n', mboxfile, cfg)
        #don't redact attachmets
        else:
            write_mbox(f'{payload}\r\n', mboxfile, cfg, redaction=False)

def process_message(msg, mboxfile, stop, cfg):
    if msg.is_multipart():
        multipart_message(msg, mboxfile, stop, cfg)
    else:
        message_id = msg['Message-ID']
        date = msg['Date']
        if message_id:
            message_id = strip_tags(message_id)
            date = date.replace(',', '')
            write_mbox(f"From {message_id} {date}", mboxfile, cfg)
        set_headers(msg.items(), mboxfile, cfg)
        single_message(msg, mboxfile, stop, cfg)

def write_mbox(output, mboxfile, cfg, redaction=True):
    if not cfg['dry_run']:
        with open(mboxfile, 'a') as fout:
            output = output.replace('\\r\\n','')
            output = (f'{output}\r\n')
            if redaction:
                output = redact(output, cfg)
            fout.write(output)

            if cfg['cli_output']:
                print(f'{output}')

def strip_tags(html):
    if html:
        for char in ['<', '>']:
            if char in html:
                html = html.replace(char, '')
    return html

def nl_preprocess(text, stop):
    text      = ' '.join([word for word in text.split() \
                                if word not in stop])
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

def extract_names(text, stop):
    names     = []
    sentences = nl_preprocess(text, stop)
    for tagged_sent in sentences:
        for chunk in nltk.ne_chunk(tagged_sent):
            if type(chunk) is nltk.tree.Tree and \
                    (chunk.label() == 'PERSON' or \
                     chunk.label() == 'GPE'):
                names.append(' '.join([c[0] for c in chunk]))
    return names

def write_names(text, stop, cfg):
    with open(cfg['names_file'], 'a+') as finfout:
        if cfg['extract_names']:
            names = extract_names(text, stop)
            for name in names:
                if name not in finfout.read():
                    output = (f'{name}\r\n')
                    finfout.write(output)

def redact(content, cfg):
    with open(cfg['redaction_file'], newline='') as fin:
        redaction_words = csv.reader(fin)
        for row in redaction_words:
            for word in row:
                content = content.replace(word, '[REDACTED]')
    return content

def false_to_bool(value):
    if value.title() == 'False':
        return False
    else:
        return value

def main():

    configs = configparser.ConfigParser()
    configs.read('config.ini')
    config = dict(configs.items('DEFAULT'))
    stop = stopwords.words('english')

    cfg = {}
    for key, value in config.items():
        cfg[key] = false_to_bool(value)

    #create needed input/output dirs
    if not os.path.exists(cfg['mbox_path']):
        os.makedirs(cfg['mbox_path'])
    if os.path.exists(cfg['mbox_path_new']):
        shutil.rmtree(cfg['mbox_path_new'])
    if os.path.exists(cfg['names_file']):
        os.remove(cfg['names_file'])
    os.makedirs(cfg['mbox_path_new'])

    mbox_files = os.listdir(cfg['mbox_path'])

    for filename in mbox_files:
        if (filename[-4:] == 'mbox'):

            mbox_file       = f"{cfg['mbox_path']}/{filename}"
            mbox_file_new   = f"{cfg['mbox_path_new']}/{filename[:-5]}.new.mbox"
            mbox            = mailbox.mbox(mbox_file)

            for key, value in mbox.iteritems():
                try:
                    process_message(mbox[key], mbox_file_new, stop, cfg)

                except (AttributeError, KeyError, UnicodeEncodeError) as e:

                    print(f"Error for '{mbox_file_new}' {e}")
                    continue

if __name__ == '__main__':
    main()

