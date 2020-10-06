import inspect
import ast
import textwrap

class State:
  def __init__(self, name, bits = 32, signed = False, init = 0):
    self.name = name
    self.bits = bits
    self.signed = signed
    self.init = init

class Param:
  def __init__(self, name, vals, bits = 32, signed = False):
    self.name = name
    self.bits = bits
    self.signed = signed
    self.vals = vals

class BasicStock:
  def get_point_bits(self): return 16

  def get_point_signed(self): return True

  def get_state_vars(self):
    return [
      State("total_profit", 32, True),
      State("shares_held", 16),
      State("last_price", 16),
      State("days_down", 4),
      State("days_up", 4)
    ]

  def get_params(self):
    return [
      Param("down_days_to_buy", [1], 4),
      Param("up_days_to_sell", [1], 4)
    ]

  def run(price):
    if self.days_down == self.down_days_to_buy:
      self.total_profit -= self.last_price
      self.shares_held += 1
      self.days_down = 0
    elif self.days_up == self.up_days_to_sell:
      self.total_profit += self.shares_held * self.last_price
      self.shares_held = 0

    if price >= self.last_price:
      self.days_down = 0
      self.days_up += 1
    else:
      self.days_up = 0
      self.days_down += 1

    self.last_price = price

def gen_v(comp):
  def get_only(arr):
    if len(arr) > 1:
      raise Exception("expected array to have only one element...")
    return arr[0]

  def convert_to_map(l):
    m = {}
    for e in l:
      m[e.name] = e
    return m

  first_line = comp.run.__code__.co_firstlineno
  comp_ast = ast.parse(textwrap.dedent(inspect.getsource(comp.run))).body[0]
  print(ast.dump(comp_ast))
  arg = get_only(comp_ast.args.args).arg
  arg_bits = comp.get_point_bits()
  arg_signed = comp.get_point_signed()
  params = convert_to_map(comp.get_params())
  states = convert_to_map(comp.get_state_vars())
  logics = "" 
  for l in list(params.values()) + list(states.values()):
    logics += "logic {}[{}:0] {};\n".format("signed " if (l.signed) else "", l.bits - 1, ('p_' if l.name in params else 's_') + l.name)
  logics += "\n"

  state_mappings = {s: "" for s in states}
  temp_mappings = {}
  def incr_mapping(mappings, var):
    nonlocal logics
    if mappings == temp_mappings and var not in mappings:
      mappings[var] = ""
    else:
      mappings[var] = str(int("0" if mappings[var] == "" else mappings[var]) + 1)
    if mappings == state_mappings:
      logics += "logic {}[{}:0] s_{}{};\n".format("signed " if (states[var].signed) else "", states[var].bits - 1, var, mappings[var])
    else:
      logics += "logic signed [31:0] t_{}{};\n".format(var, mappings[var])

  def op_to_str(op):
    if isinstance(op, ast.Eq): return "=="
    if isinstance(op, ast.GtE): return ">="
    if isinstance(op, ast.Gt): return ">"
    if isinstance(op, ast.LtE): return "<="
    if isinstance(op, ast.Lt): return "<"
    if isinstance(op, ast.Add): return "+"
    if isinstance(op, ast.Sub): return "-"
    if isinstance(op, ast.Mult): return "*"
    raise Exception("unknown op " + str(op) + " on line " + str(first_line + op.lineno))

  def wrap(expr): return "(" + expr + ")"
  def unwrap(expr): return expr[1:-1] if expr[0] == '(' else expr

  indent_spaces = 0
  def gen_expr(expr): # return str expr as well as whether signed
    nonlocal indent_spaces
    if isinstance(expr, ast.Compare):
      return (wrap(gen_expr(expr.left)[0] + op_to_str(get_only(expr.ops)) + gen_expr(get_only(expr.comparators))[0]), False)
    if isinstance(expr, ast.BinOp):
      left, ls = gen_expr(expr.left)
      right, rs = gen_expr(expr.right)
      if ls and not rs:
        right = "$signed(" + right + ")"
      if rs and not ls:
        left = "$signed(" + left + ")"
      return (wrap(left + op_to_str(expr.op) + right), ls or rs)
    if isinstance(expr, ast.BoolOp):
      return (wrap((" " + op_to_str(expr.op) + " ").join(map(lambda x: gen_expr(x)[0], expr.values))), False)
    if isinstance(expr, ast.Attribute):
      if expr.attr in params:
        return ("p_" + expr.attr, params[expr.attr].signed)
      else:
        return ("s_" + expr.attr + state_mappings[expr.attr], states[expr.attr].signed)
    if isinstance(expr, ast.Name):
      if expr.id == arg:
        return ("input_slice", arg_signed)
      else:
        return ("t_" + expr.id + temp_mappings[expr.id], True)
    if isinstance(expr, ast.Num):
      return (str(expr.n), expr.n < 0)
    if isinstance(expr, ast.IfExp):
      t = gen_expr(expr.body)
      f = gen_expr(expr.orelse)
      return (wrap(gen_expr(expr.test)[0] + " ? " + t[0] + " : " + f[0]), t[1] or f[1])
    if isinstance(expr, ast.If):
      result = (' ' * indent_spaces) + "if " + gen_expr(expr.test)[0] + " begin\n"
      indent_spaces += 2
      for stmt in expr.body:
        result += gen_expr(stmt)
      indent_spaces -= 2
      result += (' ' * indent_spaces) + "end"
      if len(expr.orelse) > 0:
        result += " else begin\n"
        indent_spaces += 2
        for stmt in expr.orelse:
          result += gen_expr(stmt)
        indent_spaces -= 2
        result += (' ' * indent_spaces) + "end"
      result += "\n"
      return result
    if isinstance(expr, ast.Assign):
      target = get_only(expr.targets)
      mappings, name = (state_mappings, target.attr) if isinstance(target, ast.Attribute) else (temp_mappings, target.id)
      val = unwrap(gen_expr(expr.value)[0])
      incr_mapping(mappings, name)
      return (' ' * indent_spaces) + gen_expr(target)[0] + " = " + val + ";\n"
    if isinstance(expr, ast.AugAssign):
      mappings, name = (state_mappings, expr.target.attr) if isinstance(expr.target, ast.Attribute) else (temp_mappings, expr.target.id)
      val = gen_expr(expr.value)[0]
      target_orig = gen_expr(expr.target)[0]
      incr_mapping(mappings, name)
      return (' ' * indent_spaces) + gen_expr(expr.target)[0] + " = " + target_orig + " " + op_to_str(expr.op) + " " + val + ";\n"
    raise Exception("unknown expr " + str(expr) + " on line " + str(first_line + expr.lineno))

  next_states = ""
  for stmt in comp_ast.body:
    next_states += gen_expr(stmt)
  next_states = textwrap.indent(next_states, '  ')
 
  param_setting = ""
  for i, p in enumerate(params.keys()):
    param_setting += ("if (param_input_counter == {}) begin\n"
                      "  p_{} <= input_word;\n"
                      "end\n").format(i, p)
  param_setting = textwrap.indent(param_setting, '  ')

  output_state_selection = ""
  for i, s in enumerate(states.keys()):
    output_state_selection += ("{}if (state_output_counter == {}) begin\n"
                               "  output_word_wire = s_{};\n"
                               "end").format(" else " if i > 0 else "", i, p)
  output_state_selection = textwrap.indent(output_state_selection, '  ')

  state_vars_init = ""
  state_vars_update = ""
  for s in states.values():
    state_vars_init += "s_{} <= {};\n".format(s.name, s.init)
    state_vars_update += "s_{} <= s_{}{};\n".format(s.name, s.name, state_mappings[s.name])
  state_vars_init = textwrap.indent(state_vars_init, ' ' * 4)
  state_vars_update = textwrap.indent(state_vars_update, ' ' * 4)

  input_slice = ("logic {}[{}:0] input_slice;\n"
                 "assign input_slice = input_word[{}:0];"
                 "").format("signed " if arg_signed else "", arg_bits - 1, arg_bits - 1)

  comp_name = type(comp).__name__
  template = open('main.sv').read()
  out_file = open(comp_name + ".sv", 'w')
  out_file.write(template.format(comp_name=comp_name,
    num_params=len(params), num_state_vars=len(states),
    logics=logics.rstrip(), input_slice=input_slice, param_setting=param_setting.rstrip(),
    output_state_selection=output_state_selection, next_states=next_states.rstrip(),
    state_vars_init=state_vars_init.rstrip(), state_vars_update=state_vars_update.rstrip()))
  out_file.close()

b = BasicStock()
gen_v(b)
# print textwrap.dedent(inspect.getsource(b.run))
# print ast.dump(ast.parse(textwrap.dedent(inspect.getsource(b.run))))
