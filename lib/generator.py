import sys
from . import qdef, func_generator

def genQstrEnum(ctx):
	s = "\nenum\n{\n"

	ext = ctx.getExternQstrs()
	extSet = set([i["name"] for i in ext])
	qstrsSet = set([i["name"] for i in ctx.qstrs])

	for q in ext:
		if q["name"] in qstrsSet:
			s += "\tMP_QSTR_{q[name]} = 0x{q[num]:08x},\n".format(q=q)

	for q in ctx.qstrs:
		if q["name"] not in extSet:
			s += "\tMP_QSTR_{q[name]} = 0x{q[num]:08x},\n".format(q=q)

	s += "};\n"
	return s

def genQstrPool(ctx):
	s = """
qstr_pool_t {ctx.name}_pool =
{{
	0,
	0,
	3, // set so that the first dynamically allocated pool is twice this size; must be <= the len (just below)
	{cnt}, // corresponds to number of strings in array just below
	0x{ctx.strStartNum:08x},
	{{
""".format(cnt=len(ctx.qstrs), ctx=ctx)

	ext = ctx.getExternQstrs()
	extSet = set([i["name"] for i in ext])

	for q in ctx.qstrs:
		if q["name"] not in extSet:
			v = qdef.genQstr(q["name"])
			s += "\t\t" + v + ",\n"
	
	s += """\t},
};
"""
	return s

def genMethodsHeaders(ctx):
	s = "\n"
	for cl in ctx.objClasses:
		if cl.extern:
			continue
		for method in cl.methods:
			s += "\n" + func_generator.genMethodHeader(cl, method) + ";"
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
		if method.isRegularMethod() or method.destructor:
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
		if cl.extern:
			continue
		s += "extern const mp_obj_type_t {name}_type;\n".format(name=cl.name);

	s += """
void register_{name}()
{{
	qstr_add_const_pool(&{name}_pool);

	mp_obj_hObject_t *v;

""".format(name=ctx.name)

	for cl in ctx.objClasses:
		if cl.extern:
			continue
		s += "\tmp_store_name(MP_QSTR_{name}, (mp_obj_t)&{name}_type);\n".format(name=cl.name)

	for gl in ctx.objGlobals:
		if gl["extern"]:
			continue
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

def genDynamicCaster(ctx):
	s = """
template<typename T>
T mycast(mp_obj_hObject_t* src)
{
""".lstrip()
	for cl in ctx.objClasses:
		if ctx.isPolymorphic(cl):
			s += "\tif (src->base.type == &{type}_type)\n".format(type=cl.name)
			s += "\t\treturn dynamic_cast<T>(({type}*)src->hObj);\n".format(type=cl.name)
	s += "\treturn 0;\n}\n"
	return s
