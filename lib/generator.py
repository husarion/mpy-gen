import sys
import lib.qdef, lib.func_generator

def findQstrs(ctx):
	qstrs = []
	for gl in ctx.objGlobals:
		qstrs.append(gl["name"])
	for cl in ctx.objClasses:
		qstrs.append(cl.name)
		for m in cl.methods:
			qstrs.append(m.name)
	
	qstrs = set(qstrs)
	qstrs.remove("sys")
	qstrs.remove("write")
	qstrs.remove("read")

	return qstrs

def genQstrEnum(qstrs):
	s = """
enum
{
	start = 0x05000000 - 1,
"""
	for q in qstrs:
		s += "\tMP_QSTR_" + q + ",\n"
	
	s += """\tMP_QSTR_hPyFramework_number_of,
};
"""
	return s

def genQstrPool(qstrs):
	s = """
qstr_pool_t hpyframework_pool =
{{
	0,
	0,
	3, // set so that the first dynamically allocated pool is twice this size; must be <= the len (just below)
	{0}, // corresponds to number of strings in array just below
	0x05000000,
	{{
""".format(len(qstrs))
	for q in qstrs:
		v = lib.qdef.genQstr(q)
		s += "\t\t" + v + ",\n"
	
	s += """\t},
};
"""
	return s

def genMethodsHeaders(ctx):
	s = "\n"
	for cl in ctx.objClasses:
		for method in cl.methods:
			s += "\n" + lib.func_generator.genMethodHeader(cl, method) + ";"
	return s

def genMethodsTable(cl):
	s = "\n"

	for method in cl.methods:
		if method.constructor or method.subscript:
			continue
		s += """
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN({objName}_{funcName}_obj, {argMin}, {argMax}, {objName}_{funcName});
""".lstrip().format(
		objName=cl.name,
		funcName=method.name,
		argMin=method.getMinArgs() + 1,
		argMax=method.getMaxArgs() + 1)

	s += """
STATIC const mp_map_elem_t {objName}_locals_dict_table[] =
{{""".lstrip().format(objName=cl.name)

	for method in cl.methods:
		if not method.isRegularMethod():
			continue
		s += """
	{{ MP_OBJ_NEW_QSTR(MP_QSTR_{funcName}), (mp_obj_t)&{objName}_{funcName}_obj }},
""".rstrip().format(objName=cl.name, funcName=method.name)

	s += """
};"""

	return s

def genObjStruct(name):
	return """
typedef struct _mp_obj_{name}_t
{{
	mp_obj_base_t base;
	void *hObj;
}} mp_obj_{name}_t;
""".format(name=name)

def genObjTypesExterns(ctx):
	s = "\n"
	for cl in ctx.objClasses:
		s += "extern const mp_obj_type_t {name}_type;\n".format(name=cl.name)
	return s

def genObjType(cl):
	new = "0"
	if cl.hasConstructor():
		new = "&{name}_constructor".format(name=cl.name)
	sub = "0"
	if cl.hasSubscript():
		sub = "&{name}_subscript".format(name=cl.name)

	return """
STATIC MP_DEFINE_CONST_DICT({name}_locals_dict, {name}_locals_dict_table);
const mp_obj_type_t {name}_type =
{{
	.base = {{ &mp_type_type }},
	.name = MP_QSTR_{name},
	.print = 0,
	.make_new = {new},
	.subscr = {sub},
	.locals_dict = (mp_obj_t)&{name}_locals_dict,
}};
""".format(name=cl.name, new=new, sub=sub)

def genReg(ctx):
	s = "\n"

	for cl in ctx.objClasses:
		s += "extern const mp_obj_type_t {name}_type;\n".format(name=cl.name);

	s += """
void pyRegister()
{
	qstr_add_const_pool(&hpyframework_pool);

	mp_obj_hObject_t *v;

"""

	for cl in ctx.objClasses:
		s += "\tmp_store_name(MP_QSTR_{name}, (mp_obj_t)&{name}_type);\n".format(name=cl.name)

	for gl in ctx.objGlobals:
		s += """
	v = m_new_obj_var(mp_obj_hObject_t, char*, 0);
	v->hObj = dynamic_cast<{type}*>(&{name});
	v->base.type = &{type}_type;
	mp_store_name(MP_QSTR_{name}, (mp_obj_t)v);
""".format(name=gl["name"], type=gl["type"])

	s += """
}
"""

	return s
