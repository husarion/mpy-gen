class GlobalVar:
	pass
class Class:
	pass
class Method:
	pass

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
			curObj = { 'type': 'class', 'name': objName, 'methods': [] }

		if cmd == "method":
			if curObj is None:
				continue

			parts = rest.split(":")

			objMethod = {
					'name': parts[1],
					'returnType': parts[0],
					'args': parts[2:],
				}

			curObj["methods"].append(objMethod)

		if cmd == "endclass":
			ctx.addClass(curObj)
			curObj = None
			pass
