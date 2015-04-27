#!/usr/bin/python2.7
import subprocess, json, os, sys, argparse
sys.path.append(".")
import lib.parser, lib.generator, lib.func_generator

argparser = argparse.ArgumentParser()
argparser.add_argument('-c', '--config', nargs=1, type=str, metavar="PATH", required=True)
args = argparser.parse_args()

data = open(args.config[0]).read()

ctx = lib.parser.ParserContext()
ctx.parseData(data)

qstrs = lib.generator.findQstrs(ctx)

name = "hPyFramework"

header = open("gen_" + name + ".h", "wb")
srcC = open("gen_" + name + ".c", "wb")
srcCPP = open("gen_" + name + ".cpp", "wb")

# HEADER
header.write("""
#ifdef __cplusplus
extern "C" {{
#endif
#include "py/nlr.h"
#include "py/parse.h"
#include "py/compile.h"
#include "py/runtime.h"
#include "py/repl.h"
#include "py/nlr.h"
#include "py/runtime.h"
#include "py/binary.h"

void reg();

extern qstr_pool_t {name}_pool;
#ifdef __cplusplus
}}
#endif

typedef struct _mp_obj_hObject_t
{{
	mp_obj_base_t base;
	void *hObj;
}} mp_obj_hObject_t;
""".lstrip().format(name=name).encode("ascii"))

t = lib.generator.genQstrEnum(qstrs)
header.write(t.encode("ascii"))

t = """
#ifdef __cplusplus
extern "C" {
#endif"""
header.write(t.encode("ascii"))

t = lib.generator.genMethodsHeaders(ctx)
header.write(t.encode("ascii"))

t = """
#ifdef __cplusplus
}
#endif
"""
header.write(t.encode("ascii"))

t = lib.generator.genObjTypesExterns(ctx)
header.write(t.encode("ascii"))

# C
srcC.write("""
#include "gen_{name}.h"

""".lstrip().format(name=name).encode("ascii"))

t = lib.generator.genQstrPool(qstrs)
srcC.write(t.encode("ascii"))

for cl in ctx.objClasses:
	t = lib.generator.genMethodsTable(cl)
	srcC.write(t.encode("ascii"))

	t = lib.generator.genObjType(cl)
	srcC.write(t.encode("ascii"))

# CPP
srcCPP.write("""
#include "gen_{name}.h"
#include <stdio.h>

typedef unsigned char byte;

""".lstrip().format(name=name).encode("ascii"))

srcCPP.write(("\n".join(["#include \"{0}\"".format(incl) for incl in ctx.inclues]) + "\n\n").encode("ascii"))
srcCPP.write(("\n".join(["using namespace {0};".format(ns) for ns in ctx.namespaces]) + "\n\n").encode("ascii"))

for cl in ctx.objClasses:
	for m in cl.methods:
		t = lib.func_generator.genMethod(cl, m)
		srcCPP.write(t.encode("ascii"))

t = lib.generator.genReg(ctx)
srcCPP.write(t.encode("ascii"))
