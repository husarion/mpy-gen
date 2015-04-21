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
	s += "\t{objName} *hSelf = ({objName}*)self->hObj;\n".format(objName=cl.name)

	i = 1
	for arg in method.args:
		s += "\t{0} val{1};\n".format(arg.type, i)
		i += 1

	i = 1
	for arg in method.args:
		if method.needArrayCall():
			s += "\tif (n_args >= {0})\n\t".format(i + 1)

		dstVar = "val{0}".format(i)

		if method.needArrayCall():
			srcVar = "args[{0}]".format(i)
		else:
			srcVar = "arg{0}".format(i)

		if arg.type == "int":
			s += "\t{dstVar} = mp_obj_get_int({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
		if arg.type == "bool":
			s += "\t{dstVar} = mp_obj_is_true({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
		# if method.needArrayCall():
			# s += "\t}\n"
		i += 1

	# s += "\n"

	retType = method.returnType
	retStr = ""
	customType = retType[0] == "h" or retType[0] == "I"
	isRef = retType[-1] == "&"
	retType = retType.rstrip("&")

	if retType != "void":
		if customType and isRef:
			s += "\t{0}* ret;\n".format(retType)
		else:
			s += "\t{0} ret;\n".format(retType)

		if isRef:
			retStr = "ret = &"
		else:
			retStr = "ret = "

	if method.needArrayCall():
		minArgs = method.getMinArgs()
		maxArgs = method.getMaxArgs()
		first = True
		for i in range(minArgs, maxArgs + 1):
			argsList = genArgsCallList(method, i)
			s += "\t"
			if not first:
				s += "else "
			s += "if (n_args == {0})\n".format(i + 1)
			s += "\t\t{retStr}hSelf->{funcName}({args});\n".format(retStr=retStr, funcName=funcName, args=", ".join(argsList))
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
	elif customType:
		s += """
	mp_obj_hObject_t *v = m_new_obj_var(mp_obj_hObject_t, char*, 0);
	v->hObj = ret;
	v->base.type = &{type}_type;
	return v;
""".format(type=retType.rstrip("&"))
	else:
		raise Exception("Unsupported return type")

	s += "}\n"

	if method.name=="write":
		print(s)

	return s
