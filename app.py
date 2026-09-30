from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os, json, re
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cybercase.db')
app = Flask(__name__)

# Small educational classifier trained on synthetic case descriptions.
TRAIN_TEXT = [
    'payment transfer unknown account urgent money',
    'fraudulent invoice bank transfer suspicious account',
    'threat message credential request phishing link',
    'normal delivery notification meeting reminder',
    'family chat dinner plans appointment reminder',
    'routine customer support question product order'
]
TRAIN_Y = [1,1,1,0,0,0]
VEC = TfidfVectorizer(ngram_range=(1,2), stop_words='english')
X = VEC.fit_transform(TRAIN_TEXT)
MODEL = LogisticRegression(random_state=42).fit(X, TRAIN_Y)


def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        incident_type TEXT,
        notes TEXT,
        risk INTEGER,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS evidence(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        evidence_type TEXT NOT NULL,
        description TEXT NOT NULL,
        timestamp TEXT,
        source TEXT,
        FOREIGN KEY(case_id) REFERENCES cases(id)
    )''')
    c.commit(); c.close()


def risk_analysis(items, notes=''):
    text = ' '.join([i.get('description','') for i in items] + [notes or ''])
    prob = float(MODEL.predict_proba(VEC.transform([text]))[0][1]) if text.strip() else 0.0
    keywords = ['payment','transfer','unknown account','invoice','phishing','password','credential','otp','threat','scam','urgent']
    hits = sum(1 for k in keywords if k in text.lower())
    score = min(99, int(30 + prob*45 + hits*5 + min(len(items), 6)*2))
    level = 'HIGH' if score >= 70 else 'MEDIUM' if score >= 45 else 'LOW'
    return score, level, prob, [k for k in keywords if k in text.lower()]


def timeline_rows(case_id):
    c = db(); rows = c.execute('SELECT * FROM evidence WHERE case_id=? ORDER BY timestamp, id', (case_id,)).fetchall(); c.close()
    return [dict(r) for r in rows]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cases', methods=['GET','POST'])
def cases():
    c = db()
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        title = str(data.get('title','')).strip()
        incident = str(data.get('incident_type','Online Fraud')).strip()
        notes = str(data.get('notes','')).strip()
        evidence = data.get('evidence', [])
        if not title: return jsonify({'error':'Case title is required.'}), 400
        if not isinstance(evidence, list): return jsonify({'error':'Evidence must be a list.'}), 400
        safe_items = []
        for e in evidence[:100]:
            desc = str(e.get('description','')).strip()
            if not desc: continue
            safe_items.append({'evidence_type': str(e.get('evidence_type','Message'))[:50], 'description': desc[:1000], 'timestamp': str(e.get('timestamp',''))[:50], 'source': str(e.get('source',''))[:100]})
        score, level, prob, hits = risk_analysis(safe_items, notes)
        now = datetime.utcnow().isoformat(timespec='seconds')
        cur = c.execute('INSERT INTO cases(title,incident_type,notes,risk,created_at) VALUES(?,?,?,?,?)', (title,incident,notes,score,now))
        cid = cur.lastrowid
        for e in safe_items:
            c.execute('INSERT INTO evidence(case_id,evidence_type,description,timestamp,source) VALUES(?,?,?,?,?)', (cid,e['evidence_type'],e['description'],e['timestamp'],e['source']))
        c.commit(); c.close()
        return jsonify({'id':cid,'title':title,'incident_type':incident,'risk':score,'risk_level':level,'ai_probability':round(prob,3),'signals':hits,'evidence_count':len(safe_items)})
    rows = c.execute('SELECT id,title,incident_type,risk,created_at FROM cases ORDER BY id DESC LIMIT 20').fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/cases/<int:case_id>')
def case_detail(case_id):
    c = db(); row = c.execute('SELECT * FROM cases WHERE id=?',(case_id,)).fetchone(); c.close()
    if not row: return jsonify({'error':'Case not found'}),404
    items = timeline_rows(case_id)
    score, level, prob, hits = risk_analysis(items, row['notes'])
    return jsonify({'case':dict(row),'evidence':items,'risk_level':level,'ai_probability':round(prob,3),'signals':hits})

@app.route('/api/demo-case', methods=['POST'])
def demo_case():
    data = {
      'title':'Online Payment Fraud Investigation', 'incident_type':'Online Payment Fraud',
      'notes':'Victim reports an urgent payment request followed by a transfer to an unknown account.',
      'evidence':[
        {'evidence_type':'Chat','description':'Suspicious WhatsApp chat received asking for urgent payment.','timestamp':'2026-09-30 10:30','source':'WhatsApp'},
        {'evidence_type':'Bank Transfer','description':'Payment transfer of Rs 25000 to unknown account.','timestamp':'2026-09-30 11:02','source':'Bank record'},
        {'evidence_type':'Email','description':'Email with fraudulent invoice and urgent payment request.','timestamp':'2026-09-30 11:47','source':'Email'},
        {'evidence_type':'Call Recording','description':'Caller requested OTP and claimed the account needed immediate verification.','timestamp':'2026-09-30 12:15','source':'Call recording'}
      ]}
    with app.test_request_context(json=data):
        return cases()

@app.route('/api/cases/<int:case_id>/report')
def report(case_id):
    c = db(); row = c.execute('SELECT * FROM cases WHERE id=?',(case_id,)).fetchone(); c.close()
    if not row: return jsonify({'error':'Case not found'}),404
    items = timeline_rows(case_id); score, level, prob, hits = risk_analysis(items,row['notes'])
    styles=getSampleStyleSheet(); buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
    story=[Paragraph('CyberCase AI — Digital Evidence Investigation Report',styles['Title']), Spacer(1,10), Paragraph(f"Case #{case_id}: {row['title']}",styles['Heading2']), Paragraph(f"Incident type: {row['incident_type']}",styles['BodyText']), Paragraph(f"Risk score: {score}% ({level})",styles['BodyText']), Spacer(1,8), Paragraph('Case notes',styles['Heading3']), Paragraph(row['notes'] or 'No notes provided.',styles['BodyText']), Spacer(1,8), Paragraph('AI analysis',styles['Heading3']), Paragraph('Synthetic ML classifier output for educational use. Signals: '+(', '.join(hits) if hits else 'none detected')+'.',styles['BodyText']), Spacer(1,10), Paragraph('Evidence timeline',styles['Heading3'])]
    data=[['Time','Type','Source','Description']]+[[e['timestamp'] or '-',e['evidence_type'],e['source'] or '-',e['description']] for e in items]
    t=Table(data,colWidths=[75,70,80,300]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#172033')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.4,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),8),('PADDING',(0,0),(-1,-1),5)])); story += [t,Spacer(1,12),Paragraph('Disclaimer: This prototype is an educational case-management and evidence-organization tool. It does not establish guilt, identify real suspects, authenticate evidence, or replace qualified forensic investigation. Uploaded evidence is not sent to an external service by this application.',styles['BodyText'])]
    doc.build(story); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f'CyberCase_AI_Case_{case_id}_Report.pdf', mimetype='application/pdf')

init_db()
if __name__ == '__main__':
    app.run(debug=True)
