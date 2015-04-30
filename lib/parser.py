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
	len = None

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
	subContexts = None

	def __init__(self):
		self.objClasses = []
		self.objGlobals = []
		self.inclues = []
		self.namespaces = []
		self.subContexts = []

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

	def getExternQstrs(self):
		qstrs = []
		for subCtx in self.subContexts:
			qstrs += subCtx.qstrs
		return qstrs

	def parseData(self, txt, extern = False):
		if extern:
			newCtx = ParserContext()
			r = newCtx.parseDataInternal(txt, True)
			self.subContexts.append(newCtx)
			self.objClasses += newCtx.objClasses
			self.objGlobals += newCtx.objGlobals
			return r
		else:
			return self.parseDataInternal(txt, False)

	def parseDataInternal(self, txt, markAsExtern):

		lines = txt.split("\n")

		for line in lines:
			line = line.strip()
			if len(line) == 0:
				continue

			(cmd, rest) = parseLine(line)

			if cmd == "name":
				parts = rest.split(":")
				self.name = parts[0]

			if cmd == "include":
				parts = rest.split(":")
				self.inclues.append(parts[0])

			if cmd == "namespace":
				parts = rest.split(":")
				self.namespaces.append(parts[0])

			if cmd == "num":
				parts = rest.split(":")
				self.strStartNum = int(parts[0], 0)

			if cmd == "global":
				parts = rest.split(":")
				objType = parts[0]
				objName = parts[1]

				self.addGlobal({'type': objType, 'name': objName, 'extern': markAsExtern})

			if cmd == "class":
				parts = rest.split(":")
				objName = parts[0]
				print("new class", objName)
				curObj = Class()
				curObj.extern = markAsExtern
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

			if cmd == "method":
				if curObj is None:
					continue

				parts = rest.split(":")

				objMethod = Method()
				objMethod.name = parts[1]
				objMethod.returnType = parseRetType(parts[0])
				objMethod.args = parseArgs(parts[2:])

				curObj.removeMethod(objMethod.name)
				curObj.methods.append(objMethod)

			if cmd == "constructor":
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
				self.addClass(curObj)
				curObj = None

		if self.name is None:
			print("Name must be specified in export file. Eg.")
			print("name:myproject")
			return False
		if self.strStartNum is None:
			print("String start number must be specified in export file. Eg.")
			print("num:0x01000000")
			return False

		qstrs = []
		for gl in self.objGlobals:
			qstrs.append(gl["name"])

		for cl in self.objClasses:
			qstrs.append(cl.name)
			for m in cl.methods:
				qstrs.append(m.name)

		builtin = set(["__build_class__", "__class__", "__doc__", "__import__", "__init__", "__new__", "__locals__", "__main__", "__module__", "__name__", "__hash__", "__next__", "__qualname__", "__path__", "__repl_print__", "__bool__", "__contains__", "__enter__", "__exit__", "__len__", "__iter__", "__getitem__", "__setitem__", "__delitem__", "__add__", "__sub__", "__repr__", "__str__", "__getattr__", "__del__", "__call__", "__lt__", "__gt__", "__eq__", "__le__", "__ge__", "__reversed__", "micropython", "bytecode", "const", "builtins", "Ellipsis", "StopIteration", "BaseException", "ArithmeticError", "AssertionError", "AttributeError", "BufferError", "EOFError", "Exception", "FileExistsError", "FileNotFoundError", "FloatingPointError", "GeneratorExit", "ImportError", "IndentationError", "IndexError", "KeyboardInterrupt", "KeyError", "LookupError", "MemoryError", "NameError", "NotImplementedError", "OSError", "OverflowError", "RuntimeError", "SyntaxError", "SystemExit", "TypeError", "UnboundLocalError", "ValueError", "ZeroDivisionError", "None", "False", "True", "object", "NoneType", "abs", "all", "any", "args", "bin", "{:#b}", "bool", "bytes", "callable", "chr", "classmethod", "_collections", "complex", "real", "imag", "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "from_bytes", "getattr", "setattr", "globals", "hasattr", "hash", "hex", "%#x", "id", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "min", "namedtuple", "next", "oct", "%#o", "open", "ord", "path", "pow", "print", "range", "read", "repr", "reversed", "round", "sorted", "staticmethod", "sum", "super", "str", "sys", "to_bytes", "tuple", "type", "value", "write", "zip", "sep", "end", "step", "stop", "clear", "copy", "fromkeys", "get", "items", "keys", "pop", "popitem", "setdefault", "update", "values", "append", "close", "send", "throw", "count", "extend", "index", "remove", "insert", "sort", "join", "strip", "lstrip", "rstrip", "format", "key", "reverse", "add", "find", "rfind", "rindex", "split", "rsplit", "startswith", "endswith", "replace", "partition", "rpartition", "lower", "upper", "isspace", "isalpha", "isdigit", "isupper", "islower", "iterable", "start", "bound_method", "closure", "dict_view", "function", "generator", "iterator", "module", "slice", "math", "e", "pi", "sqrt", "exp", "expm1", "log", "log2", "log10", "cosh", "sinh", "tanh", "acosh", "asinh", "atanh", "cos", "sin", "tan", "acos", "asin", "atan", "atan2", "ceil", "copysign", "fabs", "fmod", "floor", "isfinite", "isinf", "isnan", "trunc", "modf", "frexp", "ldexp", "degrees", "radians", "maximum recursion depth exceeded", "<module>", "<lambda>", "<listcomp>", "<dictcomp>", "<setcomp>", "<genexpr>", "<string>", "<stdin>"])
		qstrs = set(qstrs)
		qstrs -= builtin

		curNum = self.strStartNum
		self.qstrs = []
		for q in qstrs:
			self.qstrs.append({ "num": curNum, "name": q })
			curNum += 1

		# self.externQstrs = set(self.externQstrs)
		# self.externQstrs -= builtin
		# self.commonQstrs = self.qstrs & self.externQstrs
		# self.qstrs = self.qstrs - self.externQstrs

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

		# buffer[byte,in]
		m = re.match("(.*)\[([^,]*),([^,]*)\]", arg.fullType)
		if m:
			arg.fullType = m.group(1)
			arg.type = m.group(1)
			arg.subType = m.group(2)
			arg.dir = m.group(3)

		# buffer[byte,in,8]
		m = re.match("(.*)\[([^,]*),([^,]*),([^,]*)\]", arg.fullType)
		if m:
			arg.fullType = m.group(1)
			arg.type = m.group(1)
			arg.subType = m.group(2)
			arg.dir = m.group(3)
			arg.len = int(m.group(4))

		arg.customType = isCustomType(arg.type)

		args.append(arg)
	return args

def isCustomType(type):
	return type not in ["int", "int16_t", "bool", "float", "byte", "buffer"]
