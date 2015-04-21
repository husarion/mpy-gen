import generator

def genArgsCallList(method, maxArgs):
	argsList = []
	i = 0
	for arg in method.args:
		if i == maxArgs:
			break
		if arg.isRef:
			argsList.append("*val{0}".format(i + 1))
		else:
			argsList.append("val{0}".format(i + 1))
		i += 1

	return argsList

def genMethod(cl, method):
	funcName = method.name

	s = ""
	s += generator.genMethodHeader(cl, method) + "\n{\n"
	
	# prolog
	if not method.constructor:
		if method.needArrayCall():
			s += "\tmp_obj_t self_in = args[0];\n"
		# s += "\tmp_obj_{objName}_t *self = (mp_obj_{objName}_t*)self_in;\n".format(objName="hObject")
		s += "\t{objName} *hSelf = ({objName}*)(((mp_obj_hObject_t*)self_in)->hObj);\n".format(objName=cl.name)

	# arguments variables
	i = 1
	for arg in method.args:
		s += "\t{0} val{1};\n".format(arg.fullType, i)
		i += 1

	# casted arguments
	i = 1
	for arg in method.args:
		# argOffset = 0
		# if method.constructor:
			# argOffset = -1

		# if method.constructor:
			# s += "\tif (n_args >= {0})\n\t".format(i)
		if method.needArrayCall():
			s += "\tif (n_args >= {0})\n\t".format(i + 1)

		dstVar = "val{0}".format(i)

		if method.constructor:
			srcVar = "args[{0}]".format(i - 1)
		elif method.needArrayCall():
			srcVar = "args[{0}]".format(i)
		else:
			srcVar = "arg{0}".format(i)

		if arg.type == "int":
			s += "\t{dstVar} = mp_obj_get_int({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
		if arg.type == "bool":
			s += "\t{dstVar} = mp_obj_is_true({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)

		if arg.customType:
			s += "\t{dstVar} = ({type})((mp_obj_hObject_t*){srcVar})->hObj;\n".format(
					dstVar=dstVar, srcVar=srcVar, type=arg.fullType)

		# if method.needArrayCall():
			# s += "\t}\n"
		i += 1

	# s += "\n"


	# invocation
	retStr = ""
	# if method.constructor:
		# retType = cl.name
		# customType = True
		# isRef = True
	# else:
	retType = method.returnType
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

	if not method.constructor:
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
	else:
		argsList = genArgsCallList(method, method.getMaxArgs())
		s += """
	int size = {type}::constructor_get_size({args});
	mp_obj_hObject_t *v = m_new_obj_var(mp_obj_hObject_t, char*, size);
	{type}* obj = ({type}*)v->hObj;
	{type}::constructor(obj, {args});
""".format(
				retStr=retStr, funcName=funcName, args=", ".join(argsList), type=cl.name)
	
	# processing return value
	if method.constructor:
		s += "\treturn v;\n"
	elif retType == "void":
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
	# else:
		# raise Exception("Unsupported return type")

	s += "}\n"

	print(s)
	return s

def genConstructor(cl):
	s = genConstructorHeader(cl) + "\n{"

	s += """
	// mp_obj_hObject_t *v;
	// v = m_new_obj_var(mp_obj_hObject_t, char*, 0);
	// v->hObj = &{name};
	// v->base.type = &{type}_type;
	// return v;
}
"""
	return s
