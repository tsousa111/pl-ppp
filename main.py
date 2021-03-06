import os
import sys

import ply.lex as lex

states = [
    ('paragraph', 'exclusive'),
    ('bold', 'exclusive'),
    ('italic', 'exclusive'),
    ('underlined', 'exclusive'),
    ('strikethrough', 'exclusive'),
    ('struct', 'exclusive'),
    ('header', 'exclusive')
]

tokens = ['BOLD', 'ITL', 'UNDLINE', 'STRIKE',
          'STRUCTO', 'STRUCTC',
          'IMAGE', 'HDR', 'TEXT', 'LINEDOWN']

# Global Variables
headerSize = 0


# formatação: negrito, itálico, sublinhado;
# • vários níveis de títulos;
# • listas de tópicos (items) não-numerados, numerados ou tipo entradas de um dicionário ;
# • inclusão de imagens;
# • inclusão e formatação de tabelas;
# • todos os outros que achar necessário ou a sua imaginação vislumbrar.

# Header
def t_HDR(t):
    r'\@+'
    t.lexer.push_state('header')
    global headerSize
    headerSize = 0
    for character in t.value:
        if character == '@':
            headerSize += 1
    t.lexer.output += "<h" + str(headerSize) + ">"


def t_header_TEXT(t):
    r'.+'
    t.lexer.pop_state()
    t.lexer.output += t.value.strip()
    t.lexer.output += "</h" + str(headerSize) + ">\n"


def t_paragraph_HDR(t):
    r'\@+'
    t.lexer.pop_state()
    t.lexer.output += '</p>\n'
    t.lexer.push_state('header')
    global headerSize
    headerSize = 0
    for character in t.value:
        if character == '@':
            headerSize += 1
    t.lexer.output += "<h" + str(headerSize) + ">"


# BOLD
def t_BOLD(t):
    r'\$\$'
    t.lexer.output += "\n<p>\n"
    a = t.lexer.lexstatestack
    t.lexer.push_state('paragraph')
    if 'bold' in a:
        return t
    else:
        t.lexer.push_state('bold')
        t.lexer.output += "<strong>"


def t_paragraph_italic_underlined_strikethrough_struct_BOLD(t):
    r'\$\$'
    a = t.lexer.lexstatestack
    if 'bold' in a:
        return t
    else:
        t.lexer.push_state('bold')
        t.lexer.output += "<strong>"


def t_bold_BOLD(t):
    r'\$\$'
    t.lexer.pop_state()
    t.lexer.output += "</strong>"


# Italic
def t_ITL(t):
    r'//'
    a = t.lexer.lexstatestack
    t.lexer.push_state('paragraph')
    t.lexer.output += "<p>\n"
    if 'italic' in a:
        return t
    else:
        t.lexer.push_state('italic')
        t.lexer.output += "<em>"


def t_paragraph_bold_underlined_strikethrough_struct_ITL(t):
    r'//'
    a = t.lexer.lexstatestack
    if 'italic' in a:
        return t
    else:
        t.lexer.push_state('italic')
        t.lexer.output += "<em>"


def t_italic_ITL(t):
    r'//'
    t.lexer.pop_state()
    t.lexer.output += "</em>"


# UNDERLINED
def t_UNDLINE(t):
    r'__'
    a = t.lexer.lexstatestack
    t.lexer.push_state('paragraph')
    t.lexer.output += "\n<p>\n"
    if 'underlined' in a:
        return t
    else:
        t.lexer.push_state('underlined')
        t.lexer.output += "<u>"


def t_paragraph_bold_italic_strikethrough_struct_UNDLINE(t):
    r'__'
    a = t.lexer.lexstatestack
    if 'underlined' in a:
        return t
    else:
        t.lexer.push_state('underlined')
        t.lexer.output += "<u>"


def t_underlined_UNDLINE(t):
    r'__'
    t.lexer.pop_state()
    t.lexer.output += "</u>"


# STRIKETHROUGH
def t_STRIKE(t):
    r'--'
    a = t.lexer.lexstatestack
    t.lexer.push_state('paragraph')
    t.lexer.output += '\n<p>\n'
    if 'strikethrough' in a:
        return t
    else:
        t.lexer.push_state('strikethrough')
        t.lexer.output += "<del>"


def t_paragraph_bold_italic_underlined_STRIKE(t):
    r'--'
    a = t.lexer.lexstatestack
    if 'strikethrough' in a:
        return t
    else:
        t.lexer.push_state('strikethrough')
        t.lexer.output += "<del>"


def t_strikethrough_STRIKE(t):
    r'--'
    t.lexer.pop_state()
    t.lexer.output += "</del>"


# STRUCTS
def t_struct_STRUCTC(t):
    r'\]\ *'
    t.lexer.pop_state()
    match t.lexer.structtype:
        case "num":
            t.lexer.output += '</ol>\n'
        case "dot":
            t.lexer.output += '</ul>\n'
        case "dictionary":
            t.lexer.output += '</dl>\n'
        case "table":
            t.lexer.structtype = "table"
            t.lexer.output += '</table>\n'
            t.lexer.rownum = True
        case _:
            pass
    return t


def t_INITIAL_paragraph_STRUCTO(t):
    r'\[\ *\{\ *\w+\}'
    if 'paragraph' in t.lexer.lexstatestack:
        t.lexer.pop_state()
        t.lexer.output += '\n</p>\n'
    t.lexer.push_state('struct')
    for character in r'[{} ':
        t.value = t.value.replace(character, "")
    match t.value:
        case "num":
            t.lexer.structtype = 'num'
            t.lexer.output += '\n<ol>'
        case "dot":
            t.lexer.structtype = 'dot'
            t.lexer.output += '\n<ul>'
        case "dictionary":
            t.lexer.structtype = "dictionary"
            t.lexer.output += '\n<dl>'
        case "table":
            t.lexer.structtype = "table"
            t.lexer.output += '\n<table border=1px>'
        case _:
            pass
    return t


def t_struct_TEXT(t):
    r'\ *.+\ *'
    match t.lexer.structtype:
        case "dictionary":
            list = t.value.split(":")
            t.lexer.output += '\t<dt>' + list[0].strip() + '</dt>'
            t.lexer.output += '<dd>' + list[1].strip() + '</dd>'
        case "table":
            t.lexer.output += "\t<tr>\n"
            row_data = t.value.strip().split('|')
            for cell in row_data:
                if t.lexer.fstrow:
                    t.lexer.output += "\t\t<th>" + cell.strip() + "</th>\n"
                else:
                    t.lexer.output += "\t\t<td>" + cell.strip() + "</td>\n"
            t.lexer.output += "\t</tr>"
            t.lexer.fstrow = False
        case _:
            t.lexer.output += '\t<li>' + t.value.strip() + '</li>'


# IMAGE
def t_INITIAL_paragraph_IMAGE(t):
    r'img\{\ *[^\{\}]+\}\ *'
    lista = t.value.strip().split('{')[1].split('}')
    t.lexer.output += r'<img src="' + lista[0] + '\">'


# TEXT
def t_paragraph_LINEDOWN(t):
    r'\n\n'
    t.lexer.output += '\n</p>'
    t.lexer.pop_state()


def t_ANY_LINEDOWN(t):
    r'\n\n'
    return t


def t_TEXT(t):
    r'(.|\n)'
    t.lexer.output += '\n<p>\n'
    t.lexer.output += t.value
    t.lexer.push_state('paragraph')
    return t


def t_paragraph_bold_italic_underlined_strikethrough_struct_TEXT(t):
    r'(.|\n)'
    t.lexer.output += t.value
    return t


t_ignore = '\n'
t_header_paragraph_bold_italic_underlined_strikethrough_struct_ignore = ''


# ERROR
def t_ANY_error(t):
    print('Invalid Character! ' + t.value)


if len(sys.argv) < 3:
    sys.exit(1)
# Open input file
f = open(sys.argv[1], "r")
# Read input file
text = f.read()
# Close input file
f.close()

lexer = lex.lex()

lexer.input(text)

# Define our variable
lexer.output = "<html>\n<body>\n"
lexer.structtype = ""
lexer.fstrow = True

for tok in lexer:
    pass

# Open output file
outputFile = open(sys.argv[2], "w")
lexer.output += "</body>\n</html>"
outputFile.write(lexer.output)
outputFile.close()
