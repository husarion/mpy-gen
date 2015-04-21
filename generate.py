#!/usr/bin/python2.7
import subprocess, json, os, sys
import parser, generator, func_generator

data = open("info").read()

ctx = parser.ParserContext()
parser.genTree(ctx, data)

qstrs = generator.findQstrs(ctx)

header = open("gen.h", "wb")
srcC = open("gen.c", "wb")
srcCPP = open("gen.cpp", "wb")

# HEADER
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

extern qstr_pool_t hpyframework_pool;
#ifdef __cplusplus
}
#endif

typedef struct _mp_obj_hObject_t
{
	mp_obj_base_t base;
	void *hObj;
} mp_obj_hObject_t;
""".lstrip().encode("ascii"))

t = generator.genQstrEnum(qstrs)
header.write(t.encode("ascii"))

t = generator.genMethodsHeaders(ctx)
header.write(t.encode("ascii"))

# for cl in ctx.objClasses:
	# t = generator.genObjStruct(cl["name"])
	# header.write(t.encode("ascii"))

# C
srcC.write("""
#include "gen.h"

""".lstrip().encode("ascii"))

t = generator.genQstrPool(qstrs)
srcC.write(t.encode("ascii"))

for cl in ctx.objClasses:
	t = generator.genMethodsTable(cl)
	srcC.write(t.encode("ascii"))

	t = generator.genObjType(cl["name"])
	srcC.write(t.encode("ascii"))

# CPP
srcCPP.write("""
#include "gen.h"
#include <hFramework.h>

using namespace hFramework;

""".lstrip().encode("ascii"))

for cl in ctx.objClasses:
	for m in cl["methods"]:
		t = func_generator.genMethod(cl, m)
		srcCPP.write(t.encode("ascii"))

t = generator.genReg(ctx)
srcCPP.write(t.encode("ascii"))
