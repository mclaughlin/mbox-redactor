mbox Redactor
==============================================
This utility redacts mbox email files (like those exported from Google Vault). It does so by first disassembling each message and sub-message into its individual parts and sub-parts (headers, payload, and boundary markers). It then redacts them based on a list of words defined in the 'redaction_words.csv' file, and then reassembles them in the same order they were dissasembled.


Configuration (config.ini)::

    [DEFAULT]
    mbox_path = ./mbox_files
    mbox_path_new = ./mbox_files_new
    redaction_file = ./redaction_words.csv
    decode_payload = False
    cli_output = False
    redact_attachments = True

Run the script::

    python ./mbox-redactor/mbox-redactor.py

...or using pipenv::

    pipenv run ./mbox-redactor/mbox-redactor.py

