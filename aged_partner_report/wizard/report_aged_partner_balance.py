import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from,
                                target_move, period_length):
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5 - (i + 1)) * period_length + 1) + \
                '-' + str((5 - i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        # build the reconciliation clause to see what partner needs to be
        # printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute(
            'SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where max_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        line_details = {}
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id']
                       for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, [])
                     for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type),
                           date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(
                line.company_id.currency_id, user_currency, line.balance)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency, partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= ResCurrency._compute(
                        partial_line.company_id.currency_id, user_currency, partial_line.amount)
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })
                if line.invoice_id.user_id:
                    inv_user_id = line.invoice_id.user_id
                    if inv_user_id.id not in line_details:
                        line_details.update(
                            {inv_user_id.id: [{
                                'partner_id': partner_id,
                                'period': 6,
                                'amount': line_amount}, {
                                'partner_id': partner_id,
                                'period': 7,
                                'amount': line_amount
                            }]})
                    else:
                        status = False
                        for details in line_details:
                            if details != 'unknown' and \
                                    details == inv_user_id.id:
                                for data in line_details[details]:
                                    if data['partner_id'] == partner_id:
                                        add_line_amount = line_amount + \
                                            data['amount']
                                        data.update(
                                            {'amount': add_line_amount})
                                        status = True
                                if not status:
                                    line_details[details].append({
                                        'partner_id': partner_id,
                                        'period': 6,
                                        'amount': line_amount})
                                    line_details[details].append({
                                        'partner_id': partner_id,
                                        'period': 7,
                                        'amount': line_amount})
                if not line.invoice_id or not line.invoice_id.user_id:
                    if 'unknown' not in line_details:
                        line_details.update({'unknown': [{
                            'partner_id': partner_id,
                            'period': 6,
                            'amount': line_amount}, {
                            'partner_id': partner_id,
                            'period': 7,
                            'amount': line_amount}]})
                    else:
                        status = False
                        for data in line_details['unknown']:
                            if data['partner_id'] == partner_id:
                                add_line_amount = line_amount + data['amount']
                                data.update(
                                    {'amount': add_line_amount})
                                status = True
                        if not status:
                            line_details[details].append({
                                'partner_id': partner_id,
                                'period': 6,
                                'amount': line_amount})
                            line_details[details].append({
                                'partner_id': partner_id,
                                'period': 7,
                                'amount': line_amount})
                        # Use one query per period and store results in history (a list variable)
                        # Each history will contain: history[1] = {'<partner_id>':
                        # <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(
                account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'],
                              periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(
                    line.company_id.currency_id, user_currency, line.balance)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency, partial_line.amount)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= ResCurrency._compute(
                            partial_line.company_id.currency_id, user_currency, partial_line.amount)

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })
                    if line.invoice_id.user_id:
                        for details in line_details:
                            status = False
                            if details != 'unknown' and \
                                    details == inv_user_id.id:
                                for data in line_details[details]:
                                    if data['partner_id'] == partner_id and \
                                            data['period'] in [i + 1, 7]:
                                        add_line_amount = line_amount + \
                                            data['amount']
                                        data.update(
                                            {'amount': add_line_amount})
                                        status = True
                                if not status:
                                    line_details[details].append({
                                        'partner_id': partner_id,
                                        'period': i + 1,
                                        'amount': line_amount})
                                    line_details[details].append({
                                        'partner_id': partner_id,
                                        'period': 7,
                                        'amount': line_amount})
                    if not line.invoice_id or not line.invoice_id.user_id:
                        status = False
                        if 'unknown' in line_details:
                            for data in line_details['unknown']:
                                if data['partner_id'] == partner_id and \
                                        data['period'] in [i + 1, 7]:
                                    add_line_amount = line_amount + \
                                        data['amount']
                                    data.update(
                                        {'amount': add_line_amount})
                                    status = True
                            if not status:
                                line_details['unknown'].append({
                                    'partner_id': partner_id,
                                    'period': i + 1,
                                    'amount': line_amount})
                                line_details['unknown'].append({
                                    'partner_id': partner_id,
                                    'period': 7,
                                    'amount': line_amount})

            history.append(partners_amount)
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            # Making sure this partner actually was found by the query
            if partner['partner_id'] in undue_amounts:
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] +
                                  [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env[
                    'res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(
                    browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
            users_partner_dict = {}
            for user_id in line_details:
                users_partner_dict.update({user_id: []})
                for partner_data in line_details[user_id]:
                    if partner_data['partner_id'] not in \
                            users_partner_dict[user_id]:
                        users_partner_dict[user_id].append(
                            partner_data['partner_id'])
        return res, total, lines, users_partner_dict, line_details

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']

        movelines, total, dummy, user_list, user_amount_dic = self._get_partner_move_lines(
            account_type, date_from, target_move, data['form']['period_length'])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'users': user_list,
            'user_total': user_amount_dic
        }


class AccountAgedPartner(models.AbstractModel):
    _inherit = 'account.aged.partner'

    @api.model
    def get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        results, total, amls, user_list, user_amount_dic = self.env[
            'report.account.report_agedpartnerbalance'].with_context(
            include_nullified_amount=True)._get_partner_move_lines(
            account_types, self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in \
                    options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in (
                            'in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [line['period'] == 6 - i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                        'action_context': aml.get_action_context(),
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'class': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'parent_id': 'partner_%s' % (values['partner_id'],),
                    'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                }
                lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 'None',
                'columns': [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines
