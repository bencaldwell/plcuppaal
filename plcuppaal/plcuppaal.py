import os
import pyuppaal
import sys
import re
import xml.etree.ElementTree as ET
import argparse

class plcuppaal:
	"""plcuppaal converts an xml configuration file to a base Uppaal TA system.
	"""
	def __init__(self, configfile="", outputfile=""):
		self.configfile=configfile
		self.outputfile=outputfile
		self.inputs = []
		self.outputs = []
		self.templates = []
		self.iutname = "iut"
		self.envname = "env"

	def create(self):
		self.parse_config_file()
		self.append_iut_template()
		self.append_env_template()
		self.append_global_declarations()

		self.systemdeclaration = "system {}, {};\r\n".format(self.iutname, self.envname)
		nta = pyuppaal.NTA(	templates=self.templates,
							declaration=self.globaldeclaration,
							system=self.systemdeclaration)

		file=open(self.outputfile, 'w')
		file.write(nta.to_xml())
		file.close()

	def parse_config_file(self):
		"""Read the xml config file and extract inputs and outputs"""
		tree = ET.parse(self.configfile)
		root = tree.getroot()

		parms = root.findall('./STIMPARMS/PARM/TAG')
		self.inputs = []
		for sym in parms:
			tokens = re.split(r"\.", sym.text) # split the input tag into dot hierarchy and just use the last component as the tag
			self.inputs.append(tokens[-1])

		parms = root.findall('./OBSPARMS/PARM/TAG')
		for sym in parms:
			tokens = re.split(r"\.", sym.text) # split the input tag into dot hierarchy and just use the last component as the tag
			self.outputs.append(tokens[-1])

	def append_iut_template(self):
		templatename=self.iutname
    	
    	# create one location
		locations = []
		initlocation = pyuppaal.Location(name="id0")
		locations.append(initlocation)

		#create a transition for each input with "ch<input>?" sync
		transitions = []
		for sym in self.inputs:
			#false guard transition
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="in"+sym+"Off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==0",
												synchronisation="ch"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

			#true guard transition
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="in"+sym+"On",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==1",
												synchronisation="ch"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

		for sym in self.outputs:
			#assign a true value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="out"+sym+"On",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=1",
												synchronisation="ch"+sym+"!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

			#assign a false value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="out"+sym+"Off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=0",
												synchronisation="ch"+sym+"!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

		template = pyuppaal.Template(	templatename,
										initlocation=initlocation,
										locations=locations,
										transitions=transitions)
		template.assign_ids()
		template.layout()
		self.templates.append(template)


	def append_env_template(self):
		templatename=self.envname
    	
		# create one location
		locations = []
		initlocation = pyuppaal.Location(name="id0")
		locations.append(initlocation)

		#create a transition for each output with "ch<output>?" sync
		transitions = []
		for sym in self.outputs:
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="out"+sym+"On",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==1",
												synchronisation="ch"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="out"+sym+"Off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==0",
												synchronisation="ch"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

		for sym in self.inputs:
			#assign a value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="in"+sym+"Off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=0",
												synchronisation="ch"+sym+"!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name="in"+sym+"On",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=1",
												synchronisation="ch"+sym+"!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

		template = pyuppaal.Template(	templatename,
										initlocation=initlocation,
										locations=locations,
										transitions=transitions)
		template.assign_ids()
		template.layout()
		self.templates.append(template)

	def append_global_declarations(self):
		declitems = []
		declitems.append("//inputs\r\n")
		declitems.append("int[0,1] ")
		for sym in self.inputs[:-1]:
			declitems.append(sym + ", ")
		declitems.append(self.inputs[-1] + ";\r\n")

		declitems.append("//outputs\r\n")
		declitems.append("int[0,1] ")
		for sym in self.outputs[:-1]:
			declitems.append(sym + ", ")
		declitems.append(self.outputs[-1] + ";\r\n")
        
		declitems.append("\r\n//input sync channels\r\n")
		declitems.append("broadcast chan ")
		for sym in self.inputs[:-1]:
			declitems.append("ch"+sym+",")
		declitems.append("ch"+self.inputs[-1]+";\r\n")

		declitems.append("\r\n//output sync channels\r\n")
		declitems.append("broadcast chan ")
		for sym in self.outputs[:-1]:
			declitems.append("ch"+sym+",")
		declitems.append("ch"+self.outputs[-1]+";\r\n")
        
		self.globaldeclaration =  ''.join(declitems)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("configfile", help="the plc software configuration file")
	parser.add_argument("outputfile", help="the file to write the uppaal ta into")
	args = parser.parse_args()
	print args
	p = plcuppaal(configfile=args.configfile, outputfile=args.outputfile)
	p.create()
	