import generator

def genArgsCallList(method, maxArgs):
	argsList = []
	i = 0
	for arg in method.args:
		if i == maxArgs:
			break
		argsList.append("val{0}".format(i + 1))
		i += 1

	return argsList

def genMethod(cl, method):
	funcName = method.name

	s = ""
	s += generator.genMethodHeader(cl, method) + "\n{\n"
	
	if method.needArrayCall():
		s += "\tmp_obj_t self_in = args[0];\n"
	s += "\tmp_obj_{objName}_t *self = (mp_obj_{objName}_t*)self_in;\n".format(objName="hObject")
	s += "\t{objName} *hSelf = ({objName}*)self->hObj;\n".format(objName=cl["name"])

	i = 1
	for arg in method.args:
		if arg.type == "int":
			s += "\tmp_int_t val{0};\n".format(i)
		i += 1

	i = 1
	for arg in method.args:
		if arg.type == "int":
			if method.needArrayCall():
				s += "\tif (n_args >= {0})".format(i + 1)
				s += " val{0} = mp_obj_get_int(args[{0}]);\n".format(i)
			else:
				s += "\tval{0} = mp_obj_get_int(arg{0});\n".format(i)
		i += 1

	retType = method.returnType
	retStr = ""
	if retType != "void":
		s += "\t{0} ret;\n".format(retType)
		retStr = "ret = "

	if method.needArrayCall():
		minArgs = method.getMinArgs()
		maxArgs = method.getMaxArgs()
		first = True
		for i in range(minArgs, maxArgs + 1):
			print(i)
			argsList = genArgsCallList(method, i)
			s += "\t"
			if not first:
				s += "else "
			s += "if (n_args == {0})\n".format(i + 1)
			s += "\t\t{retStr}hSelf->{funcName}({args});\n".format(retStr=retStr, funcName=funcName, args=", ".join(argsList))
			print(argsList)
			first = False

	else:
		argsList = genArgsCallList(method, method.getMaxArgs())
		s += "\t{retStr}hSelf->{funcName}({args});\n".format(retStr=retStr, funcName=funcName, args=", ".join(argsList))
	
	if retType == "void":
		s += "\treturn mp_const_none;\n"
	elif retType == "int":
		s += "\treturn mp_obj_new_int(ret);\n"
	elif retType == "bool":
		s += "\treturn ret ? mp_const_true : mp_const_false;\n"
	else:
		raise Exception("Unsupported return type")

	s += "}\n"
	print(s)

	# print(s)

	return s
