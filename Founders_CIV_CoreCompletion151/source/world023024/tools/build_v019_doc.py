"""Build a readable Word version of the v0.19 four-system development guide."""
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'docs/V019_FOUR_SYSTEMS_DEVELOPMENT.md').read_text()
out=ROOT/'docs/Founders_CIV_v019_Four_Systems_Development.docx'
D=Document();sec=D.sections[0];sec.top_margin=Inches(.78);sec.bottom_margin=Inches(.73);sec.left_margin=Inches(.86);sec.right_margin=Inches(.86)
styles=D.styles
for sn in ['Normal','List Bullet','List Number']:
    s=styles[sn];s.font.name='Aptos';s.font.size=Pt(9.5);s.font.color.rgb=RGBColor(39,52,72)
    s.paragraph_format.space_after=Pt(5)
for sn,size,color in [('Title',22,(21,40,65)),('Heading 1',15,(19,75,90)),('Heading 2',11.8,(26,68,95)),('Heading 3',10.2,(31,86,101))]:
    st=styles[sn];st.font.name='Aptos Display';st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=RGBColor(*color)
    st.paragraph_format.space_before=Pt(12 if sn!='Title' else 0)
    st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.keep_with_next=True
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run('FOUNDERS-CIV  •  v0.19 experimental systems  •  not yet live-engine integrated');r.font.size=Pt(8);r.font.color.rgb=RGBColor(100,115,130)

lines=src.splitlines();i=0

def inline(p,line):
    line=line.replace('**','').replace('`','')
    p.add_run(line)

def shade(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd');shd.set(qn('w:fill'),fill);tcPr.append(shd)

while i<len(lines):
    line=lines[i].strip()
    if not line:
        i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[x.strip().replace('**','').replace('`','') for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'-+:?|:-+',x) for x in cells):rows.append(cells)
            i+=1
        if len(rows)>0:
            tab=D.add_table(rows=0,cols=len(rows[0]));tab.style='Light Shading Accent 1';tab.alignment=WD_TABLE_ALIGNMENT.CENTER
            for idx,row in enumerate(rows):
                rc=tab.add_row().cells
                for j,val in enumerate(row[:len(rc)]):
                    rc[j].text=val;rc[j].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    for p in rc[j].paragraphs:
                        for run in p.runs:run.font.size=Pt(8.1)
                    if idx==0:shade(rc[j],'E6F0F4')
            D.add_paragraph().paragraph_format.space_after=Pt(2)
        continue
    if line.startswith('# '):
        p=D.add_paragraph(style='Title');inline(p,line[2:]);i+=1;continue
    if line.startswith('## '):
        p=D.add_paragraph(style='Heading 1');inline(p,line[3:]);i+=1;continue
    if line.startswith('### '):
        p=D.add_paragraph(style='Heading 2');inline(p,line[4:]);i+=1;continue
    if re.match(r'^\d+\. ',line):
        p=D.add_paragraph(style='List Bullet');inline(p,re.sub(r'^\d+\. ','',line));i+=1;continue
    if line.startswith('* '):
        p=D.add_paragraph(style='List Bullet');inline(p,line[2:]);i+=1;continue
    if line.startswith('---'):
        i+=1;continue
    # Concatenate hard-wrap continuations into same paragraph
    chunks=[line.rstrip('  ')];i+=1
    while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','* ','---')) and not re.match(r'^\d+\. ',lines[i].strip()):
        chunks.append(lines[i].strip().rstrip('  '));i+=1
    p=D.add_paragraph();inline(p,' '.join(chunks))
D.save(out)
print(out)
