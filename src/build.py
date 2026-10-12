#!/usr/bin/env python3
"""Сборка варианта: python3 build.py template.html out.html
В шаблоне должны быть две метки: <!--DATA--> (заменится на <script type="application/json" id="data">…</script>)
и <!--MARKED--> (заменится на <script>…marked…</script>)."""
import sys,json,os
D=os.path.dirname(os.path.abspath(__file__))
t=open(sys.argv[1]).read()
data=open(D+'/data.json').read().replace('</','<\\/')
marked=open(D+'/marked.min.js').read()
assert '<!--DATA-->' in t and '<!--MARKED-->' in t
t=t.replace('<!--DATA-->','<script type="application/json" id="data">'+data+'</script>').replace('<!--MARKED-->','<script>'+marked+'</script>')
open(sys.argv[2],'w').write(t); print('ok',len(t))
