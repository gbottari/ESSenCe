#coding: utf-8

from time import sleep

import sys, os
sys.path.append(os.path.abspath('..'))

from system.server import Server

lost_filename = '/mnt/ram/lost.txt'
reply_filename = '/mnt/ram/replied.txt'


def peekFile(filename):
	try:
		f = open(filename,'r')
	except:
		return -1

	result = f.readline()
	f.close()
	return result


def main():
	server = Server()
	server.processor.detect()

	"""
	Printing
	"""

	print '#CPU / Freq / Temp / QoS'

	old_lost = int(peekFile(lost_filename))
	old_reply = int(peekFile(reply_filename))
	server.processor.updateFreq()
	server.processor.updateUtil()

	sleep(1)
	while True:
		lost = int(peekFile(lost_filename))
		reply = int(peekFile(reply_filename))
		server.processor.updateFreq()
		server.processor.updateUtil()

		if lost < 0 or reply < 0:
			qos = -1
		else:
			replied = reply - old_reply
			lost_now = lost - old_lost
			#print "replied = ",replied
			#print "lost = ",lost_now

			if replied == 0:
				qos = 1
			else:
				qos = float(replied - lost_now) / replied	
		
		string = ''		
		string += "%03.0f" % (server.processor.utilization * 100) + ' '
		string += "%01.3f" % (server.processor.freq) + ' '

		if qos >= 0:
			string += " %03.0f" % (qos * 100)

		print string
		
		old_reply = reply
		old_lost = lost
		
		sleep(1)

if __name__ == '__main__':
	main()