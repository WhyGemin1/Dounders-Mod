"""Optional release-author tool. Requires python-docx: pip install python-docx."""
from pathlib import Path
import re,sys
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/CANONICAL_SIMULATION_SPEC.md'
OUTPUT=ROOT/'Founders_CIV_v018_Canonical_Systems.docx'
navy=RGBColor(23,48,69);teal=RGBColor(16,122,118);muted=RGBColor(92,115,133)
doc=Document();section=doc.sections[0];section.top_margin=Inches(.77);section.bottom_margin=Inches(.72);section.left_margin=Inches(.9);section.right_margin=Inches(.85)
styles=doc.styles
normal=styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(8.95);normal.font.color.rgb=navy;normal.paragraph_format.space_after=Pt(5);normal.paragraph_format.line_spacing=1.11
for name,size,color,before,after in [('Title',32,navy,6,18),('Heading 1',16,teal,17,7),('Heading 2',11.5,navy,12,5),('Heading 3',10,teal,8,4)]:
 st=styles[name];st.font.name='Aptos Display' if name=='Title' else 'Aptos';st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=color;st.paragraph_format.space_before=Pt(before);st.paragraph_format.space_after=Pt(after);st.paragraph_format.keep_with_next=True
# Running page furniture
header=section.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=header.add_run('FOUNDERS–CIV   /   CANONICAL SYSTEMS');run.bold=True;run.font.size=Pt(7.8);run.font.color.rgb=teal
footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run('v0.18  •  Experimental simulator   |   Page ');r.font.color.rgb=muted;r.font.size=Pt(8)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def add_rich(p,t):
 parts=re.split(r'(\*\*.*?\*\*|`[^`]*`|\*[^*]+\*)',t)
 for part in parts:
  if part.startswith('**') and part.endswith('**'):
   r=p.add_run(part[2:-2]);r.bold=True
  elif part.startswith('`') and part.endswith('`'):
   r=p.add_run(part[1:-1]);r.font.name='Consolas';r.font.size=Pt(8.2);r.font.color.rgb=teal
  elif part.startswith('*') and part.endswith('*') and len(part)>2:
   r=p.add_run(part[1:-1]);r.italic=True
  else:p.add_run(part)

def shade(cell,color):
 tcPr=cell._tc.get_or_add_tcPr();shd=OxmlElement('w:shd');shd.set(qn('w:fill'),color);tcPr.append(shd)

def make_table(lines):
 rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines]
 if len(rows)>=2 and all(set(x.replace(':','').replace('-','').strip())==set() for x in rows[1]):rows.pop(1)
 rows=[r for r in rows if r and not all(re.fullmatch(r'[-: ]+',x or '-') for x in r)]
 if not rows:return
 count=len(rows[0]);t=doc.add_table(rows=1,cols=count);t.autofit=True;t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for i,text in enumerate(rows[0]):
  cell=t.rows[0].cells[i];cell.text='';shade(cell,'174455');p=cell.paragraphs[0];add_rich(p,text)
  for run in p.runs:run.font.bold=True;run.font.size=Pt(8);run.font.color.rgb=RGBColor(255,255,255)
 for j,row in enumerate(rows[1:]):
  cells=t.add_row().cells
  for i in range(count):
   cell=cells[i];cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;cell.text='';p=cell.paragraphs[0]
   add_rich(p,row[i] if i<len(row) else '')
   for run in p.runs:run.font.size=Pt(7.8)
   if j%2==1:shade(cell,'EEF4F5')
 for row in t.rows:
  trPr=row._tr.get_or_add_trPr();el=OxmlElement('w:cantSplit');trPr.append(el)
 doc.add_paragraph().paragraph_format.space_after=Pt(0)

# Cover page
p=doc.add_paragraph();p.paragraph_format.space_before=Pt(70);r=p.add_run('FOUNDERS–CIV');r.font.name='Aptos Display';r.font.size=Pt(15);r.bold=True;r.font.color.rgb=teal
p=doc.add_paragraph(style='Title');p.add_run('Canonical Systems\n& Simulation Rules')
p=doc.add_paragraph();p.paragraph_format.space_after=Pt(20);r=p.add_run('v0.18  /  Canon & Observatory');r.font.size=Pt(17);r.font.color.rgb=muted
p=doc.add_paragraph();p.paragraph_format.space_before=Pt(8);p.paragraph_format.space_after=Pt(26)
add_rich(p,'A consolidated specification of the **House and Wellspring**, individual Founders, energy and material laws, **animals and ecology**, **Soul Networks**, social learning, **RSW / Fear Logic**, governance, and executable testing requirements.')
T=doc.add_table(rows=2,cols=2);T.autofit=False
summaries=[('25','Tracked canonical systems'),('4','Operational in current core'),('17','Partial implementations'),('4','Specified-only systems')]
for i,(number,label) in enumerate(summaries):
 cell=T.cell(i//2,i%2);shade(cell,'E6F2F1' if i%2==0 else 'EEF3F6');cell.text='';p=cell.paragraphs[0];r=p.add_run(number+'\n');r.bold=True;r.font.size=Pt(24);r.font.color.rgb=teal;r=p.add_run(label);r.font.color.rgb=navy;r.font.size=Pt(9)
p=doc.add_paragraph();p.paragraph_format.space_before=Pt(25)
add_rich(p,'**Important:** Canon describes what is true within the fictional universe. Implementation status describes what the current code can actually simulate. Unspecified numerical rates are not automatically canon.')
p=doc.add_paragraph();p.paragraph_format.space_before=Pt(18)
r=p.add_run('Consolidated 5 November 2026   •   Local Python simulation   •   Seeded reproducible experiments');r.font.size=Pt(8.7);r.font.color.rgb=muted
p.add_run().add_break(WD_BREAK.PAGE)

lines=SOURCE.read_text(encoding='utf-8').splitlines();i=0
while i<len(lines):
 line=lines[i].strip()
 if not line or line.startswith('**Release:**') or line.startswith('**Canon consolidation') or line.startswith('**Implementation baseline') or line.startswith('**Scope:**') or line.startswith('# Founders-CIV —'):
  i+=1;continue
 if line.startswith('|'):
  block=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   block.append(lines[i]);i+=1
  make_table(block);continue
 if line.startswith('### '):p=doc.add_paragraph(line[4:],style='Heading 2')
 elif line.startswith('## '):p=doc.add_paragraph(line[3:],style='Heading 1')
 elif line.startswith('# '):p=doc.add_paragraph(line[2:],style='Heading 1')
 elif line.startswith('> '):
  p=doc.add_paragraph();p.paragraph_format.left_indent=Inches(.24);p.paragraph_format.space_before=Pt(9);p.paragraph_format.space_after=Pt(11);add_rich(p,line[2:]);p.style='Quote'
 elif line.startswith('- '):
  p=doc.add_paragraph(style='List Bullet');add_rich(p,line[2:])
 elif re.match(r'^\d+\. ',line):
  p=doc.add_paragraph(style='List Number');add_rich(p,re.sub(r'^\d+\. ','',line))
 else:
  # Join wrapped markdown prose paragraphs into one Word paragraph.
  paragraph=[line]
  while i+1<len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith(('#','>','- ','|')) and not re.match(r'^\d+\. ',lines[i+1].strip()):
   paragraph.append(lines[i+1].strip());i+=1
  p=doc.add_paragraph();add_rich(p,' '.join(paragraph))
 i+=1

# Styling trick for keep with next in tables not needed; set doc props
doc.core_properties.title='Founders-CIV v0.18: Canonical Systems and Simulation Rules'
doc.core_properties.subject='Simulation universe, implementation traceability and operating standards'
doc.core_properties.author='Founders-CIV project'
doc.save(OUTPUT)
print(OUTPUT)
