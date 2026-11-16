from pathlib import Path
from datetime import datetime, timezone
import re, json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_ORIENT, WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import argparse
SOURCE=Path(__file__).resolve().parent
PAGES=json.loads((SOURCE/'pages.json').read_text())
REFS=json.loads((SOURCE/'references.json').read_text())
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()

ROOT=Path(__file__).resolve().parents[1]
REPORT=args.output_dir.resolve()
REPORT.mkdir(parents=True,exist_ok=True)
doc=Document()
sec=doc.sections[0]
sec.orientation=WD_ORIENT.LANDSCAPE
sec.page_width=Inches(11.69); sec.page_height=Inches(8.27)
sec.top_margin=Inches(.45); sec.bottom_margin=Inches(.45)
sec.left_margin=Inches(.45); sec.right_margin=Inches(.45)
sec.header_distance=Inches(.25); sec.footer_distance=Inches(.28)

styles=doc.styles
# The bundled Word template carries a blue Title border; remove paragraph rules.
for e in list(styles.element.iter(qn('w:pBdr'))):
    e.getparent().remove(e)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
    st=styles[name]; st.font.name='Calibri'; st.font.color.rgb=RGBColor(0,0,0)
normal=styles['Normal']; normal.font.size=Pt(10.5)
normal.paragraph_format.space_after=Pt(7)
normal.paragraph_format.line_spacing=1.05
normal.paragraph_format.widow_control=True
styles['Title'].font.size=Pt(22); styles['Title'].font.bold=True
styles['Title'].paragraph_format.space_after=Pt(12)
styles['Title'].paragraph_format.line_spacing=1.0
styles['Heading 1'].font.size=Pt(17); styles['Heading 1'].font.bold=True
styles['Heading 1'].paragraph_format.space_after=Pt(12)
styles['Heading 1'].paragraph_format.space_before=Pt(0)
styles['Heading 1'].paragraph_format.line_spacing=1.04
styles['Heading 2'].font.size=Pt(12); styles['Heading 2'].font.bold=True
styles['Heading 2'].paragraph_format.space_before=Pt(7)
styles['Heading 2'].paragraph_format.space_after=Pt(5)
styles['Heading 2'].paragraph_format.keep_with_next=True
styles['Subtitle'].font.size=Pt(13)
styles['Subtitle'].paragraph_format.space_after=Pt(5)

doc.core_properties.title='Immunotherapy resistance evidence and treatment implications'
doc.core_properties.subject='Case-specific evidence and therapeutic implications for Alexander Young'
doc.core_properties.author='Prepared with Codex for Alexander Young'
doc.core_properties.keywords='MSS colorectal cancer; immunotherapy resistance; immune recruitment; vaccines; N-803; vactosertib'
doc.core_properties.comments='Evidence and development status reviewed 16 November 2026.'
doc.core_properties.created=datetime.now(timezone.utc)
doc.core_properties.modified=doc.core_properties.created

# Page numbers are needed to navigate a clinical report with a reference appendix.
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run('Alexander Young  |  16 November 2026  |  '); r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string('666666')
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)

used=[]
def hyperlink(p,text,url,size=None):
    if url is None:
        r=p.add_run(text)
        if size:r.font.size=Pt(size)
        return
    h=OxmlElement('w:hyperlink'); h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement('w:r'); pr=OxmlElement('w:rPr')
    c=OxmlElement('w:color'); c.set(qn('w:val'),'244E70'); pr.append(c)
    if size:
        s=OxmlElement('w:sz'); s.set(qn('w:val'),str(int(size*2))); pr.append(s)
    r.append(pr); t=OxmlElement('w:t'); t.text=text; r.append(t); h.append(r); p._p.append(h)

def expand_cites(text):
    def sub(m):
        start,end=m.group(1),m.group(2)
        a=re.match(r'([A-Z]+)(\d+)',start); b=re.match(r'([A-Z]+)(\d+)',end)
        assert a[1]==b[1]
        return ' '.join('['+a[1]+str(i)+']' for i in range(int(a[2]),int(b[2])+1))
    return re.sub(r'\[([A-Z]+\d+)[–-]([A-Z]+\d+)\]',sub,text)

def clean_text(text):
    # Gene/value separators are explicit in the source; never split gene prefixes.
    protected=[]
    def protect(match):
        protected.append(match.group())
        return '__PROTECTED_'+chr(65+len(protected)-1)+'__'
    text=re.sub(r'10\.\d{4,9}/\S+|\b(?:Tgfbr2|Foxp3|Lrrc15)\b',protect,text)
    text=re.sub(r'\b(TPM|TMB|RNA|PFS|OS|ORR)(?=\d)',r'\1 ',text)
    text=re.sub(r'\b(The|This|Revised|Updated|Ranks|ranks|axis)(?=\d)',r'\1 ',text)
    text=text.replace('medianPFS','median PFS').replace('medianOS','median OS').replace('MSSCRC','MSS CRC').replace('HLA-A/B/C5','HLA-A/B/C 5').replace('HLA-A/B/C4','HLA-A/B/C 4').replace('HLA-A/B/C2','HLA-A/B/C 2')
    text=re.sub(r'([a-z]{3,})(\d)',r'\1 \2',text)
    text=re.sub(r'\b(by|of|at|in|on|is|or|and|vs|to|an)(?=\d)',r'\1 ',text)
    text=re.sub(r'(\d)(January|February|March|April|May|June|July|August|September|October|November|December)',r'\1 \2',text)
    text=re.sub(r'(January|February|March|April|May|June|July|August|September|October|November|December)(20\d\d)',r'\1 \2',text)
    text=re.sub(r'(\d)(CRC|MSS|patients|subjects|months|years|weeks|people|peptides|cases|mutations|tumours|canonical|queried|table-listed|gene-specific|sequences|targets|source-labelled|of|versus|Phase|phase|reported|reference|positive|monotherapy|responses|months|per|clinical|source|TPM|x10)',r'\1 \2',text)
    text=re.sub(r'\b(phase|Phase|Table|Part|rank|Rank|run|Run|ASCO|ESMO)(\d)',r'\1 \2',text)
    text=re.sub(r'(?<=[a-z])(?=20[12]\d\b)',' ',text)
    text=text.replace('CRCstudy','CRC study').replace('CRCresponses','CRC responses').replace('antiCD73','anti-CD73').replace('lowTMB','low TMB').replace('KRASwt','KRAS wild-type').replace('PFS1','PFS 1').replace('OS19','OS 19').replace('OS14','OS 14')
    text=re.sub(r'(?<=\d)%?th(?=[A-Za-z])',lambda m:m.group()+' ',text)
    text=re.sub(r'([;:])(?=\d)',r'\1 ',text)
    text=re.sub(r',(?=\d{1,2}(?:[A-Za-z/]|\s))',', ',text)
    text=text.replace('log 2(', 'log2(').replace('sponsor’s26', 'sponsor’s 26').replace("sponsor's26", "sponsor's 26")
    for i,value in enumerate(protected):text=text.replace('__PROTECTED_'+chr(65+i)+'__',value)
    return text

def text_into(p,text,size=None):
    text=expand_cites(clean_text(text))
    for bit in re.split(r'(\[[A-Z]+\d+\])',text):
        if re.fullmatch(r'\[[A-Z]+\d+\]',bit):
            key=bit[1:-1]
            assert key in REFS,key
            if key not in used: used.append(key)
            hyperlink(p,bit,REFS[key][2],size)
        else:
            r=p.add_run(bit)
            if size: r.font.size=Pt(size)

def ptext(text,small=False):
    p=doc.add_paragraph()
    if small:
        p.paragraph_format.space_after=Pt(6)
        p.paragraph_format.line_spacing=1.05
    text_into(p,text,9 if small else None)
    return p

def table(headers,rows,widths,font_size=10,padding=80):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for col,w in zip(t.columns,widths): col.width=Inches(w)
    for c,w in zip(t.rows[0].cells,widths): c.width=Inches(w)
    props=t._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    props.append(borders)
    for rowi,values in enumerate([headers]+rows):
        row=t.rows[0] if rowi==0 else t.add_row()
        if rowi==0:
            tag=OxmlElement('w:tblHeader'); row._tr.get_or_add_trPr().append(tag)
        cant=OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(cant)
        for coli,(c,txt,w) in enumerate(zip(row.cells,values,widths)):
            c.width=Inches(w); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=c._tc.get_or_add_tcPr()
            marg=OxmlElement('w:tcMar')
            for edge,val in [('top',padding),('bottom',padding),('left',90),('right',90)]:
                e=OxmlElement('w:'+edge); e.set(qn('w:w'),str(val));e.set(qn('w:type'),'dxa');marg.append(e)
            tcPr.append(marg)
            shade=OxmlElement('w:shd'); shade.set(qn('w:fill'),'24465F' if rowi==0 else ('F3F5F7' if rowi%2==0 else 'FFFFFF'));tcPr.append(shade)
            p=c.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1.02
            text_into(p,txt,font_size)
            if rowi==0:
                for r in p.runs:r.bold=True;r.font.color.rgb=RGBColor(255,255,255)
            if headers[coli]=='CRC percentile':p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    after=doc.add_paragraph();after.paragraph_format.space_after=Pt(1);after.paragraph_format.space_before=Pt(0);after.paragraph_format.line_spacing=1
    after.add_run().font.size=Pt(1)


for i,page in enumerate(PAGES):
    title,blocks=page['title'],page['blocks']
    landscape=page.get('landscape',False)
    if i:
        sec=doc.add_section(WD_SECTION_START.NEW_PAGE)
    else: sec=doc.sections[0]
    sec.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sec.page_width=Inches(11.69 if landscape else 8.27)
    sec.page_height=Inches(8.27 if landscape else 11.69)
    sec.left_margin=sec.right_margin=Inches(.5 if landscape else .65)
    sec.top_margin=sec.bottom_margin=Inches(.5 if landscape else .6)
    sec.header_distance=sec.footer_distance=Inches(.25)
    heading=doc.add_paragraph(title,'Title' if i==0 else 'Heading 1')
    for kind,data in blocks:
        if kind=='p': ptext(data)
        elif kind=='note':ptext(data,True)
        elif kind=='h':doc.add_paragraph(data,'Heading 2')
        elif kind=='table':
            headers,rows,widths,*opts=data
            table(headers,rows,widths,font_size=opts[0] if opts else 9.5,padding=70)
        elif kind=='figure':
            path,width,caption=data
            doc.add_picture(str(ROOT/path),width=Inches(width))
            ptext(caption,True)
        elif kind=='meta':
            p=ptext(data,True); p.paragraph_format.space_after=Pt(7)
        else: raise ValueError(kind)

# A compact, linked bibliography; manually grouped to keep each page readable.
keys=used.copy()
for n in range(0,len(keys),11):
    sec=doc.add_section(WD_SECTION_START.NEW_PAGE)
    sec.orientation=WD_ORIENT.PORTRAIT;sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.left_margin=sec.right_margin=Inches(.65);sec.top_margin=sec.bottom_margin=Inches(.6)
    doc.add_paragraph('Sources and provenance' if n==0 else 'Sources continued','Heading 1')
    for key in keys[n:n+11]:
        title,detail,url=REFS[key]
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(5)
        r=p.add_run('['+key+'] '+clean_text(title));r.bold=True;r.font.size=Pt(9)
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(10)
        r=p.add_run(clean_text(detail)+' ');r.font.size=Pt(9)
        if url:hyperlink(p,url,url,8)

out=REPORT/'immunotherapy_resistance_report_2026-11-16.docx'
doc.save(out)
(REPORT/'citation_manifest.json').write_text(json.dumps({k:REFS[k] for k in keys},indent=2))
print(out)
print('Designed pages',len(PAGES),'references',len(keys))
