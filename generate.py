#!/usr/bin/python2.7
import subprocess, json, os, sys
import parser, generator, func_generator

data = open("info").read()

ctx = parser.ParserContext()
parser.genTree(ctx, data)

header = open("gen.h", "wb")
srcC = open("gen.c", "wb")
srcCPP = open("gen.cpp", "wb")

header.write("""
#ifdef __cplusplus
extern "C" {
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

extern const qstr_pool_t hpyframework_pool;
#ifdef __cplusplus
}
#endif
""".lstrip().encode("ascii"))

srcC.write("""
#include "gen.h"

""".lstrip().encode("ascii"))

srcCPP.write("""
#include "gen.h"
#include <hFramework.h>

using namespace hFramework;

""".lstrip().encode("ascii"))

qstrs = generator.findQstrs(ctx)

t = generator.genQstrPool(qstrs)
srcC.write(t.encode("ascii"))

t = generator.genQstr(qstrs)
header.write(t.encode("ascii"))

t = generator.genMethodsHeaders(ctx)
header.write(t.encode("ascii"))

for cl in ctx.objClasses:
	# print(cl)
	# generator.genQstrDefs(cl)

	t = generator.genMethodsTable(cl)
	srcC.write(t.encode("ascii"))
	t = generator.genObjStruct(cl["name"])
	header.write(t.encode("ascii"))
	# print(t)
	print()
	for m in cl["methods"]:
		t = func_generator.genMethod(cl, m)
		srcCPP.write(t.encode("ascii"))
		# print(t)
	# print(t)
	t = generator.genObjType(cl["name"])
	srcC.write(t.encode("ascii"))

t = generator.genReg(ctx)
srcCPP.write(t.encode("ascii"))
