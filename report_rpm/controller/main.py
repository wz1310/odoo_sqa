from odoo import http
from odoo.http import content_disposition, request
import base64
import logging

_logger = logging.getLogger(__name__)


class RpmDownload(http.Controller):
    @http.route('/rencana-pembelian-material-report-download', type='http', auth='user')
    def download_rpm_report(self, model, id, filename=None, **kw):
        Model = request.env[model]
        res = Model.browse(int(id))
        filecontent = base64.b64decode(res.data_x or '')
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
            return request.make_response(
                filecontent,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename + '.xlsx'))
                ]
            )
