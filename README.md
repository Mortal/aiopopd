# mailtk

Email client based on an [asyncio Tkinter event loop](https://github.com/Mortal/aiotkinter.git).

## Goals

The first pre-alpha version will be released Soon™.
Until then, the following vaporware goals should be kept in mind during development:

* Fast GUI, aggressively displaying cached mail folder data
* Native Google API client implementation for Gmail
* Native Exchange Web Services implementation for corporate email
* IMAP-client for all others
* Rich internal account interface for displaying partially completed folder lists

## Configuration

Create a file named `accounts.ini` in the directory from which you run
`python -m mailtk`. The file is parsed by `mailtk/accounts/config.py`,
and its structure is roughly as follows:

Each section specifies a single IMAP/EWS/Gmail connection,
and the `class` option is required and should be a dotted path
to one of the account classes in `mailtk/accounts/`,
e.g. `mailtk.accounts.imap.ImapAccount`.
The rest of the options should match the names of the parameters of
the `initialize` classmethod of the account class (sans the `loop`),
e.g. host, port, username and password for ImapAccount
(passing "ssl=1" if the IMAP server uses TLS).

The `password` option in each section is special and should be either of the form
`plain:P4SSW0RD` for a plaintext password, or `pass:arg` to use the first line
of output from [`pass arg`](https://www.passwordstore.org/) as the password.
You may extend `get_password_from_spec` in `mailtk/accounts/config.py`

### Gmail

To use the Gmail account class, you need to create
`mailtk/accounts/client_secret.json` from the Python Gmail quickstart tutorial.
