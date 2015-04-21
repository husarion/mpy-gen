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

class Arg:
	type = None
	optional = None
	defaultValue = None

class Method:
	name = None
	returnType = None
	args = None

	def needArrayCall(self):
		if len(self.args) > 3:
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

def findMethod(methods, name):
	for m in methods:
		if m.name == name:
			return m
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
			objMethod.returnType = parts[0]
			objMethod.args = parseArgs(parts[2:])

			curObj.removeMethod(objMethod.name)
			curObj.methods.append(objMethod)

		if cmd == "endclass":
			ctx.addClass(curObj)
			curObj = None
			pass

def parseArgs(argsArray):
	args = []
	for a in argsArray:
		arg = Arg()
		if a[0] == "[" and a[-1] == "]":
			arg.type = a[1:-1]
			arg.optional = True
		else:
			arg.type = a
			arg.optional = False
		args.append(arg)
	return args

