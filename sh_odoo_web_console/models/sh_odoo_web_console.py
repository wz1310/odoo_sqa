# -*- coding: utf-8 -*-
import sys
import ast
from io import StringIO
from odoo import fields, models


class ShOdooWebConsole(models.TransientModel):
    _name = 'sh.odoo.web.console'
    _description = 'SH Odoo Web Console'

    name = fields.Char('Name', default='Web Console')
    code = fields.Text('Code', default='''result = self.env['res.partner'].search_read([], ['id','name','email'], limit=2)\nprint(result)''')
    result = fields.Text('Result', default='\n>>>')

    def multiline_eval(self, expr, context={}):
        tree = ast.parse(expr)
        eval_expr = ast.Expression(tree.body[-1].value)
        exec_expr = ast.Module(tree.body[:-1])

        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        exec(compile(exec_expr, 'file', 'exec'), context)
        eval(compile(eval_expr, 'file', 'eval'), context)

        sys.stdout = old_stdout
        message = mystdout.getvalue()
        return message

    def run(self):
        self.result = False
        res = '<No output>\n please use "Print()" to see the output'
        context = {"self": self}
        if self.code:
            try:
                res= self.multiline_eval(self.code, context)
                if not res:
                    res = '<No output>'
            except Exception as e:
                print('Error: ',e)
                res = '<Wrong input> %s' % str(e)
        res += '\n>>>'
        self.result = res

    def clear(self):
        self.code = False
