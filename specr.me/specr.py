# all the imports
#import sqlite3
import xmltodict
import random
import re
import psycopg2
from flask import Flask, request, g, redirect, url_for, render_template, flash
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired, Length


# configuration
DEBUG = False
SECRET_KEY = ''
USERNAME = ''
PASSWORD = ''

# create our little application :)
specr = Flask(__name__)
application = specr
specr.config.from_object(__name__)


def connect_db():
    return psycopg2.connect("dbname='specr' user='' host='localhost' password=''")


class UploadForm(Form):
    creator_name = StringField('Your Nickname', validators=[DataRequired(), Length(3, 25)])
    comp_name = StringField('Computer Name', validators=[DataRequired(), Length(3, 50)])


@specr.before_request
def before_request():
    g.db = connect_db()


@specr.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@specr.route('/') # Index page.
def index():
    form = UploadForm()
    return render_template('upload_computer.html', form=form)


@specr.route('/show/<comp>') # Show specific commputer
def show_computer(comp):
    hexcomp = comp
    comp = int(comp, 16)
    cur = g.db.cursor()
    cur.execute('select system_name, creator_name, mobo, cpu_name, gpu_name, mem_size, hdds, monitors from computers where urlid = %s', [comp])
    computer = [dict(system_name=row[0], creator_name=row[1], mobo=row[2], cpu_name=row[3], gpu_name=row[4], mem_size=row[5], hdds=row[6], monitors=row[7]) for row in cur.fetchall()]
    cur.execute('select urlid from computers order by urlid desc limit 1')
    max_urlid = int(cur.fetchone()[0])
    if computer:
        if 'O.E.M' in computer[0]['mobo']:
            computer[0]['mobo'] = 'unknown'
        computer[0]['mobo'] = computer[0]['mobo'].replace('All Series', 'unknown').replace('System Product Name', 'unknown')
        computer[0]['gpu_name'] = computer[0]['gpu_name'].replace('Unknown,', '').replace('unknown,', '')
        computer[0]['monitors'] = computer[0]['monitors'].replace('Unknown', 'Unknown Monitor').replace('unknown', 'Unknown Monitor')
        computer[0]['gpu_name'] = computer[0]['gpu_name'].split(',')
        computer[0]['hdds'] = computer[0]['hdds'].split(',')
        computer[0]['monitors'] = computer[0]['monitors'].split(',')
        computer[0]['mem_size'] = computer[0]['mem_size'] + ' GB RAM'
    try:
        return render_template('show_computer.html', computer=computer[0], comp=comp, max_urlid=max_urlid, hexcomp=hexcomp)
    except:
        flash('Invalid computer ID (URL) - you get a random instead!', 'warning')
        return redirect(url_for('random_computer'))


@specr.route('/show/last') # Hidden functionality: Show last submitted computer.
def last_computer():
    cur = g.db.cursor()
    cur.execute('select max(urlid) from computers')
    max_urlid = int(cur.fetchone()[0])
    max_comp = hex(max_urlid)[2:]
    try:
        return redirect(url_for('show_computer', comp=max_comp))
    except:
        flash('Invalid computer ID (URL) - you get a random instead!', 'warning')
        return redirect(url_for('random_computer'))


@specr.route('/random') # Show random computer.
def random_computer():
    cur = g.db.cursor()
    cur.execute('select max(urlid) from computers')
    max_urlid = int(cur.fetchone()[0])
    rnd_urlid = hex(random.randint(256, max_urlid))[2:]
    return redirect(url_for('show_computer', comp=rnd_urlid))


@specr.route('/prev/<comp>') # Show previous computer.
def prev_computer():
    cur = g.db.cursor()
    cur.execute('select max(urlid) from computers')
    max_urlid = int(cur.fetchone()[0])
    rnd_urlid = hex(random.randint(256, max_urlid))[2:]
    return redirect(url_for('show_computer', comp=rnd_urlid))


@specr.route('/next/<comp>') # Show next computer.
def next_computer():
    cur = g.db.cursor()
    cur.execute('select max(urlid) from computers')
    max_urlid = int(cur.fetchone()[0])
    rnd_urlid = hex(random.randint(256, max_urlid))[2:]
    return redirect(url_for('show_computer', comp=rnd_urlid))


@specr.route('/upload', methods=['GET', 'POST']) # Process and store  data from form into database.
def upload_computer():
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        try:
            xml = xmltodict.parse(file)
        except:
            flash('Invalid DxDiag.xml file (xmltodict)!', 'error')
            return redirect(url_for('index'))
        tmp_did = ''
        tmp_mid = ''
        tmp_hid = ''
        opti_words = ['cd', 'CD', 'Cd', 'dvd', 'DVD', 'Dvd', 'virtual', 'Virtual', 'atapi', 'ATAPI']
        parsed_specs = dict(system_name='', creator_name='', mobo='', cpu_name='', gpu_name='', mem_size='', hdds='', monitors='', os_ver='')
        try:
            parsed_specs['system_name'] = form.comp_name.data
            parsed_specs['creator_name'] = form.creator_name.data
            if request.headers.getlist("X-Real-IP"):
                parsed_specs['creator_IP'] = request.headers.getlist("X-Real-IP")[0]
            else:
                parsed_specs['creator_IP'] = request.remote_addr
            parsed_specs['mobo'] = xml['DxDiag']['SystemInformation']['SystemModel']
            parsed_specs['os_ver'] = re.sub('\(.*?\)','', xml['DxDiag']['SystemInformation']['OperatingSystem']).strip()
            if parsed_specs['mobo'] == ' ' or not None:
                parsed_specs['mobo'] = 'unknown'
            parsed_specs['cpu_name'] = xml['DxDiag']['SystemInformation']['Processor'].replace('(R)', '').replace('(TM)', '').replace('(tm)', '').strip()
            parsed_specs['mem_size'] = int(xml['DxDiag']['SystemInformation']['Memory'].replace('MB RAM', '')) / 1024
            try:
                for dd in xml['DxDiag']['DisplayDevices']['DisplayDevice']:
                    if dd['CardName'] and dd['DeviceID'] not in tmp_did:
                        tmp_name = dd['CardName']
                        if parsed_specs['gpu_name']:
                            parsed_specs['gpu_name'] = parsed_specs['gpu_name'] + ',' + tmp_name
                        else:
                            parsed_specs['gpu_name'] = tmp_name
                        tmp_did = tmp_did + dd['DeviceID']
                        tmp_sli = 0
                        for devid in xml['DxDiag']['SystemDevices']['SystemDevice']:
                            if dd['CardName'] in devid['Name']:
                                tmp_sli += 1
                        if tmp_sli > 1:
                            parsed_specs['gpu_name'] = parsed_specs['gpu_name'] + ' SLI ' + str(tmp_sli) + 'x'
                    try:
                        if len(dd['MonitorModel'][0]) > 1:
                            for monitor, monitorid in zip(dd['MonitorModel'], dd['MonitorId']):
                                if monitorid not in tmp_mid:
                                    if parsed_specs['monitors']:
                                        parsed_specs['monitors'] = parsed_specs['monitors'] + ',' + monitor
                                    else:
                                        parsed_specs['monitors'] = monitor
                                    tmp_mid = tmp_mid + monitorid
                        else:
                            if dd['MonitorId'] not in tmp_mid:
                                if parsed_specs['monitors']:
                                    parsed_specs['monitors'] = parsed_specs['monitors'] + ',' + dd['MonitorModel']
                                else:
                                    parsed_specs['monitors'] = dd['MonitorModel']
                                tmp_mid = tmp_mid + dd['MonitorId']
                    except:
                        pass
            except:
                parsed_specs['gpu_name'] = xml['DxDiag']['DisplayDevices']['DisplayDevice']['CardName']
                tmp_sli = 0
                for devid in xml['DxDiag']['SystemDevices']['SystemDevice']:
                    if xml['DxDiag']['DisplayDevices']['DisplayDevice']['CardName'] in devid['Name']:
                        tmp_sli += 1
                if tmp_sli > 1:
                    parsed_specs['gpu_name'] = parsed_specs['gpu_name'] + ' SLI ' + str(tmp_sli) + 'x'
                if len(xml['DxDiag']['DisplayDevices']['DisplayDevice']['MonitorModel'][0]) > 1:
                    for monitor, monitorid in zip(xml['DxDiag']['DisplayDevices']['DisplayDevice']['MonitorModel'], xml['DxDiag']['DisplayDevices']['DisplayDevice']['MonitorId']):
                        if monitorid not in tmp_mid:
                            if parsed_specs['monitors']:
                                parsed_specs['monitors'] = parsed_specs[
                                    'monitors'] + ',' + monitor
                            else:
                                parsed_specs['monitors'] = monitor
                            tmp_mid = tmp_mid + monitorid
                else:
                    parsed_specs['monitors'] = xml['DxDiag']['DisplayDevices']['DisplayDevice']['MonitorModel']
            if parsed_specs['monitors'].replace(' ', '') == '':
                parsed_specs['monitors'] = 'No Physical Monitor Detected'
            try:
                for dd in xml['DxDiag']['LogicalDisks']['LogicalDisk']:
                    if dd['Model'] and dd['PNPDeviceID'] not in tmp_hid:
                        if not any(word in dd['Model'] for word in opti_words):
                            if parsed_specs['hdds']:
                                parsed_specs['hdds'] = parsed_specs[
                                    'hdds'] + ',' + dd['Model']
                            else:
                                parsed_specs['hdds'] = dd['Model']
                        tmp_hid = tmp_hid + dd['PNPDeviceID']
            except:
                if not any(word in xml['DxDiag']['LogicalDisks']['LogicalDisk']['Model'] for word in opti_words):
                    parsed_specs['hdds'] = xml['DxDiag']['LogicalDisks']['LogicalDisk']['Model']
            parsed_specs['urlid'] = None
        except Exception as e:
            flash('Invalid DxDiag.xml file (parser)!', 'error')
            print(e)
            return redirect(url_for('index'))
        try:
            cur = g.db.cursor()
            cur.execute('insert into computers(system_name, creator_name, creator_IP, mobo, cpu_name, gpu_name, mem_size, hdds, monitors, os_ver) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [parsed_specs['system_name'], parsed_specs['creator_name'], parsed_specs['creator_IP'], parsed_specs['mobo'], parsed_specs['cpu_name'], parsed_specs['gpu_name'], parsed_specs['mem_size'],parsed_specs['hdds'], parsed_specs['monitors'], parsed_specs['os_ver']])
            g.db.commit()
            cur.execute('select urlid from computers order by urlid desc limit 1')
            urlid = hex(cur.fetchone()[0])[2:]
            return redirect(url_for('show_computer', comp=urlid))
        except Exception as e:
            flash('Invalid DxDiag.xml file (DB)!', 'error')
            print(e)
            return redirect(url_for('index'))
    flash('Wrong/invalid nickname or computer name!', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    specr.run(host='0.0.0.0', port='8090')
