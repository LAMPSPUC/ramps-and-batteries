"""Duas horas do SIN em 04/02/2026: o vale (h12) e a ponta (h19) da curva do
parque controlavel. Calibrado com ONS (geracao, carga, CMO) e CCEE (PLD).

Hidraulica separada em duas parcelas:
  - inflexivel: o piso do dia (fio d'agua, vazao minima, usos multiplos). Nao rampeia.
  - flexivel: rampeia a rho%/h da propria capacidade, ao valor da agua.
Pilha termica com CVU do PMO de fevereiro de 2026. Bateria despachada de forma otima.
"""
import json
ST=sorted((u["cvu"],u["mw"]) for u in json.load(open('stack.json')))
D=json.load(open('dia04.json'))
T1,T2=D["vale"],D["pico"]                 # 12 e 19
D1,D2=D["ctrl"][T1],D["ctrl"][T2]         # 50.148 e 93.111 MW
HFIX,HFLEX=D["hfix"],D["hflex"]           # 41.696 e 39.352 MW
DT=T2-T1                                  # 7 horas entre as duas
W=D["cmo"][T1]                            # valor da agua = CMO da hora do vale
R1,R2=D1-HFIX, D2-HFIX

def th(q):
    rem,c=q,0.0
    for cvu,mw in ST:
        if rem<=1e-9: return c
        u=min(mw,rem); c+=u*cvu; rem-=u
    return c if rem<=1e-6 else float('inf')

def _run(rho,e,r1,r2):
    R=rho/100.*HFLEX*DT
    best=float('inf'); cand={0.0}
    acc=0.0
    for cvu,mw in ST:
        acc+=mw
        cand.add(r1+e-acc); cand.add(r2-e-acc-R)
    top=min(r1+e,HFLEX)
    for i in range(2001): cand.add(top*i/2000.)
    for h1 in cand:
        if h1<0 or h1>top: continue
        h2=min(h1+R,r2-e,HFLEX)
        if h2<0: continue
        t1,t2=r1+e-h1, r2-e-h2
        if t1<-1e-9 or t2<-1e-9: continue
        c1,c2=th(max(t1,0)),th(max(t2,0))
        if c1==float('inf') or c2==float('inf'): continue
        v=c1+W*h1+c2+W*h2                 # blocos de 1 hora
        if v<best: best=v
    return best

def cost(rho,E,r1=R1,r2=R2,n=60):
    best,arg=float('inf'),0.0
    for i in range(n+1):
        e=E*i/n; v=_run(rho,e,r1,r2)
        if v<best: best,arg=v,e
    return best,arg

def precos(rho,E,d=10.0):
    base,e=cost(rho,E)
    p1=(cost(rho,E,R1+d,R2)[0]-base)/d
    p2=(cost(rho,E,R1,R2+d)[0]-base)/d
    return base,p1,p2,e

if __name__=="__main__":
    print(f"vale h{T1}={D1:,.0f} MW  ponta h{T2}={D2:,.0f} MW  ({DT} h)")
    print(f"hidro: piso {HFIX:,} flexivel {HFLEX:,} | valor da agua {W} R$/MWh")
    print(f"residual: t1={R1:,.0f}  t2={R2:,.0f}")
    obs=(D["hid"][T1],D["hid"][T2],D["ter"][T1],D["ter"][T2])
    print(f"\n{'rho %/h':>8}{'preco t1':>10}{'preco t2':>10}{'spread':>10}")
    for rho in (14.3,12,10,8,6,4):
        _,p1,p2,_=precos(rho,0)
        print(f"{rho:>8.1f}{p1:>10,.1f}{p2:>10,.1f}{p2-p1:>10,.1f}")
    print(f"\nObservado: hidro {obs[0]:,.0f} -> {obs[1]:,.0f} | termica {obs[2]:,.0f} -> {obs[3]:,.0f}")
    print(f"           CMO {D['cmo'][T1]} -> {D['cmo'][T2]}   PLD {D['pld'][T1]} -> {D['pld'][T2]}")
