import xmlrpc.client
from datetime import date


success = False
vals_line = [] 
url = 'http://172.16.16.78:8069'
db = 'live_odoo'
username = 'admin'
password = 'kalbis123!!'
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

vals_header = {
	'name': 'Tes woi',
}
try:
	new_algoritma_pembelian = models.execute_kw(db, uid, password, 'hr.employee', 'create', [vals_header])
	success = True
except Exception as exc:
	pass
if success == True:
	print("Data berhasil di create")
else:
	print("Data gagal")
