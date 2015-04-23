import generator

def genArgsCallList(method, maxArgs):
	argsList = []
	i = 0
	for arg in method.args:
		if i == maxArgs:
			break
		if arg.type == "buffer":
			argsList.append("val{0}_array".format(i + 1))
			argsList.append("val{0}_array_len".format(i + 1))
		elif arg.isRef:
			argsList.append("*val{0}".format(i + 1))
		else:
			argsList.append("val{0}".format(i + 1))
		i += 1

	return argsList

def genSimpleTypeCast(type, srcVar, dstVar, lvl=1):
	s = "\t" * lvl
	if type == "int":
		s += "{dstVar} = mp_obj_get_int({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
	elif type == "byte":
		s += "{dstVar} = (byte)mp_obj_get_int({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
	elif type == "bool":
		s += "{dstVar} = mp_obj_is_true({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
	else:
		return ""
	return s

def genSimpleTypeCastReverse(type, srcVar, dstVar, lvl=1):
	s = "\t" * lvl
	if type == "int":
		s += "{dstVar} = mp_obj_new_int({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
	elif type == "byte":
		s += "{dstVar} = mp_obj_new_int((byte){srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
	elif type == "bool":
		s += "{dstVar} = {srcVar} ? mp_const_true : mp_const_false;\n".format(dstVar=dstVar, srcVar=srcVar)
	else:
		return ""
	return s

def genArgumentsCasts(method):
	s = ""
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

		s += genSimpleTypeCast(type=arg.type, dstVar=dstVar, srcVar=srcVar)
		if arg.type == "buffer":
			array_var = "val{idx}_array".format(idx=i)
			array_len_var = "val{idx}_array_len".format(idx=i)

			castStr = genSimpleTypeCast(
					arg.subType,
					dstVar="{array}[i]".format(array=array_var),
					srcVar="val{idx}->items[i]".format(idx=i))

			s += "\t{dstVar} = (mp_obj_list_t*)({srcVar});\n".format(dstVar=dstVar, srcVar=srcVar)
			s += """\tint {array_len} = {dstVar}->len;
	{subType} *{array} = ({subType}*)sys.malloc(sizeof({subType}) * {array_len});
""".format(dstVar=dstVar, subType=arg.subType, array=array_var, array_len=array_len_var).rstrip()

			if arg.isIn():
				s += "\n\tfor (int i = 0; i < {array_len}; i++)\n\t{castStr}".format(
						array_len=array_len_var, castStr=castStr).rstrip()
			
			s += "\n"

		if arg.customType:
			s += "\t{dstVar} = ({type})(&((mp_obj_hObject_t*){srcVar})->hObj);\n".format(
					dstVar=dstVar, srcVar=srcVar, type=arg.fullType)

		# if method.needArrayCall():
			# s += "\t}\n"
		i += 1

	s = s.strip("\n")
	if len(s) > 0:
		s += "\n"
	return s

def genArgumentsOutProcessing(method):
	s = ""
	i = 1
	for arg in method.args:
		if arg.type == "buffer":
			array_var = "val{idx}_array".format(idx=i)
			array_len_var = "val{idx}_array_len".format(idx=i)

			castStr = genSimpleTypeCastReverse(
					arg.subType,
					dstVar="val{idx}->items[i]".format(idx=i),
					srcVar="{array}[i]".format(array=array_var))

			if arg.isOut():
				s += "\tfor (int i = 0; i < {array_len}; i++)\n\t{castStr}".format(
						array_len=array_len_var, castStr=castStr).rstrip()

			s += "\n"

		i += 1

	s = s.strip("\n")
	if len(s) > 0:
		s += "\n"
	return s
def genArgumentsCleaning(method):
	s = ""
	i = 1
	for arg in method.args:
		if arg.type == "buffer":
			array_var = "val{idx}_array".format(idx=i)
			s += "\tsys.free({array});\n".format(array=array_var)
		i += 1

	s = s.strip("\n")
	if len(s) > 0:
		s += "\n"
	return s

def genMethodCall(cl, method):
	s = ""
	retStr = ""
	funcName = method.name
	retType = method.returnType
	if retType != "void":
		if retType.isRef:
			retStr = "ret = &"
		else:
			retStr = "ret = "

	if method.isRegularMethod():
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

	elif method.constructor:
		argsList = genArgsCallList(method, method.getMaxArgs())
		s += """
	int size = {type}::constructor_get_size({args});
	mp_obj_hObject_t *v = m_new_obj_var(mp_obj_hObject_t, uint8_t, size);
	v->base.type = (mp_obj_type_t*)type_in;
	{type}* obj = ({type}*)&v->hObj;
	{type}::constructor(obj, {args});
""".lstrip("\n").format(
				retStr=retStr, funcName=funcName, args=", ".join(argsList), type=cl.name)

	elif method.subscript:
		casts = genArgumentsCasts(method)
		s += """
	int indexNum = mp_obj_get_int(index);
	if (arg1 == MP_OBJ_NULL)
		return MP_OBJ_NULL;

	if (!{type}::subscript_check_index(hSelf, indexNum))
		return MP_OBJ_NULL;

	if (arg1 == MP_OBJ_SENTINEL) {{
		ret = {type}::subscript_get(hSelf, indexNum);
	}}
	else {{
	{casts}
		{type}::subscript_set(hSelf, indexNum, val1);
		return mp_const_none;
	}}
""".lstrip("\n").format(
				retStr=retStr, funcName=funcName, type=cl.name, casts=casts)
	
	s = s.strip("\n")
	if len(s) > 0:
		s += "\n"
	return s

def genMethod(cl, method):
	funcName = method.name
	print("Generating " + funcName)

	s = ""
	s += generator.genMethodHeader(cl, method) + "\n{\n"
	
	# prolog - extracting self object
	# if method.hasSelf():
	if method.hasSelf():
		s += "\t/* extracting self object */\n"
		if method.needArrayCall():
			s += "\tmp_obj_t self_in = args[0];\n"

		if cl.storeValue:
			s += "\t{objName} *hSelf = ({objName}*)(&(((mp_obj_hObject_t*)self_in)->hObj));\n".format(objName=cl.name)
		else:
			s += "\t{objName} *hSelf = ({objName}*)(((mp_obj_hObject_t*)self_in)->hObj);\n".format(objName=cl.name)

	# arguments variables
	s += "\t/* argument variables */\n"
	i = 1
	for arg in method.args:
		if arg.fullType == "buffer":
			s += "\tmp_obj_list_t* val{0};\n".format(i)
		else:
			s += "\t{0} val{1};\n".format(arg.fullType, i)
		i += 1

	# casted arguments
	if not method.subscript:
		s += "\t/* argument casting */\n"
		s += genArgumentsCasts(method)

	# invocation
	retType = method.returnType
	
	s += "\t/* return variable */\n"
	if retType != "void":
		if retType.customType and retType.isRef:
			s += "\t{0}* ret;\n".format(retType.type)
		else:
			s += "\t{0} ret;\n".format(retType.type)

	s += "\t/* method call */\n"
	s += genMethodCall(cl, method)

	# out processing
	s += "\t/* processing out vars */\n"
	s += genArgumentsOutProcessing(method)

	# cleaning
	s += "\t/* arguments cleaning */\n"
	s += genArgumentsCleaning(method)
	
	# processing return value
	s += "\t/* return */\n"
	if method.constructor:
		s += "\treturn v;\n"
	elif retType == "void":
		s += "\treturn mp_const_none;\n"
	elif retType == "int":
		s += "\treturn mp_obj_new_int(ret);\n"
	elif retType == "bool":
		s += "\treturn ret ? mp_const_true : mp_const_false;\n"
	elif retType.customType:
		s += """
	mp_obj_hObject_t *v = m_new_obj_var(mp_obj_hObject_t, char*, 0);
	v->hObj = ret;
	v->base.type = &{type.type}_type;
	return v;
""".format(type=retType)

	s += "}\n"

	if(funcName=="write"):
		print(s)
	if(funcName=="read"):
		print(s)
	return s
