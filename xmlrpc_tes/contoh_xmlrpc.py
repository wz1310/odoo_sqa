import xmlrpc.client
from datetime import date


success = False
vals_line = [] 
url = 'http://localhost:8013'
db = 'local_odoo'
username = 'andri.novian@kalbis.ac.id'
password = 'aan'
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
vals_line.append((0,0,{
	'product_id' : 25,
	'quantity' : 10,
	'price' : 2000,
	'uom_id' : 10
	}))
vals_header = {
	'tanggal': str(date.today()),
	'algoritma_pembelian_ids' : vals_line,
	'brand_ids': [(6,0, [5,6,7])],
}
try:
	new_algoritma_pembelian = models.execute_kw(db, uid, password, 'algoritma.pembelian', 'create', [vals_header])
	success = True
except Exception as exc:
	pass
if success == True:
	print("Data berhasil di create")
else:
	print("Data gagal")
