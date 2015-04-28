import re

class GlobalVar:
	pass

class Class:
	name = None
	methods = None
	parents = None

	def removeMethod(self, name):
		for m in self.methods:
			if m.name == name:
				self.methods.remove(m)
				return
	
	def hasConstructor(self):
		for m in self.methods:
			if m.constructor:
				return True
		return False
	def hasSubscript(self):
		for m in self.methods:
			if m.subscript:
				return True
		return False

class Arg:
	type = None # only typename
	fullType = None # with ref/pointer
	optional = None
	defaultValue = None
	isRef = None
	customType = None
	subType = None # for lists
	dir = None # in, out, inout

	def isIn(self):
		return self.dir == "in" or self.dir == "inout"
	def isOut(self):
		return self.dir == "out" or self.dir == "inout"

	def __eq__(self, other):
		return self.type == other
	def __ne__(self, other):
		return not self.__eq__(other)

class Method:
	name = None
	returnType = None
	args = None
	constructor = None
	destructor = None
	subscript = None

	def __init__(self):
		self.returnType = parseRetType("void")
		self.args = []
		self.constructor = False
		self.destructor = False
		self.subscript = False

	def needArrayCall(self):
		if self.subscript:
			return False
		if len(self.args) > 2: # self + 2 args
			return True
		for a in self.args:
			if a.optional:
				return True
		return False
	def getMinArgs(self):
		cnt = 0
		for a in self.args:
			if not a.optional:
				cnt += 1
		return cnt
	def getMaxArgs(self):
		return len(self.args)
	def isRegularMethod(self):
		return not self.constructor and not self.destructor and not self.subscript
	def hasSelf(self):
		return not self.constructor

def parseLine(line):
	parts = line.split(":", 1)
	cmd = parts[0]
	if len(parts) == 1:
		parts.append("")
	return cmd, parts[1]

curObj = None

class ParserContext:
	name = None
	objClasses = None
	objGlobals = None
	inclues = None
	namespaces = None
	strStartNum = None

	def __init__(self):
		self.objClasses = []
		self.objGlobals = []
		self.inclues = []
		self.namespaces = []

	def addClass(self, o):
		self.objClasses.append(o)
	def addGlobal(self, o):
		self.objGlobals.append(o)

	def findClass(self, name):
		for cl in self.objClasses:
			if cl.name == name:
				return cl
		return None

	def isPolymorphic(self, cl):
		if len(cl.parents) > 0:
			return True
		for c in self.objClasses:
			if cl in c.parents:
				return True
		return False

	def parseData(self, txt, extern = False):
		lines = txt.split("\n")

		for line in lines:
			line = line.strip()
			if len(line) == 0:
				continue

			(cmd, rest) = parseLine(line)

			if not extern and cmd == "name":
				parts = rest.split(":")
				self.name = parts[0]

			if not extern and cmd == "include":
				parts = rest.split(":")
				self.inclues.append(parts[0])

			if not extern and cmd == "namespace":
				parts = rest.split(":")
				self.namespaces.append(parts[0])

			if not extern and cmd == "num":
				parts = rest.split(":")
				self.strStartNum = int(parts[0], 0)

			if cmd == "global":
				parts = rest.split(":")
				objType = parts[0]
				objName = parts[1]

				self.addGlobal({'type': objType, 'name': objName, 'extern': extern})

			if cmd == "class":
				parts = rest.split(":")
				objName = parts[0]
				print("new class", objName)
				curObj = Class()
				curObj.extern = extern
				curObj.name = objName
				curObj.storeValue = False
				curObj.methods = []
				curObj.parents = []

				if len(parts) >= 2:
					for p in parts[1:]:
						baseClass = self.findClass(p)
						for m in baseClass.methods:
							curObj.removeMethod(m.name)
						curObj.methods += baseClass.methods
						curObj.parents.append(baseClass)

			if not extern and cmd == "method":
				if curObj is None:
					continue

				parts = rest.split(":")

				objMethod = Method()
				objMethod.name = parts[1]
				objMethod.returnType = parseRetType(parts[0])
				objMethod.args = parseArgs(parts[2:])

				curObj.removeMethod(objMethod.name)
				curObj.methods.append(objMethod)

			if not extern and cmd == "constructor":
				parts = rest.split(":")

				objMethod = Method()
				objMethod.name = "constructor"
				objMethod.returnType = parseRetType("void")
				objMethod.args = parseArgs(parts[0:])
				objMethod.constructor = True

				curObj.removeMethod(objMethod.name)
				curObj.methods.append(objMethod)

				objMethod = Method()
				objMethod.name = "__del__"
				objMethod.returnType = parseRetType("void")
				objMethod.destructor = True

				curObj.removeMethod(objMethod.name)
				curObj.methods.append(objMethod)

			if not extern and cmd == "subscript":
				parts = rest.split(":")

				objMethod = Method()
				objMethod.name = "subscript"
				objMethod.returnType = parseRetType(parts[0])
				objMethod.args = [objMethod.returnType]
				objMethod.constructor = False
				objMethod.subscript = True

				curObj.removeMethod(objMethod.name)
				curObj.methods.append(objMethod)

			if not extern and cmd == "storevalue":
				curObj.storeValue = True

			if cmd == "endclass":
				self.addClass(curObj)
				curObj = None

		if not extern and self.name is None:
			print("Name must be specified in export file. Eg.")
			print("name:myproject")
			return False
		if not extern and self.strStartNum is None:
			print("String start number must be specified in export file. Eg.")
			print("num:0x01000000")
			return False
		return True

def parseRetType(ret):
	r = parseArgs([ret])
	return r[0]
def parseArgs(argsArray):
	args = []
	for a in argsArray:
		arg = Arg()
		a = a.replace("&", "*")
		if a[0] == "[" and a[-1] == "]":
			arg.fullType = a[1:-1]
			arg.optional = True
		else:
			arg.fullType = a
			arg.optional = False

		if arg.fullType[-1] == "*":
			arg.isRef = True
			arg.type = arg.fullType[:-1]
		else:
			arg.isRef = False
			arg.type = arg.fullType
		arg.customType = isCustomType(arg.type)

		m = re.match("(.*)\[(.*),(.*)\]", arg.fullType)
		if m:
			arg.fullType = m.group(1)
			arg.type = m.group(1)
			arg.subType = m.group(2)
			arg.dir = m.group(3)

		args.append(arg)
	return args

def isCustomType(type):
	return type not in ["int", "int16_t", "bool", "float", "byte", "buffer"]
