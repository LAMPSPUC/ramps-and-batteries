# -*- coding: utf-8 -*-
"""Gera o TikZ das duas figuras do Caso Brasil e a tabela de liquidacao,
a partir dos MESMOS dados e do MESMO modelo usados no deck HTML."""
import json, math
def rnd(x): return int(math.floor(x+0.5)) if x>=0 else -int(math.floor(-x+0.5))
from modelo import ST, D1, D2, HFIX, HFLEX, W, R1, R2, T1, T2, DT, th, cost, precos
D=json.load(open('dia04.json'))
RHO, E = 14.3, 2000.0

# ---------- despacho e liquidacao ----------
def dispatch(rho, e):
    R=rho/100.*HFLEX*DT; best=None
    for i in range(40001):
        h1=min(R1+e,HFLEX)*i/40000.
        h2=min(h1+R, R2-e, HFLEX)
        if h2<0: continue
        t1,t2=R1+e-h1, R2-e-h2
        if t1<-1e-9 or t2<-1e-9: continue
        c1,c2=th(max(t1,0)),th(max(t2,0))
        if c1==float('inf') or c2==float('inf'): continue
        v=c1+W*h1+c2+W*h2
        if best is None or v<best[0]: best=(v,h1,h2,max(t1,0),max(t2,0),c1,c2)
    return best

def settle(rho,Ecap):
    _,p1,p2,e = precos(rho,Ecap)
    v,h1,h2,t1,t2,c1,c2 = dispatch(rho,e)
    row=lambda q1,q2,c: (p1*q1+p2*q2, c, p1*q1+p2*q2-c)
    ag={'fix':row(HFIX,HFIX,0.0), 'flex':row(h1,h2,W*(h1+h2)), 'term':row(t1,t2,c1+c2), 'bat':row(-e,e,0.0)}
    pago=p1*D1+p2*D2
    ag['dem']=(-pago,None,None)
    ag['soma']=(sum(ag[k][0] for k in ('fix','flex','term','bat'))-pago,
                sum(ag[k][1] for k in ('fix','flex','term')),
                sum(ag[k][2] for k in ('fix','flex','term','bat')))
    return p1,p2,e,ag

s0=settle(RHO,0.0); s1=settle(RHO,E)
M=lambda v: "" if v is None else f"{v/1e6:,.1f}".replace(",","@").replace(".",",").replace("@",".")
linhas=[]
for k in ('fix','flex','term'):
    linhas.append((k, [M(s0[3][k][i]) for i in range(3)], [M(s1[3][k][i]) for i in range(3)]))
linhas.append(('bat', ["","",""], [M(s1[3]['bat'][i]) for i in range(3)]))
linhas.append(('dem', [M(s0[3]['dem'][0]),"",""], [M(s1[3]['dem'][0]),"",""]))
linhas.append(('soma',[M(s0[3]['soma'][i]) for i in range(3)], [M(s1[3]['soma'][i]) for i in range(3)]))
out={'p0':(rnd(s0[0]),rnd(s0[1])), 'p1':(rnd(s1[0]),rnd(s1[1])), 'E':int(E), 'rho':RHO,
     'linhas':linhas}
json.dump(out, open('beamer_tabela.json','w'), ensure_ascii=False)
print("precos: sem bateria %d -> %d | com %d MWh: %d -> %d" % (rnd(s0[0]),rnd(s0[1]),E,rnd(s1[0]),rnd(s1[1])))
for k,a,b in linhas: print(f"  {k:<5} sem {a} | com {b}")

# ---------- figura 1: a curva do dia ----------
WID, HGT = 7.15, 2.60
SX, SY, SC = WID/23.0, HGT/110000.0, HGT/5000.0
TOP = HGT + 0.25
F=lambda n: "\\fontsize{%s}{%s}\\selectfont" % (n, round(n*1.2,1))
f=["\\begin{tikzpicture}[x=1cm,y=1cm]"]
f.append(f"  \\draw[rulec,line width=.6pt] (0,0) -- ({WID:.2f},0);")
f.append(f"  \\draw[rulec,line width=.6pt] (0,0) -- (0,{TOP:.2f});")
f.append(f"  \\draw[rulec,line width=.6pt] ({WID:.2f},0) -- ({WID:.2f},{TOP:.2f});")
for v in (0,25000,50000,75000,100000):
    y=v*SY
    f.append(f"  \\draw[rulec,line width=.6pt] (-.07,{y:.3f}) -- (0,{y:.3f});")
    f.append(f"  \\node[left,muted,font={F(5.2)}] at (-.09,{y:.3f}) {{{v//1000}}};")
for v,lab in ((0,"0"),(2500,"2,5k"),(5000,"5k")):
    y=v*SC
    f.append(f"  \\draw[rulec,line width=.6pt] ({WID:.2f},{y:.3f}) -- ({WID+0.07:.2f},{y:.3f});")
    f.append(f"  \\node[right,brick,font={F(5.2)}] at ({WID+0.09:.2f},{y:.3f}) {{{lab}}};")
bw=SX*0.62
for h in range(24):
    x=h*SX; y=min(D["cmo"][h],5000)*SC
    f.append(f"  \\fill[brick,opacity=.17] ({x-bw/2:.3f},0) rectangle ({x+bw/2:.3f},{y:.3f});")
def poly(series, style):
    return f"  \\draw[{style}] " + " -- ".join(f"({h*SX:.3f},{min(series[h],110000)*SY:.3f})" for h in range(24)) + ";"
f.append(poly(D["carga"], "muted,line width=.45pt"))
f.append(poly(D["erv"],   "tealx,line width=.65pt"))
f.append(poly(D["ctrl"],  "ink,line width=1.0pt"))
for h,lab in ((T1,"t1"),(T2,"t2")):
    x=h*SX
    f.append(f"  \\draw[ink,line width=.35pt,dashed] ({x:.3f},0) -- ({x:.3f},{TOP:.2f});")
    f.append(f"  \\filldraw[fill=paperbg,draw=ink,line width=.7pt] ({x:.3f},{D['ctrl'][h]*SY:.3f}) circle (1.3pt);")
    an,dx = ("right",.08) if h<12 else ("left",-.08)
    f.append(f"  \\node[{an},ink,font={F(5.6)}\\bfseries] at ({x+dx:.3f},{TOP-0.10:.2f}) {{{lab}}};")
    f.append(f"  \\node[{an},brick,font={F(5.2)}] at ({x+dx:.3f},{TOP-0.33:.2f}) {{{rnd(D['ctrl'][h]/1000)} GW}};")
for h in range(0,24,3):
    f.append(f"  \\node[below,muted,font={F(5.2)}] at ({h*SX:.3f},-.04) {{{h}h}};")
f.append("\\end{tikzpicture}")
open("fig-dia.tikz","w").write("\n".join(f))
open("fig-dia-en.tikz","w").write("\n".join(f).replace("}h}}","h}}").replace("{0h}","{0}").replace("{3h}","{3}").replace("{6h}","{6}").replace("{9h}","{9}").replace("{12h}","{12}").replace("{15h}","{15}").replace("{18h}","{18}").replace("{21h}","{21}").replace("2,5k","2.5k"))

# ---------- figura 2: a pilha de ordem de merito ----------
ordem=[(0.0,HFIX,"fix")]+sorted([(c,m,"thm") for c,m in ST]+[(W,HFLEX,"hyd")], key=lambda x:x[0])
TOT=sum(o[1] for o in ordem); YMAX=1400.
QX, PY = WID/TOT, HGT/YMAX
g=["\\begin{tikzpicture}[x=1cm,y=1cm]"]
acc=0.0
for c,m,kind in ordem:
    x0,x1=acc*QX,(acc+m)*QX
    y = 0.10 if kind=="fix" else min(c,YMAX)*PY
    col={"fix":"muted,opacity=.42","hyd":"tealx,opacity=.28","thm":"brick,opacity=.26"}[kind]
    g.append(f"  \\fill[{col}] ({x0:.3f},0) rectangle ({x1:.3f},{y:.3f});")
    acc+=m
acc=0.0; pts=[]
for c,m,kind in ordem:
    y=min(c,YMAX)*PY
    pts.append(f"({acc*QX:.3f},{y:.3f}) -- ({(acc+m)*QX:.3f},{y:.3f})"); acc+=m
g.append("  \\draw[ink,line width=.6pt] " + " -- ".join(pts) + ";")
g.append(f"  \\draw[rulec,line width=.6pt] (0,0) -- ({WID:.2f},0);")
g.append(f"  \\draw[rulec,line width=.6pt] (0,0) -- (0,{TOP:.2f});")
for p in (0,350,700,1050,1400):
    y=p*PY
    g.append(f"  \\draw[rulec,line width=.6pt] (-.07,{y:.3f}) -- (0,{y:.3f});")
    g.append(f"  \\node[left,muted,font={F(5.2)}] at (-.09,{y:.3f}) {{{p}}};")
for gw in range(0,101,25):
    g.append(f"  \\node[below,muted,font={F(5.2)}] at ({gw*1000*QX:.3f},-.04) {{{gw}}};")
for d,lab in ((D1,"t1"),(D2,"t2")):
    x=d*QX
    g.append(f"  \\draw[ink,line width=.35pt,dashed] ({x:.3f},0) -- ({x:.3f},{TOP:.2f});")
    an,dx = ("right",.08) if d==D1 else ("left",-.08)
    g.append(f"  \\node[{an},ink,font={F(5.6)}\\bfseries] at ({x+dx:.3f},{TOP-0.10:.2f}) {{{lab}}};")
    g.append(f"  \\node[{an},brick,font={F(5.2)}] at ({x+dx:.3f},{TOP-0.33:.2f}) {{{rnd(d/1000)} GW}};")
for p,lab in ((s0[0],"t1"),(s0[1],"t2")):
    y=max(min(p,YMAX),0)*PY
    g.append(f"  \\draw[brick,line width=.7pt] (0,{y:.3f}) -- ({WID:.2f},{y:.3f});")
    g.append(f"  \\node[right,fill=brick,text=white,inner sep=1pt,font={F(5.0)}] at (.06,{y+0.13:.3f}) {{{lab} $\\rightarrow$ {rnd(p)}}};")
g.append("\\end{tikzpicture}")
open("fig-pilha.tikz","w").write("\n".join(g))
open("fig-pilha-en.tikz","w").write("\n".join(g))
print("figuras regeradas em %.2f x %.2f cm" % (WID,HGT))
