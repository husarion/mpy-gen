import sys
from . import qdef, func_generator

def findQstrs(ctx):
	qstrs = []
	for gl in ctx.objGlobals:
		qstrs.append(gl["name"])
	for cl in ctx.objClasses:
		qstrs.append(cl.name)
		for m in cl.methods:
			qstrs.append(m.name)
	
	qstrs = set(qstrs)
	qstrs -= set(["__build_class__", "__class__", "__doc__", "__import__", "__init__", "__new__", "__locals__", "__main__", "__module__", "__name__", "__hash__", "__next__", "__qualname__", "__path__", "__repl_print__", "__bool__", "__contains__", "__enter__", "__exit__", "__len__", "__iter__", "__getitem__", "__setitem__", "__delitem__", "__add__", "__sub__", "__repr__", "__str__", "__getattr__", "__del__", "__call__", "__lt__", "__gt__", "__eq__", "__le__", "__ge__", "__reversed__", "micropython", "bytecode", "const", "builtins", "Ellipsis", "StopIteration", "BaseException", "ArithmeticError", "AssertionError", "AttributeError", "BufferError", "EOFError", "Exception", "FileExistsError", "FileNotFoundError", "FloatingPointError", "GeneratorExit", "ImportError", "IndentationError", "IndexError", "KeyboardInterrupt", "KeyError", "LookupError", "MemoryError", "NameError", "NotImplementedError", "OSError", "OverflowError", "RuntimeError", "SyntaxError", "SystemExit", "TypeError", "UnboundLocalError", "ValueError", "ZeroDivisionError", "None", "False", "True", "object", "NoneType", "abs", "all", "any", "args", "bin", "{:#b}", "bool", "bytes", "callable", "chr", "classmethod", "_collections", "complex", "real", "imag", "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "from_bytes", "getattr", "setattr", "globals", "hasattr", "hash", "hex", "%#x", "id", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "min", "namedtuple", "next", "oct", "%#o", "open", "ord", "path", "pow", "print", "range", "read", "repr", "reversed", "round", "sorted", "staticmethod", "sum", "super", "str", "sys", "to_bytes", "tuple", "type", "value", "write", "zip", "sep", "end", "step", "stop", "clear", "copy", "fromkeys", "get", "items", "keys", "pop", "popitem", "setdefault", "update", "values", "append", "close", "send", "throw", "count", "extend", "index", "remove", "insert", "sort", "join", "strip", "lstrip", "rstrip", "format", "key", "reverse", "add", "find", "rfind", "rindex", "split", "rsplit", "startswith", "endswith", "replace", "partition", "rpartition", "lower", "upper", "isspace", "isalpha", "isdigit", "isupper", "islower", "iterable", "start", "bound_method", "closure", "dict_view", "function", "generator", "iterator", "module", "slice", "math", "e", "pi", "sqrt", "exp", "expm1", "log", "log2", "log10", "cosh", "sinh", "tanh", "acosh", "asinh", "atanh", "cos", "sin", "tan", "acos", "asin", "atan", "atan2", "ceil", "copysign", "fabs", "fmod", "floor", "isfinite", "isinf", "isnan", "trunc", "modf", "frexp", "ldexp", "degrees", "radians", "maximum recursion depth exceeded", "<module>", "<lambda>", "<listcomp>", "<dictcomp>", "<setcomp>", "<genexpr>", "<string>", "<stdin>"])

	return qstrs

def genQstrEnum(ctx, qstrs):
	s = """
enum
{{
	MP_{ctx.name}_start = 0x{ctx.strStartNum:08x} - 1,
""".format(ctx=ctx)

	for q in qstrs:
		s += "\tMP_QSTR_" + q + ",\n"

	s += "\n};\n"
	return s

def genQstrPool(ctx, qstrs):
	s = """
qstr_pool_t {ctx.name}_pool =
{{
	0,
	0,
	3, // set so that the first dynamically allocated pool is twice this size; must be <= the len (just below)
	{cnt}, // corresponds to number of strings in array just below
	0x{ctx.strStartNum:08x},
	{{
""".format(cnt=len(qstrs), ctx=ctx)
	for q in qstrs:
		v = qdef.genQstr(q)
		s += "\t\t" + v + ",\n"
	
	s += """\t},
};
"""
	return s

def genMethodsHeaders(ctx):
	s = "\n"
	for cl in ctx.objClasses:
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
void register_{name}()
{{
	qstr_add_const_pool(&{name}_pool);

	mp_obj_hObject_t *v;

""".format(name=ctx.name)

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
