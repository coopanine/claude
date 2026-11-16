import math
from labelkit import Source, build_pdf, render, PT, ELEMENTS as E
from final_a import make_final
from v3cap import GOLD_RULE, DASH, WRAP_PAGE
from precise import ink
SHIFT, NARROW = 1.5, 0.5
def make(src):
    pl,extra,geo,R=make_final(src)
    left=E['facts_box']+E['facts_content']+E['other1']+E['other2']+E['dist1']+E['dist2']
    pl.shift(left,5.3355-SHIFT,0)
    b=ink(src,pl,E['facts_box']); pl.set_rect(E['facts_box'][0],b[0]+NARROW,b[1],b[2]-NARROW,b[3])
    prot=[i for n in ('p_box','p_title','p_dir','p_num','p_steps','p_warn','p_body','p_stor','p_stor_text','p_fda_box','p_fda_text','upc') for i in E[n]]
    pl.shift(prot,SHIFT,0)
    b=ink(src,pl,E['p_box']); pl.set_rect(E['p_box'][0],b[0]+NARROW,b[1],b[2]-NARROW,b[3])
    return pl,extra
if __name__=='__main__':
    src=Source('src.pdf'); pl,extra=make(src)
    fh,ph=0.1764,0.1729
    fb=ink(src,pl,E['facts_box']); st=ink(src,pl,E['statue']); pb=ink(src,pl,E['p_box'])
    fc=ink(src,pl,E['facts_content']); pt=ink(src,pl,E['p_fda_box'])
    r=188/(2*math.pi); ax=94.936
    print('gap L %.2f R %.2f back %.2f'%(st[0]-fb[2]-fh,pb[0]-ph-st[2],188-pb[2]-ph+fb[0]-fh))
    print('edge angles %.1f %.1f deg'%(math.degrees((ax-fb[2]-fh)/r),math.degrees((pb[0]-ph-ax)/r)))
    print('facts margins L %.2f R %.2f | protocol FDA margins L %.2f R %.2f | protocol to overlap %.2f'%(fc[0]-fb[0],fb[2]-fc[2],pt[0]-pb[0],pb[2]-pt[2],188-pb[2]-ph))
    D='/home/user/claude/lucid_mockups/option_a_proof/'
    build_pdf(src,pl,D+'TESTIDE_OptionA_Proof_Clean.pdf',title='TESTIDE label - Option A',recolor=GOLD_RULE,drop_ids=DASH,**extra)
    import pymupdf; pymupdf.open(D+'TESTIDE_OptionA_Proof_Clean.pdf')[0].get_pixmap(dpi=300).save(D+'TESTIDE_OptionA_Proof_Clean.png')
    build_pdf(src,pl,'vG_art.pdf',recolor=GOLD_RULE,page_mm=WRAP_PAGE,keep_mm=(-5,0,196,157),drop_layers=('/MC2','/MC3'),drop_ids=DASH,**extra)
    render('vG_art.pdf','vG_tex.png',zoom=20/PT)
