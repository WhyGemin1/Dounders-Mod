from reproduction_021109 import birth_with_parental_investment
class Book:
 def __init__(self):self.energy={'animal:p':.01,'animal:c':.025}
 def move(self,energy):
  for src,dst,n in energy:self.energy[src]-=n;self.energy[dst]+=n
class Parent:
 id='p';species='field_mouse';habitat='grassland';age=90;alive=True
class Bridge:
 def __init__(self):self.book=Book()
 def _new(self,*args,**kw):return type('Child',(),{'id':'c','energy':.025})()
def test_finite_parental_investment():
 b=Bridge();p=Parent();before=sum(b.book.energy.values());child=birth_with_parental_investment(b,p)
 assert child and abs(sum(b.book.energy.values())-before)<1e-12
 assert abs(b.book.energy['animal:p']-.007)<1e-12
 assert abs(child.energy-.028)<1e-12
def test_insufficient_parent_energy():
 b=Bridge();b.book.energy['animal:p']=.003;assert birth_with_parental_investment(b,Parent()) is None
