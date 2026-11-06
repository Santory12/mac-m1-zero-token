import contextlib
import csv
import io
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / 'src'

def module(name):
    return runpy.run_path(str(SRC / name))

class Regression(unittest.TestCase):
    def test_compact_numbered_heading(self):
        c = module('cleandoc.py')
        text = c['clean_text_compact']('Конфиденциальность\nPrivate\n2. Производительность\n500 пользователей', 'doc.txt')
        self.assertIn('500 пользователей', text)

    def test_ocr_uses_fresh_stdout(self):
        c = module('cleandoc.py')
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'a.pdf'
            p.with_suffix('.txt').write_text('STALE')
            with patch('subprocess.run', return_value=subprocess.CompletedProcess([],0,'FRESH','')):
                self.assertEqual(c['convert_to_markdown'](str(p)), 'FRESH')
            with patch('subprocess.run', return_value=subprocess.CompletedProcess([],1,'','failed')):
                with self.assertRaises(RuntimeError): c['convert_to_markdown'](str(p))

    def test_invalid_hours(self):
        w = module('validate_wbs.py')
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d)/'a.csv'
            for hours, valid in [(['-5','abc','10','2'],False),(['NaN','Infinity','0','0'],False),(['1.5','2.5','3','4'],True)]:
                with p.open('w') as f:
                    writer=csv.writer(f,delimiter=';');writer.writerow(w['EXPECTED_HEADERS']);writer.writerow(['Req','WBI','Build','Dev','Task','','']+hours)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(w['validate_wbs'](str(p)),valid)

    def test_xml_comment(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'a.xml';p.write_text('<odoo><!-- <tree> example </tree> --></odoo>')
            with contextlib.redirect_stdout(io.StringIO()): self.assertTrue(module('checkodoo.py')['check_xml'](str(p)))

    def test_non_tty_file(self):
        m=module('localai.py');seen=[]
        m['main'].__globals__['stream_generate']=lambda *a,**k:seen.append(a[0])
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'a.txt';p.write_text('UNIQUE_CONTENT')
            with patch.object(sys,'argv',['localai',str(p),'Summarize']),patch.object(sys,'stdin',io.StringIO('')): m['main']()
        self.assertIn('UNIQUE_CONTENT',seen[0])

    def test_search_literal_and_error(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d)/'a.txt').write_text('literal [ text')
            r=subprocess.run([sys.executable,str(SRC/'localsearch.py'),'[',d],capture_output=True,text=True)
            self.assertEqual(r.returncode,0);self.assertIn('literal [ text',r.stdout)
        m=module('localsearch.py')
        with patch.object(sys,'argv',['localsearch','query','.']),patch('subprocess.run',return_value=subprocess.CompletedProcess([],2,'','ERROR')),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as e:m['main']()
        self.assertEqual(e.exception.code,2)

    def test_excel_decimal_and_literal_formula(self):
        import openpyxl
        m=module('generate_wbs_xlsx.py');w=module('validate_wbs.py')
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'a.csv';out=pathlib.Path(d)/'a.xlsx'
            with p.open('w') as f:
                writer=csv.writer(f,delimiter=';');writer.writerow(w['EXPECTED_HEADERS']);writer.writerow(['=1+1','WBI','Build','Dev','Task','','','1.5','2.5','3','4'])
            with contextlib.redirect_stdout(io.StringIO()):m['build_wbs_xlsx'](str(p),str(p),str(out))
            wb=openpyxl.load_workbook(out);self.assertEqual(wb.active['H2'].value,1.5);self.assertEqual(wb.active['A2'].data_type,'s')

if __name__ == '__main__': unittest.main()
