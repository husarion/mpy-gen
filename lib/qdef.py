# codepoint2name is different in Python 2 to Python 3
import platform, re

if platform.python_version_tuple()[0] == '2':
    from htmlentitydefs import codepoint2name
elif platform.python_version_tuple()[0] == '3':
    from html.entities import codepoint2name
codepoint2name[ord('-')] = 'hyphen';

# add some custom names to map characters that aren't in HTML
codepoint2name[ord(' ')] = 'space'
codepoint2name[ord('\'')] = 'squot'
codepoint2name[ord(',')] = 'comma'
codepoint2name[ord('.')] = 'dot'
codepoint2name[ord(':')] = 'colon'
codepoint2name[ord('/')] = 'slash'
codepoint2name[ord('%')] = 'percent'
codepoint2name[ord('#')] = 'hash'
codepoint2name[ord('(')] = 'paren_open'
codepoint2name[ord(')')] = 'paren_close'
codepoint2name[ord('[')] = 'bracket_open'
codepoint2name[ord(']')] = 'bracket_close'
codepoint2name[ord('{')] = 'brace_open'
codepoint2name[ord('}')] = 'brace_close'
codepoint2name[ord('*')] = 'star'
codepoint2name[ord('!')] = 'bang'
codepoint2name[ord('\\')] = 'backslash'

def compute_hash(qstr):
	hash = 5381
	for char in qstr:
		hash = (hash * 33) ^ ord(char)
	# Make sure that valid hash is never zero, zero means "hash not computed"
	return (hash & 0xffff) or 1

def genQstr(qstr):
	cfg_bytes_len = 1
	cfg_max_len = 255

	ident = re.sub(r'[^A-Za-z0-9_]', lambda s: "_" + codepoint2name[ord(s.group(0))] + "_", qstr)

	qhash = compute_hash(qstr)
	# Calculate len of str, taking escapes into account
	qlen = len(qstr.replace("\\\\", "-").replace("\\", ""))
	qdata = qstr.replace('"', '\\"')
	if qlen >= cfg_max_len:
		print('qstr is too long:', qstr)
		assert False
	qlen_str = ('\\x%02x' * cfg_bytes_len) % tuple(((qlen >> (8 * i)) & 0xff) for i in range(cfg_bytes_len))
	return '(const byte*)"\\x%02x\\x%02x%s" "%s"' % (qhash & 0xff, (qhash >> 8) & 0xff, qlen_str, qdata)

