#!/usr/bin/python
import sys
import cparser
fout = open("../test/a.s", "wb")
with open ("../test/lib.s", 'r') as myfile:
      data=myfile.read()
fout.write(data)

root, symbol_table = cparser.main()
# print symbol_table
# for temp in symbol_table:
#   print temp

def get_argc_symbole_table(variable,scope_name):
  for hash_table in symbol_table:
    if hash_table['scope_name'] == scope_name:
      if variable in hash_table.keys():
        return hash_table[variable][1].split(' ')[1]
      elif scope_name == 's0':
        print 'Variable not found in symbol table exiting'
        sys.exit()
      else:
        return get_offset_symbole_table(variable,hash_table['parent_scope_name'])

def get_size_symbole_table(variable,scope_name):
  for hash_table in symbol_table:
    if hash_table['scope_name'] == scope_name:
      if variable in hash_table.keys():
        return hash_table[variable][4]
      elif scope_name == 's0':
        print 'Variable not found in symbol table exiting'
        sys.exit()
      else:
        return get_offset_symbole_table(variable,hash_table['parent_scope_name'])


def get_offset_symbole_table(variable,scope_name):
  for hash_table in symbol_table:
    if hash_table['scope_name'] == scope_name:
      if variable in hash_table.keys():
        if(hash_table[variable][1].startswith('Function')):
          return ''
        return hash_table[variable][5]
      elif scope_name == 's0':
        print 'Variable not found in symbol table exiting'
        sys.exit()
      else:
        return get_offset_symbole_table(variable,hash_table['parent_scope_name'])

def set_address_symbole_table(variable,scope_name,address):
  for index,hash_table in enumerate(symbol_table):
    if hash_table['scope_name'] == scope_name:
      if variable in hash_table.keys():
        symbol_table[index][variable].append(address)
        # print symbol_table[index][variable]
      elif scope_name == 's0':
        print 'Variable not found in symbol table exiting'
        sys.exit()
      else:
        set_address_symbole_table(variable,hash_table['parent_scope_name'],address)

count_label = 0
count_temp = 0
code = ''
data = ''
offset = 0


class label(object):
  def __init__(self,_id = 0,name=''):
    global count_label
    # self.code = code
    self._id = count_label;
    if name == '':
      name = 'L' + str(count_label) 
      count_label = count_label + 1;
    self.name = name
  def __repr__(self):
    return (self.name+':')

class newtemp(object):
  def __init__(self,_id = 0):
    global count_temp
    self.count = count_temp
    self._id = count_temp;
    count_temp = count_temp + 1;
  def __repr__(self):
    p = 'T' + str(self.count)
    return p

class Assignment():
  """docstring for Assignment"""
  def __init__(self,source='',sourceadd='', destination='',destinationadd=''):
    global data
    self.source = source
    self.destination = destination
    if destinationadd != '':
      data = data + '\tmov ecx, '+destinationadd+'\n'
      data = data + '\tmov '+sourceadd+', ecx'+'\n'
    else:
      data = data + '\tmov ecx, '+destination+'\n'
      data = data + '\tmov '+sourceadd+', ecx'+'\n'
  def __repr__(self):
    return self.source + ' = ' + self.destination

class Function_definition():
  """docstring for Function_definition"""
  def __init__(self,name=''):
    self.name = name
  def __repr__(self):
    return self.name

class BinOp():
  """docstring for BinOp"""
  def __init__(self,destination='',source_1='',operand='',source_2=''):
    self.source_1 = source_1
    self.source_2 = source_2
    self.operand = operand
    self.destination = destination
  def __repr__(self):
    return self.destination + ' = ' + self.source_1 + self.operand + self.source_2

def Jump(arg, arg2):
  global code
  global data
  code = code + '\tJMP ' + str(arg) + '\n'

def Compare(arg1, arg2):
  global code
  global data
  code = code + '\tCMP ' + str(arg1) +', ' + str(arg2) + '\n'

def PushParam(arg1,add1):
  global code
  global data
  code = code + '\tPUSH ' + str(arg1)+ '\n'
  if add1 == '':
    data = data + '\tmov eax, '+str(arg1)+'\n'
  else:
    data = data + '\tmov eax, '+add1+'\n'
  data = data + '\tpush eax'+'\n'

def FuncCall(arg1):
  global code
  global data
  k = int(get_argc_symbole_table(str(arg1.value),'s0'))
  # print "+++",get_argc_symbole_table(str(arg1.value),'s0')
  code = code + '\tCALL ' + str(arg1.value)+ '\n'
  data = data + '\tcall ' + str(arg1.value) + '\n'
  for i in range(0,k):
    data = data + '\tpop edx'+'\n'

def Decl(arg1):
  global offset
  global code
  global data
  arg2 = arg1.children[0]
  p = arg2.value
  temp = str(get_size_symbole_table(arg2.value, arg1.scope_name))
  data = data + '\tsub ebp, '+str(temp)+'\n'
  address = "[ebp-"+str(offset+int(temp))+"]"
  set_address_symbole_table(arg2.value, arg1.scope_name,address)
  offset =offset+int(temp)
  code = code + '\tDecl ' + str(p)+' '+temp+ '\n'
  return address

def Ret():
  global code
  global data
  code = code + '\tRET '+ '\n'

def BeginFunc():
  global code
  global data
  code = code + '\tBeginFunc'+'\n'
  data = data + '\tpush ebp'+'\n'
  data = data + '\tmov ebp, esp'+'\n'

def EndFunc():
  global code
  global data
  code = code + '\tEndFunc'+'\n'
  data = data + '\tpop ebp'+'\n'
  data = data + '\tret'+'\n'



def traverse_tree(ast_node, nextlist ,breaklist):
  global offset
  global code
  global data
  arg = ''
  add = ''
  if ast_node.name == 'VarAccess':
    arg = ast_node.value
    add = get_offset_symbole_table(ast_node.value,ast_node.scope_name)
    # pass
  elif ast_node.name == 'ConstantLiteral':
    arg = ast_node.value
  if ast_node.name == 'IF Statement':
    E_next = label(name = ast_node.value)
    E_true = label(name = ast_node.value)
    
    arg1,add1 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    Compare(arg1,0)
    Jump(E_next, "je")
    
    code = code + str(E_true) + '\n'
    data = data + str(E_true) + '\n'

    traverse_tree(ast_node.children[1], nextlist ,breaklist)
    Jump(E_next,"jmp")
    
    code = code + str(E_next) + '\n'
    data = data + str(E_next) + '\n'


  elif ast_node.name == 'IF-Else Statement':
    E_next = label(name = ast_node.value)
    E_true = label(name = ast_node.value)
    E_false = label(name = ast_node.value)

    arg1,add1 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    Compare(arg1,0)
    Jump(E_false,"je")
    
    code = code + str(E_true) + '\n'
    data = data + str(E_true) + '\n'

    traverse_tree(ast_node.children[1], nextlist ,breaklist)
    Jump(E_next,"jmp")

    code = code + str(E_false) + '\n'
    data = data + str(E_false) + '\n'

    traverse_tree(ast_node.children[2], nextlist ,breaklist)

    code = code + str(E_next) + '\n'
    data = data + str(E_next) + '\n'

  elif ast_node.name == 'While Statement':
    E_next = label(name = ast_node.value)
    E_begin = label(name = ast_node.value)

    code = code + str(E_begin) + '\n'
    data = data + str(E_begin) + '\n'
    
    arg1,add1 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    Compare(arg1,0)
    Jump(E_next,"je")
    
    traverse_tree(ast_node.children[1], E_begin ,E_next)
    Jump(E_begin,"jmp")

    code = code + str(E_next) + '\n'
    data = data + str(E_next) + '\n'

  elif ast_node.name == 'BREAK':
    Jump(breaklist,"jmp")
  elif ast_node.name == 'CONTINUE':
    Jump(nextlist,"jmp")

  elif ast_node.name == 'ForStatement3Exp':
    traverse_tree(ast_node.children[0], nextlist ,breaklist)

    E_next = label(name = ast_node.value)
    E_begin = label(name = ast_node.value)
    E_end = label(name = ast_node.value)

    code = code + str(E_begin) + '\n'
    data = data + str(E_begin) + '\n'

    arg1,add1 = traverse_tree(ast_node.children[1], nextlist ,breaklist)
    Compare(arg1,0)
    Jump(E_next,"je")

    traverse_tree(ast_node.children[3], E_end ,E_next)

    code = code + str(E_end) + '\n'
    data = data + str(E_end) + '\n'

    traverse_tree(ast_node.children[2], nextlist ,breaklist)
    Jump(E_begin,"jmp")

    code = code + str(E_next) + '\n'
    data = data + str(E_next) + '\n'

  elif ast_node.name == 'VarDecl':
    Decl(ast_node)
  elif ast_node.name == 'VarDecl and Initialise':
    add2 = Decl(ast_node)
    arg1= ''
    add1= ''
    if ast_node.children[1] is not None: 
      arg1,add1 = traverse_tree(ast_node.children[1], nextlist ,breaklist)
    arg3 = Assignment(ast_node.children[0].value,add2,arg1,add1)
    code = code +'\t' + str(arg3) +'\n'

  elif ast_node.name == 'Argument List':
    if len(ast_node.children) > 0 :
      for child in ast_node.children[::-1]:
        if child is not None: 
          arg1,add1 = traverse_tree(child, nextlist ,breaklist)
          PushParam(arg1,add1)

  elif ast_node.name == 'FuncCall':
    FuncCall(ast_node.children[0])

  elif ast_node.name == 'FuncCallwithArgs':
    if len(ast_node.children) > 0 :
      for child in ast_node.children :
        traverse_tree(child, nextlist ,breaklist)
    FuncCall(ast_node.children[0])

  elif ast_node.name == 'Function_definition':
    offset = 0
    arg1 = label(name = ast_node.value) 
    temp = ' '+str(get_size_symbole_table(ast_node.value, ast_node.scope_name))

    code = code + str(arg1) +temp + '\n'
    data = data + str(arg1) + '\n'

    # set_address_symbole_table(ast_node.value, ast_node.scope_name, 50)
    # print get_offset_symbole_table(ast_node.value, ast_node.scope_name)

    BeginFunc()
    if len(ast_node.children) > 0 :
      for child in ast_node.children :
        if child is not None: 
          traverse_tree(child, nextlist ,breaklist)
    EndFunc()
    symbol_table[0][ast_node.value][1] = symbol_table[0][ast_node.value][1] + ' ' + str(offset)
  # elif ast_node.name == 'paramater':
  #   PopParam(ast_node.value)

  elif ast_node.name == 'RETURN_EXPRESSION':
    arg1,add1 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    # PushParam(arg1)
    Ret()
  elif ast_node.name == 'RETURN':
    Ret()

  elif ast_node.name == 'Assignment':
    arg1,add1 = traverse_tree(ast_node.children[1], nextlist ,breaklist)
    arg3 = BinOp(ast_node.children[0].value, arg1, '','')
    code = code +'\t' + str(arg3) +'\n'

  elif ast_node.name in {'Addition','Logical AND','Logical OR','Multiplication','Modulus Operation',
    'Shift','Relation','EqualityExpression','AND', 'Exclusive OR','Inclusive OR'}:
    arg1,add1 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    arg2,add2 = traverse_tree(ast_node.children[1], nextlist ,breaklist)
    # for index,hash_table in enumerate(symbol_table):
    #   if hash_table['scope_name'] == 's0':
    arg = str(newtemp())
    symbol_table[0][arg] = [ast_node.type,'',-1,{},cparser.get_size(ast_node.type)]
 
    address = "[ebp-"+str(offset+int(cparser.get_size(ast_node.type)))+"]"
    set_address_symbole_table(arg, 's0',address)
    offset =offset+int(cparser.get_size(ast_node.type))

    arg3 = BinOp(str(arg),str(arg1),ast_node.children[2].value,str(arg2))
    code = code +'\t' + str(arg3) +'\n'

  elif ast_node.name == 'UnaryOperator':
    arg1,add2 = traverse_tree(ast_node.children[0], nextlist ,breaklist)
    arg3 = ''
    if(ast_node.children[1].value == '++'):
      arg3 = BinOp(str(arg1),str(arg1), '+',str(1))
    else: 
      arg3 = BinOp(str(arg1),str(arg1), '-',str(1))
    code = code +'\t' + str(arg3) +'\n'
    
  # elif ast_node.name == 'ArrayAccess':

  # elif ast_node.name == 'ArrayDeclaration':

  # elif ast_node.name == 'InitializerList':

  # elif ast_node.name == 'StructReference':

  # elif ast_node.name == 'Pointer Dereference':

  elif ast_node.name == 'Address Of Operation':
    arg = ast_node.children[0].value
  else:
    if len(ast_node.children) > 0 :
      for child in ast_node.children :
        if child is not None:
          traverse_tree(child, nextlist ,breaklist)
  return str(arg), add

def main():
  global symbol_table, root
  traverse_tree(root, None,None)
  return root, symbol_table
