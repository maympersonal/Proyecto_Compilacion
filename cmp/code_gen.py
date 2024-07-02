from cmp import visitor
from cmp import ast_h

REG_ZERO = "$zero" # constant 0
REG_RESERVED = "$at" # assembler reserved

REG_GLOBAL = "$gp" # global area pointer
REG_STACK_POINTER = "$sp" # stack pointer
REG_FRAME_POINTER = "$fp" # fram pointer
REG_RETURN_ADDR = "$ra" # return address

# os kernel reserved
REG_OS_RESERVED_0 = "$k0"
REG_OS_RESERVED_1 = "$k1"

# function return registers
REG_VALUE_0 = "$v0"
REG_VALUE_1 = "$v1"

# argument registers
REG_ARG_0 = "$a0"
REG_ARG_1 = "$a1"
REG_ARG_2 = "$a2"
REG_ARG_3 = "$a3"

# temporal registers (not preserved)
REG_TEMP_0 = "$t0"
REG_TEMP_1 = "$t1"
REG_TEMP_2 = "$t2"
REG_TEMP_3 = "$t3"
REG_TEMP_4 = "$t4"
REG_TEMP_5 = "$t5"
REG_TEMP_6 = "$t6"
REG_TEMP_7 = "$t7"
REG_TEMP_8 = "$t8"
REG_TEMP_9 = "$t9"
REG_TEMP_10 = "$t10"

# temporal saved registers (preserved)
REG_SAV_0 = "$s0"
REG_SAV_1 = "$s1"
REG_SAV_2 = "$s2"
REG_SAV_3 = "$s3"
REG_SAV_4 = "$s4"
REG_SAV_5 = "$s5"
REG_SAV_6 = "$s6"

class MIPSTranslator:
    def op_abs(src, dest):
        return f"abs {dest}, {src}"
    
    def op_add(r1, r2, dest):
        return f"add {dest}, {r1}, {r2}"
    
    def op_addu(r1, r2, dest):
        return f"addu {dest}, {r1}, {r2}"
    
    def op_and(r1, r2, dest):
        return f"and {dest}, {r1}, {r2}"

    def op_div(r1, r2, dest):
        return f"div {dest}, {r1}, {r2}"
    
    def op_divu(r1, r2, dest):
        return f"divu {dest}, {r1}, {r2}"

    def op_mult(r1, r2, dest):
        return f"mult {dest}, {r1}, {r2}"
    
    def op_multu(r1, r2, dest):
        return f"multu {dest}, {r1}, {r2}"
    
    def op_nor(r1, r2, dest):
        return f"nor {dest}, {r1}, {r2}"
    
    def op_not(src, dest):
        return f"not {dest}, {src}"
    
    def op_or(r1, r2, dest):
        return f"or {dest}, {r1}, {r2}"
    
    def op_rem(r1, r2, dest):
        return f"rem {dest}, {r1}, {r2}"
    
    def op_remu(r1, r2, dest):
        return f"remu {dest}, {r1}, {r2}"


class HulkMIPSGenerator:
    def __init__(self):
        super().__init__()

    @visitor.on('node')
    def visit(self, node, tabs):
        pass
    
    @visitor.when(ast_h.Node)
    def visit(self, node):
        pass   
    
    @visitor.when(ast_h.Program)
    def visit(self, node):
        term = self.visit(node.term)
        op = self.visit(node.aritmetic_operation)
        res = float(term)+float(op)
        print(res)
        return res