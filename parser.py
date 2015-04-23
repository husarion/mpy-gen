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
	subscript = None

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
		return not self.constructor and not self.subscript
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
	objClasses = None
	objGlobals = None

	def __init__(self):
		self.objClasses = []
		self.objGlobals = []

	def addClass(self, o):
		self.objClasses.append(o)
	def addGlobal(self, o):
		self.objGlobals.append(o)

	def findClass(self, name):
		for cl in self.objClasses:
			if cl.name == name:
				return cl
		return None

def genTree(ctx, txt):
	lines = txt.split("\n")

	for line in lines:
		line = line.strip()
		if len(line) == 0:
			continue

		(cmd, rest) = parseLine(line)

		if cmd == "global":
			parts = rest.split(":")
			objType = parts[0]
			objName = parts[1]

			ctx.addGlobal({'type': objType, 'name': objName})

		if cmd == "class":
			parts = rest.split(":")
			objName = parts[0]
			print("new class", objName)
			curObj = Class()
			curObj.name = objName
			curObj.storeValue = False
			curObj.methods = []
			curObj.parents = []

			if len(parts) >= 2:
				for p in parts[1:]:
					baseClass = ctx.findClass(p)
					for m in baseClass.methods:
						curObj.removeMethod(m.name)
					curObj.methods += baseClass.methods

		if cmd == "method":
			if curObj is None:
				continue

			parts = rest.split(":")

			objMethod = Method()
			objMethod.name = parts[1]
			objMethod.returnType = parseRetType(parts[0])
			objMethod.args = parseArgs(parts[2:])
			objMethod.constructor = False
			objMethod.subscript = False

			curObj.removeMethod(objMethod.name)
			curObj.methods.append(objMethod)

		if cmd == "constructor":
			parts = rest.split(":")

			objMethod = Method()
			objMethod.name = "constructor"
			objMethod.returnType = parseRetType("void")
			objMethod.args = parseArgs(parts[0:])
			objMethod.constructor = True
			objMethod.subscript = False

			curObj.removeMethod(objMethod.name)
			curObj.methods.append(objMethod)

		if cmd == "subscript":
			parts = rest.split(":")

			objMethod = Method()
			objMethod.name = "subscript"
			objMethod.returnType = parseRetType(parts[0])
			objMethod.args = [objMethod.returnType]
			objMethod.constructor = False
			objMethod.subscript = True

			curObj.removeMethod(objMethod.name)
			curObj.methods.append(objMethod)

		if cmd == "storevalue":
			curObj.storeValue = True

		if cmd == "endclass":
			ctx.addClass(curObj)
			curObj = None
			pass

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

		arg.customType = arg.fullType[0] == "h" or arg.fullType[0] == "I"
		if arg.fullType[-1] == "*":
			arg.isRef = True
			arg.type = arg.fullType[:-1]
		else:
			arg.isRef = False
			arg.type = arg.fullType

		m = re.match("(.*)\[(.*),(.*)\]", arg.fullType)
		if m:
			arg.fullType = m.group(1)
			arg.type = m.group(1)
			arg.subType = m.group(2)
			arg.dir = m.group(3)

		args.append(arg)
	return args

