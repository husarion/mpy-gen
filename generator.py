import qdef

def findQstrs(ctx):
	qstrs = []
	for gl in ctx.objGlobals:
		qstrs.append(gl["name"])
	for cl in ctx.objClasses:
		qstrs.append(cl["name"])
		for m in cl["methods"]:
			qstrs.append(m["name"])
	
	qstrs.remove("sys")

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
		v = qdef.genQstr(q)
		s += "\t\t" + v + ",\n"
	
	s += """\t},
};
"""
	return s

def genMethodHeader(cl, method):
	args = ["mp_obj_t self_in"]
	i = 0
	for arg in method["args"]:
		args.append("mp_obj_t arg{0}".format(i))
		i += 1
	s = "mp_obj_t {objName}_{funcName}({args})".format(objName=cl["name"], funcName=method["name"], args=", ".join(args))
	return s

def genMethodsHeaders(ctx):
	s = """
#ifdef __cplusplus
extern "C" {
#endif"""
	for cl in ctx.objClasses:
		for method in cl["methods"]:
			s += "\n" + genMethodHeader(cl, method) + ";"
	s += """
#ifdef __cplusplus
}
#endif
"""
	return s

def genMethodsTable(cl):
	s = "\n"

	for method in cl["methods"]:
		s += genMethodHeader(cl, method) + ";"
		s += """
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN({objName}_{funcName}_obj, {argn}, {argn}, {objName}_{funcName});
""".format(objName=cl["name"], funcName=method["name"], argn=len(method["args"]) + 1)

	s += """
STATIC const mp_map_elem_t {objName}_locals_dict_table[] =
{{""".format(objName=cl["name"])

	for method in cl["methods"]:
		s += """
	{{ MP_OBJ_NEW_QSTR(MP_QSTR_{funcName}), (mp_obj_t)&{objName}_{funcName}_obj }},
""".rstrip().format(objName=cl["name"], funcName=method["name"])

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

def genObjType(name):
	return """
STATIC MP_DEFINE_CONST_DICT({name}_locals_dict, {name}_locals_dict_table);
const mp_obj_type_t {name}_type =
{{
	.base = {{ &mp_type_type }},
	.name = MP_QSTR_{name},
	.print = 0,
	.locals_dict = (mp_obj_t)&{name}_locals_dict,
}};
""".format(name=name)

def genReg(ctx):
	s = "\n"

	for cl in ctx.objClasses:
		s += "extern const mp_obj_type_t {name}_type;\n".format(name=cl["name"]);

	s += """
void reg()
{
	qstr_add_const_pool(&hpyframework_pool);

	mp_obj_hObject_t *v;
"""

	for gl in ctx.objGlobals:
		s += """
	v = m_new_obj_var(mp_obj_hObject_t, char*, 0);
	v->hObj = &{name};
	v->base.type = &{type}_type;
	mp_store_name(MP_QSTR_{name}, (mp_obj_t)v);
""".format(name=gl["name"], type=gl["type"])

	s += """
}
"""

	return s
