"""Author the canonical specification Word report using python-docx.
Only needed for rebuilding documentation, not running simulation.
"""
from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'CANONICAL_SYSTEMS.md'
OUTPUT=ROOT/'CANONICAL_SYSTEMS.docx'
BLUE=RGBColor(24,50,74); TEAL=RGBColor(17,121,115); GRAY=RGBColor(89,110,133); DARK=RGBColor(33,49,66)

D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.75);sec.bottom_margin=Inches(.75);sec.left_margin=Inches(.88);sec.right_margin=Inches(.88)
sec.header_distance=Inches(.31);sec.footer_distance=Inches(.37)
styles=D.styles
norm=styles['Normal'];norm.font.name='Aptos';norm.font.size=Pt(9.5);norm.font.color.rgb=DARK
norm.paragraph_format.space_after=Pt(6);norm.paragraph_format.line_spacing=1.16
for name,size,before,after in [('Title',30,0,12),('Heading 1',17,19,7),('Heading 2',12.7,15,5),('Heading 3',10.6,9,4)]:
 st=styles[name];st.font.name='Aptos Display';st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=BLUE
 st.paragraph_format.space_before=Pt(before);st.paragraph_format.space_after=Pt(after);st.paragraph_format.keep_with_next=True
styles['Subtitle'].font.name='Aptos';styles['Subtitle'].font.size=Pt(13);styles['Subtitle'].font.color.rgb=GRAY
if 'Canon Note' not in styles:
 s=styles.add_style('Canon Note',WD_STYLE_TYPE.PARAGRAPH);s.base_style=norm;s.font.size=Pt(8.4);s.font.italic=True;s.font.color.rgb=GRAY
if 'Mono Inline' not in styles:
 s=styles.add_style('Mono Inline',WD_STYLE_TYPE.CHARACTER);s.font.name='Consolas';s.font.size=Pt(8);s.font.color.rgb=TEAL
header=sec.header.paragraphs[0];header.text='FOUNDERS  /  CIV     •     SYSTEMS CANON';header.style='Caption';header.alignment=WD_ALIGN_PARAGRAPH.LEFT
header.runs[0].font.bold=True;header.runs[0].font.color.rgb=TEAL;header.runs[0].font.size=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run('v0.18  •  CONTROLLED SPECIFICATION     |     ');run.font.color.rgb=GRAY;run.font.size=Pt(8)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

p=D.add_paragraph();p.paragraph_format.space_before=Pt(70)
r=p.add_run('FOUNDERS–CIV');r.bold=True;r.font.name='Aptos Display';r.font.size=Pt(34);r.font.color.rgb=BLUE
p=D.add_paragraph();r=p.add_run('Canonical Systems Specification');r.font.name='Aptos Display';r.font.size=Pt(21);r.font.color.rgb=TEAL
p=D.add_paragraph('Universe • Physics • Ecology • Cognition • Soul Networks • Social Structure • RSW/CIV-OS')
p.style='Subtitle';p.paragraph_format.space_after=Pt(40)
for a,b in [('EDITION','v0.18 / Canon & Observatory'),('DATE','November 5, 2026'),('SCOPE','Established simulation canon with implementation readiness'),('IMPORTANT','Canon ≠ executable coverage. Synthetic models are not empirical verification.')]:
 p=D.add_paragraph();r=p.add_run(a+'   ');r.bold=True;r.font.size=Pt(9);r.font.color.rgb=TEAL
 rr=p.add_run(b);rr.font.size=Pt(10)
D.add_paragraph('Prepared as the companion technical reference for the runnable local Founders-CIV Observatory release. The source registry is preserved in founders_civ/canon.py.').style='Canon Note'
D.add_page_break()
D.add_heading('Quick reference',level=1)
D.add_paragraph('The simulation has 19 registered system areas. Each is classified as operational, partial, or specified; that classification is a statement about today’s Python engine, not a judgment about worldbuilding canon.')
t=D.add_table(rows=1, cols=3);t.style='Light Shading Accent 1';t.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,text in enumerate(['Status','Meaning','Example']):t.rows[0].cells[i].text=text
for row in [('Operational','A mechanism exists, is exercised and audited','Material/energy transactions'),('Partial','Some mechanics exist; important rules are not implemented','Species ecology and Fear Logic'),('Specified','Design rule is canonical but lacks executable mechanics','Founder checkpoint resurrection')]:
 cells=t.add_row().cells
 for i,x in enumerate(row):cells[i].text=x
D.add_heading('Reading this specification',level=2)
D.add_paragraph('The numbered sections first explain the agreed systems and research requirements. Section 10 reproduces the authoritative system-by-system register, including an explicit missing-features statement. A system in the register is not automatically a working simulation mechanic.')
D.add_heading('Key non-negotiable distinctions',level=2)
for s in ['Matter is neither energy nor an actor inventory item automatically created by a harvest.','Willingness, conviction and available physical capability are different dimensions of actor agency.','Hearing a lesson, believing it and mastering a skill are different events.','A spiritual or religious commitment affects physical outcomes through real behavior; no magical production bonus is implied.','A populated food web without births is not a sustainable ecosystem.','Fine x/y dots in the animated dashboard are schematic, not simulated physics.']:
 D.add_paragraph(s,style='List Bullet')
D.add_page_break()

def append_inlines(p,text):
 parts=re.split(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)',text)
 for token in parts:
  if not token:continue
  if token.startswith('**') and token.endswith('**'):
   r=p.add_run(token[2:-2]);r.bold=True
  elif token.startswith('`') and token.endswith('`'):
   r=p.add_run(token[1:-1]);r.style='Mono Inline'
  elif token.startswith('*') and token.endswith('*'):
   r=p.add_run(token[1:-1]);r.italic=True
  else:p.add_run(token)

lines=SOURCE.read_text(encoding='utf8').splitlines()
start=False
for line in lines:
 t=line.strip()
 if t.startswith('## 1.'):start=True
 if not start or not t:continue
 if t.startswith('# '):continue
 if t.startswith('### '):D.add_heading(t[4:],level=3);continue
 if t.startswith('## '):
  h=t[3:];n=int(h.split('.')[0]) if re.match(r'^\d+\.',h) else 0
  if n in (4,6,8,10,12) and n!=1:D.add_page_break()
  D.add_heading(h,level=1);continue
 if t.startswith('- '):p=D.add_paragraph(style='List Bullet');append_inlines(p,t[2:]);continue
 if re.match(r'^\d+\. ',t):p=D.add_paragraph(style='List Number');append_inlines(p,re.sub(r'^\d+\. ','',t));continue
 if t.startswith('**') and t.endswith('**') and len(t)<160:
  p=D.add_paragraph();p.paragraph_format.space_before=Pt(6);append_inlines(p,t);continue
 p=D.add_paragraph();append_inlines(p,t.replace('  ',' '))

D.core_properties.title='Founders-CIV v0.18 Canonical Systems Specification'
D.core_properties.subject='Consolidated simulation rulebook and execution readiness register'
D.core_properties.author='Founders-CIV Project'
D.core_properties.keywords='Founders-CIV, RSW, simulation, ecology, Soul Network, canon'
D.save(OUTPUT)
print('wrote',OUTPUT,'bytes',OUTPUT.stat().st_size)
