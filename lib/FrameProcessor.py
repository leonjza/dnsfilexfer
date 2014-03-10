import hashlib

class ProcessFrame(object):

	def __init__(self):
		self.position = 0
		self.expected = 0
		self.framestore = []
		self.out_file = ''

	def setOutfile(self, out_file):
		self.out_file = out_file

	def setData(self, frame):
		self.frame = frame

	def process(self):
		print '[INFO] Processing frame', self.frame

		try:
			frame_pos = int(self.frame[0:4])
		except Exception, e:
			print '[CRITICAL] Unable to determine a position. Error:', str(e)
			print '[CRITICAL] Maybe we are not getting a message really or `-X` was used with the sender.'
			return

		# first of all, check of this is not the last frame
		if len(str(self.frame).replace('0', '')) == 0:

			# check that we got all of the parts of the message
			if self.expected <> self.position:
				print '[ERROR] EOF received but complete message was not received.'
				print '[ERROR] Expected:', self.expected
				print '[ERROR] Position:', self.position
				return

			# merge the payloads, and checksum the result
			combined_payloads = ''.join(self.framestore).decode('hex')
			checksum = hashlib.sha1(combined_payloads).hexdigest()

			if self.checksum == checksum:

				print '[OK] Message seems to be intact and passes sha1 checksum of', self.checksum
				print '[OK] Message was received in', self.expected + 2, 'requests'

				# if we need to write this too a file, do it
				if self.out_file:
					print '[OK] Writing contents to', self.out_file
					with open(self.out_file,'w') as f:
						f.write(combined_payloads)
					print '[OK] Done writing contents to', self.out_file

				# else, just print it
				else:
					print 'Message identifier:', self.identifier, '\n'
					print '---START OF MESSAGE---'
					print combined_payloads
					print '---END OF MESSAGE---'

			else:
				print '[CRITICAL] Message does not pass checksum validation. Receive Failed.'
				self.position = 0
				self.expected = 0
				self.framestore = []

			return	

		# new input starting, read the amount of expected frames
		if frame_pos == 0:
			# split by : and and get the number of extected frames, minus this one
			self.expected = int(self.frame.split(':')[0])
			self.position = 0
			self.framestore = []
			return

		if frame_pos == 1:
			self.identifier = self.frame[4:].decode('hex')
			return

		# get the sha1hash of the end message we will be getting
		if frame_pos == 2:
			self.checksum = self.frame[4:]
			self.position = frame_pos
			return

		# if the current frame value is the stored one + 1, then this is the next one
		# to record, do it
		if frame_pos == self.position + 1:
			self.position = frame_pos
			self.framestore.append(self.frame[4:])
			return

		print '[WARNING]: Out of sync frames received! We are expecting frame', self.position + 1, 'but got', frame_pos
