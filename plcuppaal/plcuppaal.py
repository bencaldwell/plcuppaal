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
		self.dlyname = "dly"

	def create(self):
		self.parse_config_file()
		self.append_iut_template()
		self.append_env_template()
		self.append_buffer_template()
		self.append_global_declarations()
		self.append_system_declarations()

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

	def append_buffer_template(self):
		templatename = self.dlyname

		transitions = []
		locations = []
		initlocation = pyuppaal.Location(name="idle")
		locations.append(initlocation)
		delaylocation = pyuppaal.Location(	name="in_transit",
											invariant="x<=DELAY")
		locations.append(delaylocation)

		transition = pyuppaal.Transition(	source=initlocation, 
											target=delaylocation,
											assignment="x:=0",
											synchronisation="in?")
		transitions.append(transition)

		transition = pyuppaal.Transition(	source=delaylocation, 
											target=initlocation,
											synchronisation="out!")
		transitions.append(transition)

		template = pyuppaal.Template(	templatename,
										initlocation=initlocation,
										locations=locations,
										transitions=transitions,
										declaration="clock x;",
										parameter="broadcast chan &in, broadcast chan &out")
		template.assign_ids()
		template.layout()
		self.templates.append(template)


	def append_iut_template(self):
		templatename=self.iutname
    	
    	# create one location
		locations = []
		initlocation = pyuppaal.Location(name="id0")
		locations.append(initlocation)

		#create a transition for each input with "ch<input>iut?" sync
		#two sets of channels exists, those used by the environment "ch<input>" and those used by the iut "ch<input>iut"
		#the iut channels are delayed through a buffer template to model the adapter latency
		transitions = []
		for sym in self.inputs:
			#false guard transition
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==0",
												synchronisation="i_"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

			#true guard transition
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_on",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==1",
												synchronisation="i_"+sym+"?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

		for sym in self.outputs:
			#assign a true value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_on",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=1",
												synchronisation="o_"+sym+"!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

			#assign a false value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=0",
												synchronisation="o_"+sym+"!")
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
			location = pyuppaal.Location(	name=sym+"_on",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==1",
												synchronisation="o_"+sym+"_env?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation, 
												target=location,
												guard=sym+"==0",
												synchronisation="o_"+sym+"_env?")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location, 
												target=initlocation)
			transitions.append(transition)

		for sym in self.inputs:
			#assign a value to an output and sync
			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_off",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=0",
												synchronisation="i_"+sym+"_env!")
			transitions.append(transition)
			transition = pyuppaal.Transition(	source=location,
												target=initlocation)
			transitions.append(transition)

			#create a committed location simply to spread the graph out
			location = pyuppaal.Location(	name=sym+"_on",
											committed=True)
			locations.append(location)
			transition = pyuppaal.Transition(	source=initlocation,
												target=location,
												assignment=sym+":=1",
												synchronisation="i_"+sym+"_env!")
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
		
		declitems.append("//constants\r")
		declitems.append("const int DELAY = 1000;\r\n")

		declitems.append("//inputs\r")
		declitems.append("int[0,1] ")
		for sym in self.inputs[:-1]:
			declitems.append(sym + ", ")
		declitems.append(self.inputs[-1] + ";\r\n")

		declitems.append("//outputs\r")
		declitems.append("int[0,1] ")
		for sym in self.outputs[:-1]:
			declitems.append(sym + ", ")
		declitems.append(self.outputs[-1] + ";\r\n")
        
		declitems.append("//input sync channels\r")
		declitems.append("broadcast chan ")
		for sym in self.inputs[:-1]:
			declitems.append("i_"+sym+","+"i_"+sym+"_env,")
		declitems.append("i_"+self.inputs[-1]+","+"i_"+self.inputs[-1]+"_env"+";\r\n")

		declitems.append("//output sync channels\r")
		declitems.append("broadcast chan ")
		for sym in self.outputs[:-1]:
			declitems.append("o_"+sym+","+"o_"+sym+"_env,")
		declitems.append("o_"+self.outputs[-1]+","+"o_"+self.outputs[-1]+"_env"+";\r\n")
        
		self.globaldeclaration =  ''.join(declitems)

	def append_system_declarations(self):
		declitems = []
		declitems.append("//delay buffers\r")
		delaybuffers = []
		# delay from env to iut
		for sym in self.inputs:
			buffname = sym + "dly"
			declitems.append(buffname + " = " + self.dlyname + "(i_" + sym + "_env,i_"+sym+");\r")
			delaybuffers.append(buffname)

		# delay from iut to env
		for sym in self.outputs:
			buffname = sym + "dly"
			declitems.append(buffname + " = " + self.dlyname + "(o_" + sym + ",o_"+sym+"_env);\r")
			delaybuffers.append(buffname)

		declitems.append("\r//templates in the system\r")
		declitems.append("system ")
		declitems.append(self.envname)
		declitems.append(",")
		declitems.append(self.iutname)
		for buff in delaybuffers:
			declitems.append(",")
			declitems.append(buff)
		declitems.append(";\r\n")
		
		self.systemdeclaration = ''.join(declitems)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("configfile", help="the plc software configuration file")
	parser.add_argument("outputfile", help="the file to write the uppaal ta into")
	args = parser.parse_args()
	print args
	p = plcuppaal(configfile=args.configfile, outputfile=args.outputfile)
	p.create()
	