#!/usr/bin/python2.7
import subprocess, json, os, sys, argparse
from lib import parser, generator, func_generator

argparser = argparse.ArgumentParser()
argparser.add_argument('-c', '--config', nargs=1, type=str, metavar="PATH", required=True)
argparser.add_argument('-o', '--outdir', nargs=1, type=str, metavar="PATH")
args = argparser.parse_args()

data = open(args.config[0]).read()

ctx = parser.ParserContext()
if not ctx.parseData(data):
	exit(1)

qstrs = generator.findQstrs(ctx)

name = ctx.name

if args.outdir is None:
	outDir = "."
else:
	outDir = args.outdir[0]

if not os.path.exists(outDir):
	os.makedirs(outDir)

header = open(outDir + "/gen_" + name + ".h", "wb")
srcC = open(outDir + "/gen_" + name + ".c", "wb")
srcCPP = open(outDir + "/gen_" + name + ".cpp", "wb")

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

t = generator.genQstrEnum(ctx, qstrs)
header.write(t.encode("ascii"))

t = """
#ifdef __cplusplus
extern "C" {
#endif"""
header.write(t.encode("ascii"))

t = generator.genMethodsHeaders(ctx)
header.write(t.encode("ascii"))

t = """
#ifdef __cplusplus
}
#endif
"""
header.write(t.encode("ascii"))

t = generator.genObjTypesExterns(ctx)
header.write(t.encode("ascii"))

# C
srcC.write("""
#include "gen_{name}.h"

""".lstrip().format(name=name).encode("ascii"))

t = generator.genQstrPool(ctx, qstrs)
srcC.write(t.encode("ascii"))

for cl in ctx.objClasses:
	t = generator.genMethodsTable(cl)
	srcC.write(t.encode("ascii"))

	t = generator.genObjType(cl)
	srcC.write(t.encode("ascii"))

# CPP
srcCPP.write("""
#include "gen_{name}.h"
#include <stdio.h>

typedef unsigned char byte;

""".lstrip().format(name=name).encode("ascii"))

srcCPP.write(("\n".join(["#include \"{0}\"".format(incl) for incl in ctx.inclues]) + "\n\n").encode("ascii"))
srcCPP.write(("\n".join(["using namespace {0};".format(ns) for ns in ctx.namespaces]) + "\n\n").encode("ascii"))

t = generator.genDynamicCaster(ctx)
srcCPP.write(t.encode("ascii"))

for cl in ctx.objClasses:
	for m in cl.methods:
		t = func_generator.genMethod(cl, m)
		srcCPP.write(t.encode("ascii"))

t = generator.genReg(ctx)
srcCPP.write(t.encode("ascii"))
