import generator

def genMethod(cl, method):
	funcName = method["name"]

	s = ""
	s += generator.genMethodHeader(cl, method) + "\n{\n"
	
	s += "\tmp_obj_{objName}_t *self = (mp_obj_{objName}_t*)self_in;\n".format(objName="hObject")
	s += "\t{objName} *hSelf = ({objName}*)self->hObj;\n".format(objName=cl["name"])

	i = 0
	argsList = []
	for arg in method["args"]:
		if arg == "int":
			s += "\tmp_int_t val{0} = mp_obj_get_int(arg{0});\n".format(i)
		argsList.append("val{0}".format(i))
		i += 1

	retType = method["returnType"]
	retStr = ""
	if retType != "void":
		retStr = "{0} ret = ".format(method["returnType"])

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

	return s
