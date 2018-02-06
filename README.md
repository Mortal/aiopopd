POP3 server proxying to remote IMAP server
==========================================

aiopopd allows you to import your email on an IMAP server
into your Gmail account.

Since Gmail only supports retrieving email from a remote POP3 server,
not a remote IMAP server, this project implements a POP3 server that takes a
username and password from a client, uses the credentials to log on to another
IMAP server, and sends the email on that remote IMAP server to the POP3 client
(i.e. Gmail).

Security concerns
-----------------

By giving your IMAP password to Gmail, you are giving your IMAP password to Gmail.
If your IMAP provider forbids you from giving your password to strangers,
then you shouldn't give your password to Gmail!

If you decide to give your password to Gmail, then Gmail will send your password
along to aiopopd. If you don't control the configuration of aiopopd,
the server it is running on, or the DNS entry managing the domain name,
then you shouldn't give your password to Gmail!

Although there are standards for challenge-response authentication
(e.g. [CRAM-MD5](https://tools.ietf.org/html/rfc2195))
such that you could have a POP3 server proxying to a remote IMAP server
where the POP3 proxy never learns the client's password,
these standards are rarely implemented and enabled.

You should use a TLS certificate for your POP3 server.
Consider using Let's Encrypt to obtain a free TLS certificate:
The simplest way is by installing `certbot` and running
`sudo certbot certonly -d pop.example.com --webroot -w /var/www/pop.example.com/htdocs`,
assuming you have configured a webserver to serve http://pop.example.com from
`/var/www/pop.example.com/htdocs`.

Running aiopopd
---------------

* (Install python3 and [pipenv](https://github.com/pypa/pipenv))
* Clone the project with git: `git clone https://github.com/Mortal/aiopopd`
* `cd aiopopd`
* `pipenv install --three && pipenv shell`
* To run a POP3 server, listening on port 9955, proxying to a fixed IMAP server:
  `python -m aiopopd -H imap.example.com -p 993 --imap-ssl -P 9955 -n --ssl-key key.pem --ssl-cert fullchain.pem --ssl-generate`

Implementation
--------------

aiopopd is implemented in Python 3 using asyncio and is closely modeled after
the [aiosmtpd](https://github.com/aio-libs/aiosmtpd) project.

The IMAP client portion was taken from the [mailtk](https://github.com/Mortal/mailtk) project.

The POP3 server runs in a single thread, while each IMAP client runs on a separate thread
(since the IMAP client implementation is synchronous).

`client.py` - POP3 client for testing
-------------------------------------

Before testing with your Gmail account,
it can be useful to check manually that your configuration works with any POP3 client.

Usage: `python3 client.py -u USERNAME`

By default, `client.py` asks for your IMAP password on standard input.
For more options, see `python3 client.py --help`.

If you use the [standard UNIX password manager](https://www.passwordstore.org/),
you can use the option `-p pass:NAME` to retrieve the password using the `pass NAME` command.
