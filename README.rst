mbox Redactor
==============================================
This utility redacts mbox email files (like those exported from Google Vault). It does so by first disassembling each message and sub-message into its individual parts and sub-parts (headers, payload, and boundary markers). It then redacts them based on a list of words defined in the 'redaction_words.csv' file, and then reassembles them in the same order they were disassembled.


Configuration (config.ini)
##########################

.. code-block:: xml

    [DEFAULT]
        mbox_path = ./mbox_files
        mbox_path_new = ./mbox_files_new
        redaction_file = ./redaction_words.csv
        redact_attachments = True
        extract_names = True
        names_file = ./extracted_names.csv
        decode_payload = False
        cli_output = True


Configuration Description
##########################

    mbox_path [= path]:
        This is where your unredacted mbox files go.
    
    mbox_path_new [= path]:
        This is where the script will place the redacted mbox files.
        
    redaction_file [= path]:
        This is a csv file that contains a list of words to redact from the mbox files.
        
    redact_attachments [= True/False]:
        If set to True, this will omit attachments, and in their place print [ATTACHMENT REDACTED].
        
    extract_names [= True/False]:
        If set to True, this uses the NLTK library to create a list potential names and save them in the 'names_file'.
        
    names_file [= path]:
        This is the location where the extracted names will be saved.
        
    decode_payload [= True/False]:
        If set to True, this will decode the payload of non-multipart messages based on the Content-Transfer-Encoding header.

    cli_output [= True/False]:
        This will output debugging info.

Run the script
##############

.. code-block:: bash

    python ./mbox-redactor/mbox-redactor.py

...or using pipenv::

    pipenv run ./mbox-redactor/mbox-redactor.py

