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
import nltk
from nltk.corpus import stopwords


__version__ = '0.0.1'

def set_headers(headers, fout, cfg, redaction_words):
    for key, value in headers:
        redaction = (key == 'subject')
        write_mbox(f'{key}: {value}', fout, cfg, redaction_words, redaction)
    write_mbox('\r\n', fout, cfg, redaction_words)

def multipart_message(msg, fout, stop, cfg, redaction_words, seen_names):

    messages       = list(msg.walk())
    sub_msg_count  = 0
    sub_messages   = {}
    mbox_boundary  = None

    if cfg['cli_output']:
        print(100*'<')
        print(len(messages))
        print(messages)

    for part in messages:

        content_type = part.get_content_type()
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
            print('**OUTPUT**')

        #if part is a group of messages
        if isinstance(part, mailbox.mboxMessage):

            message_id = strip_tags(message_id)
            date = date.replace(',', '')
            write_mbox(f'From {message_id} {date}', fout, cfg, redaction_words)
            set_headers(part.items(), fout, cfg, redaction_words)
            mbox_boundary = part.get_boundary()

        #if part contains sub-messages
        elif isinstance(part, email.message.Message) \
                and isinstance(part.get_payload(), list):

            sub_messages[boundary] = part.get_payload()
            write_mbox(f'--{mbox_boundary}', fout, cfg, redaction_words)
            set_headers(part.items(), fout, cfg, redaction_words)

        #if individual message AND message is a submessage of another message
        elif isinstance(part, email.message.Message) \
                and any(part in val for val in sub_messages.values()):

            for key, value in sub_messages.items():
                boundary     = key
                message_list = value

                if part in message_list:
                    sub_msg_count += 1
                    write_mbox(f'--{boundary}', fout, cfg, redaction_words)
                    set_headers(part.items(), fout, cfg, redaction_words)
                    single_message(part, fout, stop, cfg, redaction_words, seen_names)

                if sub_msg_count == len(message_list):
                    write_mbox(f'--{boundary}--', fout, cfg, redaction_words)
                    sub_msg_count = 0

        #if message is singular and not a submessage of another message
        elif mbox_boundary and isinstance(part, email.message.Message):

            write_mbox(f'--{mbox_boundary}', fout, cfg, redaction_words)
            set_headers(part.items(), fout, cfg, redaction_words)
            single_message(part, fout, stop, cfg, redaction_words, seen_names)

    if mbox_boundary:
        write_mbox(f'--{mbox_boundary}--\r\n', fout, cfg, redaction_words)

    if cfg['cli_output']:
        print(100*'>')
        print('\n')

def single_message(msg, fout, stop, cfg, redaction_words, seen_names):

    content_type = msg.get_content_type()
    content_disposition = msg.get_content_disposition()
    payload = None

    if not cfg['decode_payload'] \
            or content_type == 'text/plain' \
            or content_type == 'text/calendar' \
            or content_disposition == 'attachment':

        #get raw payload
        payload = msg.get_payload()

        if content_type == 'text/plain' \
                or (not cfg['decode_payload'] \
                and content_type != 'text/calendar' \
                and content_disposition != 'attachment'):

            #strip equals '=' character from end of line
            payload = ''.join(line.rstrip('=') for line in payload.splitlines())

    #decode everything else
    else:
        payload = str(msg.get_payload(decode=True))
        if payload.startswith("b'") and payload.endswith("'"):
            payload = payload[2:-1]

    if payload:
        #all payloads (except attachments)
        if content_disposition != 'attachment':
            write_mbox(f'{payload}\r\n', fout, cfg, redaction_words)
            write_names(payload, stop, cfg, seen_names)
        #redact attachments if set
        elif cfg['redact_attachments']:
            write_mbox('[ATTACHMENT REDACTED]\r\n', fout, cfg, redaction_words)
        #don't redact attachments
        else:
            write_mbox(f'{payload}\r\n', fout, cfg, redaction_words, redaction=False)

def process_message(msg, fout, stop, cfg, redaction_words, seen_names):
    if msg.is_multipart():
        multipart_message(msg, fout, stop, cfg, redaction_words, seen_names)
    else:
        message_id = msg['Message-ID']
        date = msg['Date']
        if message_id:
            message_id = strip_tags(message_id)
            date = date.replace(',', '')
            write_mbox(f'From {message_id} {date}', fout, cfg, redaction_words)
        set_headers(msg.items(), fout, cfg, redaction_words)
        single_message(msg, fout, stop, cfg, redaction_words, seen_names)

def write_mbox(output, fout, cfg, redaction_words, redaction=True):
    if not cfg['dry_run']:
        output = output.replace('\\r\\n', '')
        output = f'{output}\r\n'
        if redaction:
            output = redact(output, redaction_words)
        fout.write(output)

        if cfg['cli_output']:
            print(output)

def strip_tags(html):
    if html:
        html = html.replace('<', '').replace('>', '')
    return html

def nl_preprocess(text, stop):
    text      = ' '.join(word for word in text.split() if word not in stop)
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

def extract_names(text, stop):
    names     = []
    sentences = nl_preprocess(text, stop)
    for tagged_sent in sentences:
        for chunk in nltk.ne_chunk(tagged_sent):
            if isinstance(chunk, nltk.tree.Tree) and \
                    chunk.label() in ('PERSON', 'GPE'):
                names.append(' '.join(c[0] for c in chunk))
    return names

def write_names(text, stop, cfg, seen_names):
    if cfg['extract_names']:
        names = [n for n in extract_names(text, stop) if n not in seen_names]
        if names:
            seen_names.update(names)
            with open(cfg['names_file'], 'a') as fout:
                for name in names:
                    fout.write(f'{name}\r\n')

def redact(content, redaction_words):
    for word in redaction_words:
        content = content.replace(word, '[REDACTED]')
    return content

def load_redaction_words(path):
    words = []
    with open(path, newline='') as fin:
        for row in csv.reader(fin):
            words.extend(row)
    return words

def parse_bool(value):
    lower = value.strip().lower()
    if lower == 'true':
        return True
    if lower == 'false':
        return False
    return value

def main():

    configs = configparser.ConfigParser()
    configs.read('config.ini')
    config = dict(configs.items('DEFAULT'))
    stop = set(stopwords.words('english'))

    cfg = {key: parse_bool(value) for key, value in config.items()}
    redaction_words = load_redaction_words(cfg['redaction_file'])
    seen_names = set()

    #create needed input/output dirs
    if not os.path.exists(cfg['mbox_path']):
        os.makedirs(cfg['mbox_path'])
    if os.path.exists(cfg['mbox_path_new']):
        shutil.rmtree(cfg['mbox_path_new'])
    if os.path.exists(cfg['names_file']):
        os.remove(cfg['names_file'])
    os.makedirs(cfg['mbox_path_new'])

    for filename in os.listdir(cfg['mbox_path']):
        if not filename.endswith('.mbox'):
            continue

        mbox_file     = os.path.join(cfg['mbox_path'], filename)
        mbox_file_new = os.path.join(cfg['mbox_path_new'], f'{filename[:-5]}.new.mbox')
        mbox          = mailbox.mbox(mbox_file)

        with open(mbox_file_new, 'a') as fout:
            for key in mbox.keys():
                try:
                    process_message(mbox[key], fout, stop, cfg, redaction_words, seen_names)
                except (AttributeError, KeyError, UnicodeEncodeError) as e:
                    print(f"Error for '{mbox_file_new}': {e}")

if __name__ == '__main__':
    main()
