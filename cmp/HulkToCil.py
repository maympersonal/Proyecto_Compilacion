import cmp.cil_h as cil
from cmp.semantic import VariableInfo, Context, Type, Method
from cmp.ast_h import *
from typing import List, Dict
import math

class HulkToCil:
    def __init__(self, context: Context) -> None:
        self.dottypes: List[cil.TypeNode] = []
        self.dotdata: List[cil.DataNode] = []
        self.dotcode: List[cil.FunctionNode] = []
        self.current_type: Type = None
        self.current_method : cil.MethodNode = None
        self.current_function: cil.FunctionNode = None
        self.context: Context = context
        self.string_count = 0
        self._count = 0
        self.internal_count = 0
        self.methods = {}
        self.attrs = {}
    
    @property
    def params(self)-> List[cil.ParamNode]:
        return self.current_function.params
    
    @property
    def localvars(self)-> List[cil.LocalNode]:
        return self.current_function.localvars
    
    @property
    def instructions(self)-> List[cil.InstructionNode]:
        return self.current_function.instructions
    
    def generate_next_string_id(self):
        self.string_count += 1
        return f'string_{self.string_count}'
    
    def generate_next_id(self):
        self._count += 1
        return f'{self._count}'
    
    def get_local(self, name):
        return f'local_{name}'
    
    def register_local(self, vinfo: VariableInfo = None):
        if vinfo is not None and vinfo.name:
            vinfo.name = f'local_{vinfo.name}'
        else:
            name = f'local_{len(self.current_function.localvars)}'
            vinfo = VariableInfo(name, None)
            
        local_node = cil.LocalNode(vinfo.name, vinfo.type)
        self.current_function.localvars.append(local_node)
        return vinfo.name

    def define_internal_local(self):
        return self.register_local()

    def register_instruction(self, instruction):
        self.instructions.append(instruction)
        return instruction
    
    def to_function_name(self, method_name, type_name):
        # example: Main_main
        return f'{type_name}_{method_name}'
    
    def to_data_name(self, type_name, value):
        return f'{type_name}_{value}'
    
    def to_attr_name(self, type_name, attr_name):
        return f'{type_name}_{attr_name}'
    
    def register_function(self, function_name):
        function_node = cil.FunctionNode(function_name, [], [], [])
        self.dotcode.append(function_node)
        return function_node
    
    def register_param(self, vinfo):
        vinfo.name = self.build_internal_param(vinfo.name)
        arg_node = cil.ParamNode(vinfo.name)
        self.params.append(arg_node)
        return vinfo
    
    def get_param(self, name):
        return f"param_{name}"

    def get_var(self, name) -> cil.LocalNode:
        for var in self.localvars:
            if var.name == name:
                return var
        return None

    def build_internal_param(self, vname):
        vname = f"param_{vname}"
        # self.internal_count += 1
        return vname

    def register_type(self, name):
        type_node = cil.TypeNode(name)
        self.dottypes.append(type_node)
        return type_node

    def register_data(self, value):
        vname = f'data_{len(self.dotdata)}'
        data_node = cil.DataNode(vname, value)
        self.dotdata.append(data_node)
        return data_node
    
    def internal_param_vname(self, vname):
        self.internal_count += 1
        return f'param_{vname}'
    
    def register_param(self, vinfo: VariableInfo):
        vinfo.name = self.internal_param_vname(vinfo.name)
        arg_node = cil.ParamNode(vinfo.name)
        self.params.append(arg_node)
        return vinfo.name
    
    def is_attribute(self, vname):
        return vname not in [p.name for p in self.params] + [l.name for l in self.localvars]
    
    def add_builtin_entry(self):
        builtin_types = ["Object", "Number", "String", "Boolean"]
        for typex in builtin_types:
            last_function = self.current_function
            self.current_function = cil.FunctionNode(self.to_function_name('entry', typex), [], [], [])
            self.params.append(cil.ParamNode('self'))
            self.register_instruction(cil.ReturnNode('self'))
            self.dotcode.append(self.current_function)
            self.current_function = last_function

        # self.current_function = None
    
    def build_entry(self, node: TypeDeclaration):
        last_function = self.current_function
        self.current_function = self.register_function(self.to_function_name('entry', node.identifier))
        
        self.params.append(cil.ParamNode('self'))
        self.current_type.define_method('entry', [], [], 'Object')
        
        for attr, (_, attr_type) in self.attrs[self.current_type.name].items():
            instance = self.define_internal_local()
            self.register_instruction(cil.ArgNode('self'))
            self.register_instruction(cil.StaticCallNode(self.to_function_name(f'{attr}_entry', attr_type), instance))
            self.register_instruction(cil.SetAttribNode('self', self.to_attr_name(node.identifier,attr), instance, node.identifier))

        self.register_instruction(cil.ReturnNode('self'))
        self.current_function = last_function
    
    def build_constructor(self, node):
        # TODO: fix inherited constructor
        last_function = self.current_function

        self.current_function = self.register_function(
            self.to_function_name("constructor", node.identifier)
        )

        self.params.append(cil.ParamNode("self"))
        for arg in node.parameters:
            self.params.append(cil.ParamNode(arg.identifier))
        method = Method(
            "constructor", 
            [x.identifier for x in node.parameters], 
            [self.context.get_type(x.type) for x in node.parameters], 
            self.context.get_type(node.identifier), 
            node.parameters
        )
        self.current_type.define_method(method)

        for attr, (_, typex) in self.attrs[self.current_type.name].items():
            instance = self.define_internal_local()
            self.register_instruction(cil.ArgNode("self"))
            self.register_instruction(cil.StaticCallNode(
                self.to_function_name(f"{attr}_constructor",typex),
                instance
            ))
            self.register_instruction(cil.SetAttribNode(
                "self",
                self.to_attr_name(node.identifier, attr),
                instance,
                node.identifier
            ))

        self.register_instruction(cil.ReturnNode("self"))
        self.current_function = last_function
        
    # METODOS DE TIPOS BUILTIN 
    # OBJECT
    
    def object_abort(self,type):
        self.dotdata.append(
            cil.DataNode(f"abort_{type}", f"Abort called from class {type}\n")
        )
        error = f"abort_{type}"
        self.register_instruction(cil.RunTimeErrorNode(error))
    
    def object_copy(self):
        self.params.append(cil.ParamNode('self'))
        copy_temp = self.define_internal_local()
        self.register_instruction(cil.AllocateNode(self.current_type.name, copy_temp))
    
        for attr in self.attrs[self.current_type.name].keys():
            attr_temp = self.define_internal_local()
            attr_name = (
                self.to_attr_name(self.current_type.name, attr)
                if self.current_type.name not in ["Number", "String", "Boolean"]
                else attr
            )
            self.register_instruction(
                cil.GetAttribNode(
                    attr_temp, 
                    'self', 
                    attr_name, 
                    self.current_type.name)
                )
            self.register_instruction(
                cil.SetAttribNode(
                    copy_temp, 
                    attr_name, 
                    attr_temp, 
                    self.current_type.name)
                )
        self.register_instruction(cil.ReturnNode(copy_temp))
    
    def object_type_name(self):
        self.params.append(cil.ParamNode('self'))
        self.dotdata.append(cil.DataNode(f"type_name_{self.current_type.name}", f'{self.current_type.name}'))
        
        type_name = self.define_internal_local()
        self.register_instruction(cil.LoadNode(type_name, VariableInfo(f"type_name_{self.current_type.name}", None)))
        
        self.register_instruction(cil.ReturnNode(type_name))
    
    # STRING
    def string_length(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.LengthNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    def string_concat(self):
        self.params.append(cil.ParamNode('self'))
        
        other = VariableInfo('other', 'String')
        self.register_param(other)
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.ConcatNode(result, 'self', other.name))
        self.register_instruction(cil.ReturnNode(result))
        
    def string_substr(self):
        self.params.append(cil.ParamNode('self'))
        
        index = VariableInfo('index', 'Number')
        self.register_param(index)
        
        length = VariableInfo('length', 'Number')
        self.register_param(length)
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.SubstringNode(result, 'self', index.name, length.name))
        self.register_instruction(cil.ReturnNode(result)) 
    
    # Number
    def number_sqrt(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.SqrtNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))  
    
    def number_sin(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.SinNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    def number_cos(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.CosNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    def number_tan(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.TanNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    def number_exp(self):
        self.params.append(cil.ParamNode('self'))
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.ExpNode(result, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    def number_log(self):
        self.params.append(cil.ParamNode('self'))
        
        base = VariableInfo('base', 'Number')
        self.register_param(base)
        
        result = self.define_internal_local()
        
        self.register_instruction(cil.LogNode(result, base.name, 'self'))
        self.register_instruction(cil.ReturnNode(result))
    
    # ------------------------------------------- 
    
    def cil_abstract_method(self, mname, cname, specif_code):
        last_function = self.current_function
        self.current_type = self.context.get_type(cname, [])
        self.current_method = self.current_type.get_method(mname)
        self.current_function = cil.FunctionNode(
            self.to_function_name(mname, cname), [], [], []
        )

        if mname == "abort":  
            specif_code(cname)
        else:
            specif_code()

        self.dotcode.append(self.current_function)
        self.current_function = last_function
        self.current_type = None

        return (mname, self.to_function_name(mname, cname))
    
    def add_builtin_functions(self):
        # object
        object_type = cil.TypeNode('Object')
        object_type.attributes = []
        object_type.methods = [
            self.cil_abstract_method("abort", "Object", self.object_abort),
            self.cil_abstract_method("copy", "Object", self.object_copy),
            self.cil_abstract_method("type_name", "Object", self.object_type_name),
        ]
        
        # string
        
        self.attrs["String"] = {"length": (0, "Number"), "str_ref": (1, "String")}
        string_type = cil.TypeNode('String')
        string_type.attributes = [
            VariableInfo('length').name,
            VariableInfo('str_ref').name,
        ]
        string_type.methods = [
            self.cil_abstract_method("abort", "String", self.object_abort),
            self.cil_abstract_method("copy", "String", self.object_copy),
            self.cil_abstract_method("type_name", "String", self.object_type_name),
            self.cil_abstract_method("length", "String", self.string_length),
            self.cil_abstract_method("concat", "String", self.string_concat),
            self.cil_abstract_method("substr", "String", self.string_substr),
        ]
        
        # Number
        # ??
        self.attrs["Number"] = {"value": (0, "Number")}
        int_type = cil.TypeNode('Number')
        int_type.attributes = [VariableInfo('value').name]
        int_type.methods = [
            self.cil_abstract_method("abort", "Number", self.object_abort),
            self.cil_abstract_method("copy", "Number", self.object_copy),
            self.cil_abstract_method("type_name", "Number", self.object_type_name),
            #?  builtin math functions
            # self.cil_abstract_method("sqrt", "Number", self.number_sqrt),
            # self.cil_abstract_method("sin", "Number", self.number_sin),
            # self.cil_abstract_method("cos", "Number", self.number_cos),
            # self.cil_abstract_method("tan", "Number", self.number_tan),
            # self.cil_abstract_method("exp", "Number", self.number_exp),
            # self.cil_abstract_method("log", "Number", self.number_log),
            #? random 
        ]
        
        # Boolean
        #  ??
        self.attrs["Boolean"] = {"value": (0, "Boolean")}
        bool_type = cil.TypeNode('Boolean')
        bool_type.attributes = [VariableInfo('value').name]
        bool_type.methods = [
            self.cil_abstract_method("abort", "Boolean", self.object_abort),
            self.cil_abstract_method("copy", "Boolean", self.object_copy),
            self.cil_abstract_method("type_name", "Boolean", self.object_type_name),
        ]
        
        for t in [object_type, string_type, int_type, bool_type]:
            self.dottypes.append(t)  
        
    
    def register_abort(self):
        last_function = self.current_function
        self.current_function = cil.FunctionNode(self.to_function_name('abort', self.current_type.name), [], [], [])
        self.object_abort(self.current_type.name)
        self.dotcode.append(self.current_function)
        self.current_function = last_function
    
    def register_copy(self):
        last_function = self.current_function
        self.current_function = cil.FunctionNode(self.to_function_name('copy', self.current_type.name), [], [], [])
        self.object_copy()
        self.dotcode.append(self.current_function)
        self.current_function = last_function
    
    def register_type_name(self):
        last_function = self.current_function
        self.current_function = cil.FunctionNode(self.to_function_name('type_name', self.current_type.name), [], [], [])
        self.object_type_name()
        self.dotcode.append(self.current_function)
        self.current_function = last_function
        
    def register_object_functions(self):
        self.register_abort()
        self.register_copy()
        self.register_type_name()
    
    def reset_state(self):
        self.dottypes = []
        self.dotdata = []
        self.dotcode = []
        self.current_type = None
        self.current_method = None
        self.string_count = 0
        self.current_function = None
        self._count = 0
        self.context = None
        
    

class HulkToCilVisitor(HulkToCil):
    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(Program)
    def visit (self, node: Program, scope: Scope, return_var= None):
        # self.dotdata.append(cil.DataNode('pi', math.pi))
        
        # self.current_function = self.register_function('main')
        # self.current_vars: Dict[str, VariableInfo] = {}
        # # ?arriba así ?
        # # instance = self.define_internal_local()
        # # result = self.define_internal_local()
        
        # # main_method_name = self.to_function_name('main', 'Main')
        
        # # self.register_instruction(cil.AllocateNode('Main', instance))
        # # self.register_instruction(cil.ArgNode(instance))
        # # self.register_instruction(cil.StaticCallNode(main_method_name, result))
        # # self.register_instruction(cil.ReturnNode(0))
        # # self.current_function = self.register_function('main') #? dudoso esto
        # # self.current_type = self.context.get_type('Global')

        # for decl in node.program_decl_list:
        #     self.visit(decl, scope)
        # return cil.ProgramNode(self.dottypes, self.dotdata, self.dotcode)
        for tp in self.context.types.values():
            self.attrs[tp.name] = {
                attr.name: (i, htype.name) for i, (attr, htype) in enumerate(tp.all_attributes())
            }
            self.methods[tp.name] = {
                method.name: (i, htype.name) if htype.name != 'object' or method.name not in ["abort","type_name", "copy"]
                else (i, tp.name) for i, (method, htype) in enumerate(tp.all_methods())
            }
        self.current_function = cil.FunctionNode('main', [], [], [])
        self.dotcode.append(self.current_function)
        
        

        for decl in node.program_decl_list:
            self.visit(decl, scope)
        
        self.register_instruction(cil.ExitNode())
        
        
        
        program_node = cil.ProgramNode(self.dottypes, self.dotdata, self.dotcode)
        self.current_function = None

        self.reset_state()
        return program_node
    
    @visitor.when(FunctionDeclaration)
    def visit(self, node: FunctionDeclaration, scope, return_var=None):
        previous_method = self.current_method
        previous_function = self.current_function

        self.current_method = self.context.get_method(node.identifier, node.parameters)

        # Add function to .CODE
        self.current_function = self.register_function(node.identifier)
            #self.to_function_name(, self.current_method.return_type.name)

        # Add params
        # self.current_function.params.append(cil.ParamNode("self"))
        for pname in node.parameters:
            self.register_param(VariableInfo(pname.identifier, pname.type))

        # Body
        value = self.visit(node.body, scope)

        # Return
        if self.current_method.return_type.name == "Void":
            value = None
        self.register_instruction(cil.ReturnNode(value))

        self.current_method = previous_method
        self.current_function = previous_function

    @visitor.when(TypeMethodDeclaration)
    def visit(self, node: TypeMethodDeclaration, scope, return_var = None):
        previous_method = self.current_method
        previous_function = self.current_function

        self.current_method = self.current_type.get_method(node.identifier) #, node.parameters)

        # Add function to .CODE
        self.current_function = self.register_function(
            self.to_function_name(node.identifier, self.current_type.name)
        )

        # Add params
        self.current_function.params.append(cil.ParamNode("self"))
        for pname in node.parameters:
            self.register_param(VariableInfo(pname.identifier, pname.type))

        # Body
        value = self.define_internal_local()
        self.visit(node.body, scope, value)

        # Return
        if self.current_method.return_type.name == "Void":
            value = None
        self.register_instruction(cil.ReturnNode(value))

        self.current_method = previous_method
        self.current_function = previous_function

    @visitor.when(TypeDeclaration)
    def visit(self, node: TypeDeclaration, scope, return_var=None):
        self.current_type = self.context.get_type(node.identifier)

        self.register_abort()
        self.register_copy()
        self.register_type_name()

        type_node = self.register_type(self.current_type.name)

        current_type = self.current_type
        while current_type is not None:
            attributes = [
                (node.identifier + "_" + attr.name) for attr in current_type.attributes
            ]
           
            type_node.attributes.extend(attributes[::-1])
           
            current_type = current_type.parent

        type_node.attributes.reverse()

        type_node.methods = [(method_name, self.to_function_name(method_name, typex)) for method_name,(_, typex) in self.methods[node.identifier].items()]
        self.build_constructor(node)

        self.visit(node.decl_body, scope)

    @visitor.when(TypeInstanciation)
    def visit(self, node: TypeInstanciation, scope, return_var = None):
        _self = self.define_internal_local()
        self.register_instruction(cil.AllocateNode(node.identifier, _self))
        self.register_instruction(cil.ArgNode(_self))
        for arg in node.arguments:
            local_arg = self.get_local(arg.identifier)
            self.register_instruction(cil.ArgNode(local_arg))
        self.register_instruction(
            cil.StaticCallNode(self.to_function_name("constructor", node.identifier), return_var)
        )

    @visitor.when(TypeVarInit)
    def visit(self, node: TypeVarInit, scope, return_var=None):
        last_function = self.current_function

        self.current_function = self.register_function(self.to_function_name(f"{node.identifier.identifier}_constructor", self.current_type.name))

        self.params.append(cil.ParamNode("self"))
         
        # Assign init_expr if not None
        if node.expression:
            init_expr_value = self.define_internal_local()
            val = self.visit(node.expression, scope, init_expr_value)
            self.register_instruction(cil.ReturnNode(init_expr_value))                
        else: # Assign default value 
            default_var = self.define_internal_local()
            self.register_instruction(cil.ValueNode(default_var, node.type_downcast))
            self.register_instruction(cil.ReturnNode(default_var))
        
        self.current_function = last_function

    
    @visitor.when(VarInit)
    def visit(self, node: VarInit, scope: Scope, return_var= None):

        idx = self.get_local(node.identifier.identifier)
        value = self.visit(node.expression, scope, idx)

        if isinstance(node.identifier.identifier, VarAttr):
            self.register_instruction(cil.SetAttribNode(
                "self",
                self.to_attr_name(node.identifier.identifier.identifier, node.identifier.identifier.attr),
                value,
                node.expression.type
            ))
            # self.register_instruction(cil.AssignNode(return_var, value))
        else:
            if not any(idx == l.name for l in self.current_function.localvars):
                self.register_local(VariableInfo(node.identifier.identifier, node.identifier.type))
            self.register_instruction(cil.AssignNode(idx, value))
        # Add Assignment Node
        # if node.expression:

        # self.register_instruction(
        #     cil.SetAttribNode(
        #         "self",
        #         self.to_attr_name(self.current_type.name, node.id),
        #         return_var,
        #         self.current_type.name,
        #     )
        # )
        # else:
        #     self.register_instruction(cil.ValueNode(idx, node.type))
    
    @visitor.when(VarDeclaration)
    def visit(self, node: VarDeclaration, scope: Scope, return_var= None):
        new_scope = Scope(scope)
        for var_init in node.var_init_list:
            self.visit(var_init, new_scope)
        return self.visit(node.body, new_scope, return_var)
    
    
    @visitor.when(VarUse)
    def visit(self, node: VarUse, scope: Scope, return_var= None):
        # # see how to handle this shit
        if isinstance(node.identifier, VarAttr):
            self.register_instruction(cil.AssignNode(node.identifier.attr, "self"))
            return

        local_id = self.get_local(node.identifier)
        if any(local_id == l.name for l in self.current_function.localvars):
            # self.register_instruction(cil.AssignNode(node.identifier, local_id))
            return local_id

        param_id = self.get_param(node.identifier)
        if any(param_id == p.name for p in self.current_function.params):
            # self.register_instruction(cil.AssignNode(node.identifier, param_id))
            return param_id

        self.register_instruction(
            cil.GetAttribNode(
                node.identifier,
                "self",
                self.to_attr_name(self.current_type.name, node.identifier),
                self.current_type.name,
            )
        )

    @visitor.when(FunctionCall)
    def visit(self, node: FunctionCall, scope: Scope, return_var = None):
        for arg in node.arguments:
            arg_name = self.visit(arg, scope)
            self.register_instruction(cil.ArgNode(arg_name))
        ret = self.define_internal_local()
        self.register_instruction(cil.StaticCallNode(self.to_function_name(node.identifier, self.current_type.name), ret))

    @visitor.when(FullConditional)
    def visit(self, node: FullConditional, scope, return_var= None):
        # IF condition GOTO label
        condition_value = self.define_internal_local()
        self.visit(node.conditional_expression, scope, condition_value)
        then_label = "THEN_" + self.generate_next_id()
        self.register_instruction(cil.GotoIfNode(condition_value, then_label))

        # Else
        self.visit(node.else_elif_statement, scope, return_var)

        # GOTO end_label
        end_label = "END_IF_" + self.generate_next_id()  # Example: END_IF_120
        self.register_instruction(cil.GotoNode(end_label))

        # Then label
        self.register_instruction(cil.LabelNode(then_label))
        [self.visit(x, scope, return_var) for x in node.scope_list]

        # end_label
        self.register_instruction(cil.LabelNode(end_label))

    @visitor.when(WhileLoop)
    def visit(self, node: WhileLoop, scope: Scope, return_var = None):
        # While label
        while_label = "WHILE_" + self.generate_next_id()
        self.register_instruction(cil.LabelNode(while_label))

        # Condition
        c = self.define_internal_local()
        self.visit(node.condition, scope, c)

        # If condition GOTO body_label
        body_label = "BODY_" + self.generate_next_id()
        self.register_instruction(cil.GotoIfNode(c, body_label))

        # GOTO end_while label
        end_while_label = "END_WHILE_" + self.generate_next_id()
        self.register_instruction(cil.GotoNode(end_while_label))

        # Body
        self.register_instruction(cil.LabelNode(body_label))
        self.visit(node.body, self.define_internal_local(), return_var)

        # GOTO while label
        self.register_instruction(cil.GotoNode(while_label))

        # End while label
        self.register_instruction(cil.LabelNode(end_while_label))

        self.register_instruction(cil.ValueNode(return_var, "Void"))

    @visitor.when(LessThan)
    def visit(self, node: LessThan, scope, return_var = None):
        left = self.visit(node.expr1, scope)
        right = self.visit(node.expr2, scope)

        self.register_instruction(cil.LessNode(return_var, left, right))

    @visitor.when(LessEqual)
    def visit(self, node: LessThan, scope, return_var = None):

        left = self.visit(node.expr1, scope)
        right = self.visit(node.expr2, scope)

        self.register_instruction(cil.LessEqualNode(return_var, left, right))

    @visitor.when(GreaterThan)
    def visit(self, node: GreaterThan, scope, return_var = None):
        left = self.visit(node.expr2, scope)
        right = self.visit(node.expr1, scope)

        self.register_instruction(cil.LessNode(return_var, left, right))

    @visitor.when(GreaterEqual)
    def visit(self, node: GreaterEqual, scope, return_var = None):
        left = self.visit(node.expr2, scope)
        right = self.visit(node.expr1, scope)

        self.register_instruction(cil.LessEqualNode(return_var, left, right))

    @visitor.when(Equal)
    def visit(self, node: Equal, scope, return_var=None):
        left = self.visit(node.expr1, scope)
        right = self.visit(node.expr2, scope)
        
        if self.get_var(left).type == "String":
            self.register_instruction(cil.StrEqualNode(return_var, left, right))
        else:
            self.register_instruction(cil.EqualNode(return_var, left, right))

    @visitor.when(NotEqual)
    def visit(self, node: NotEqual, scope, return_var = None):
        left = self.visit(node.expr1, scope)
        right = self.visit(node.expr2, scope)

        self.register_instruction(cil.NotEqualNode(return_var, left, right))

    @visitor.when(Not)
    def visit(self, node: Not, scope, return_var = None):
        value = self.define_internal_local()
        self.visit(node.condition, scope, value)
        constant = self.define_internal_local()
        self.register_instruction(cil.StaticCallNode(self.to_function_name("constructor", "Bool"), constant))
        self.register_instruction(cil.AssignNode(constant, 1))
        self.register_instruction(cil.MinusNode(return_var, constant, value))

    @visitor.when(Add)
    def visit(self, node: VarUse, scope: Scope, return_var= None):
        # self.current_function = self.register_function("add_function")
        left = self.visit(node.term, scope)
        right = self.visit(node.aritmetic_operation, scope)
        var = self.define_internal_local()   # aquiii
        self.register_instruction(cil.PlusNode(var, left, right))
        return var
    
    @visitor.when(Sub)
    def visit(self, node: Sub, scope: Scope, return_var= None):
        # self.current_function = self.register_function("sub_function")
        left = self.visit(node.term, scope)
        right = self.visit(node.aritmetic_operation, scope)
        var = self.define_internal_local()
        self.register_instruction(cil.MinusNode(var, left, right))
        return var
    
    @visitor.when(Mult)
    def visit(self, node: Mult, scope: Scope, return_var= None):
        # self.current_function = self.register_function("mult_function")
        left = self.visit(node.factor, scope)
        right = self.visit(node.term, scope)
        var = self.define_internal_local()
        self.register_instruction(cil.StarNode(var, left, right))
        return var
    
    @visitor.when(Div)
    def visit(self, node: Div, scope: Scope, return_var= None):
        # self.current_function = self.register_function("div_function")
        left = self.visit(node.factor, scope)
        right = self.visit(node.term, scope)
        var = self.define_internal_local()
        self.register_instruction(cil.DivNode(var, left, right))
        return var
    
    @visitor.when(Number)
    def visit(self, node: Number, scope: Scope, return_var= None):
        self.register_instruction(cil.ValueNode(node.value, "Number"))
        return node.value
    
    @visitor.when(Atom)
    def visit(self, node: Atom, scope: Scope, return_var= None):
        # self.register_instruction(cil.ValueNode(node.value))
        return node.value
    
    @visitor.when(Power)
    def visit(self, node: Power, scope: Scope, return_var= None):
        # self.current_function = self.register_function("pow_function")
        base = self.visit(node.base_exponent, scope)
        exp = self.visit(node.factor, scope)
        var = self.define_internal_local()
        self.register_instruction(cil.PowNode(var, base, exp))
        return var
    
    @visitor.when(UnaryBuildInFunction)
    def visit(self, node: UnaryBuildInFunction, scope: Scope, return_var= None):
        # arg = self.visit(node.argument, scope, return_var)
        if node.func == 'print':
            if return_var is None:
                return_var = self.define_internal_local()
            self.visit(node.argument, scope, return_var)
            if node.argument.__class__.__name__ == 'Number':
                self.register_instruction(cil.PrintIntNode(return_var))
            else:
                self.register_instruction(cil.PrintStrNode(return_var))
            return return_var   
        
    @visitor.when(String)
    def visit(self, node: String, scope: Scope, return_var):
        idx = self.generate_next_string_id()
        self.dotdata.append(cil.DataNode(idx, node.value))
        self.register_instruction(cil.LoadNode(return_var, VariableInfo(idx, "String", node.value))) 
    
    @visitor.when(Scope)
    def visit(self, node: Scope, scope, return_var=None):
        for statement in node.statements:
            self.visit(statement, scope, return_var)

    @visitor.when(DeclarationScope)
    def visit(self, node: DeclarationScope, scope, return_var=None):
        for statement in node.statements:
            self.visit(statement, scope, return_var)
        
    