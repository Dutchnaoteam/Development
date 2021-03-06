# requirements: pexpect

import subprocess as sub
import threading, re, time, sys, pexpect, os

def parse_avahi(avahi):
	output, _ = avahi.communicate()

	# filter only the lines starting with '='
	lines = re.findall(r'=;\S+', output)

	# substitute ; for , and add quotes around each element to eval the data
	# into a Python list
	lines = [ '[' + re.sub(r';', r',', l) + ']' for l in lines]
	lines = [ re.sub(r'([^,]+)', r'"\1"', l) for l in lines]
	for l in lines:
		if l[-1] == ';':
			l = l[:-1]
	lines = [eval(l) for l in lines]

	return [(l[7], l[3]) for l in lines]

# returns a list of robot names along with their IP address
def get_robots():
	while True:
		# get new data
		avahi = sub.Popen(["avahi-browse", "-rp", "--no-db-lookup", "_nao._tcp"],
			stdout=sub.PIPE)
		time.sleep(1)
		avahi.kill()
		current = parse_avahi(avahi)

		# prompt the user
		print "Found Naos: "
		for ip, name in current:
			print name, ip

		print ""
		valid_input = False

		# validate input
		while not valid_input:
			choice = raw_input("Do you want to: [c]ontinue, [r]efresh, [q]uit?\n> ").lower()
			if choice in ['c', 'r', 'q']:
				valid_input = True
			else:
				print "Error, invalid input."

		# parse input
		if choice == 'c': break
		if choice == 'r': continue
		if choice == 'q': sys.exit(0)

	return current

# sends a file to the nao
def send_path(local_path, remote_path, ip):
	args = ["-r", local_path, "nao@%s:%s" % (ip, remote_path)]
	child = pexpect.spawn("rsync", args)
	index = child.expect(["password", "Password", pexpect.EOF, pexpect.TIMEOUT])

	if index == 0 or index == 1:
		child.sendline("nao")
	elif index == 2:
		print "Error, EOF"
	elif index == 3:
		print "Error, timeout"

	child.expect(pexpect.EOF)


# prompts for a folder and pushes to the naos
def push_code(naos):
	print ""
	path = raw_input("Please give the path to your naoqi/ folder:\n> ")

	# push the code to each nao
	for ip, name in naos:
		send_path(path, "~/", ip)

# creates a naoinfo.txt for each Nao and pushes it
def setup_naoinfo(naos):
	print ""
	team = raw_input("Please enter your team's number:\n> ")

	for ip, name in naos:
		player = raw_input("Please enter %s's player number:\n> " % name)
		pinfo = """%s
%s

Regel 1 is de robot
Regel 2 is het team
* autogenerated by match_preparation.py * """ % (player, team)

		# write the info to a temp-file
		with open('NAOINFO.txt', 'w') as f:
			f.write(pinfo)

		# push the naoinfo
		send_path('NAOINFO.txt', "~/naoinfo", ip)

	# remove the leftover naoinfo.txt
	os.remove('NAOINFO.txt')



def main():
	robots = get_robots()
	push_code(robots)
	setup_naoinfo(robots)

	print "Preparation completed succesfully."

if __name__ == '__main__':
	main()