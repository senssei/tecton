/* Explicit data-flow diagrams. No nodes or flows are inferred from system links. */
(() => {
  const escape = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render(host,state) {
    const diagrams=state.dataFlowDiagrams || [];
    if(!diagrams.length) {
      host.innerHTML='<p class="empty-state"><strong>No data flow diagram defined</strong>Define processes, data stores, external entities and named flows in the catalog. System connections are shown separately below.</p>';
      return;
    }
    const selected=host.dataset.selected || diagrams[0].id;
    host.innerHTML=`<label>Diagram <select aria-label="Data flow diagram">${diagrams.map(d=>`<option value="${escape(d.id)}">${escape(d.name)}</option>`).join('')}</select></label><p data-role="description"></p><div class="dfd-canvas"></div><p>Rounded boxes: processes · Open-ended stores: stored data · Rectangles: external entities · Arrows: named data flows</p><details><summary>Flow definitions</summary><div class="dfd-flow-list"></div></details>`;
    const control=host.querySelector('select');control.value=diagrams.some(d=>d.id===selected)?selected:diagrams[0].id;
    function draw() {
      const diagram=diagrams.find(d=>d.id===control.value);host.dataset.selected=diagram.id;
      host.querySelector('[data-role=description]').textContent=diagram.description || diagram.name;
      const nodes=diagram.nodes.map(n=>({...n})).sort((a,b)=>a.id.localeCompare(b.id));
      const byId=new Map(nodes.map(n=>[n.id,n]));
      const flows=diagram.flows.filter(f=>byId.has(f.source_id)&&byId.has(f.target_id));
      const processes=nodes.filter(n=>n.kind==='process');
      const order=[], seen=new Set(), queue=flows.length?[flows[0].source_id]:[];
      while(queue.length) {
        const id=queue.shift();if(seen.has(id))continue;seen.add(id);order.push(id);
        flows.filter(f=>f.source_id===id).forEach(f=>queue.push(f.target_id));
      }
      nodes.forEach(n=>{if(!seen.has(n.id))order.push(n.id);});
      nodes.forEach(n=>{const angle=-Math.PI/2+order.indexOf(n.id)*2*Math.PI/nodes.length;n.x=Math.cos(angle)*400;n.y=Math.sin(angle)*400;});
      const simulation=d3.forceSimulation(nodes).randomSource(d3.randomLcg(.614))
        .force('link',d3.forceLink(flows.map(f=>({source:f.source_id,target:f.target_id}))).id(n=>n.id).distance(420))
        .force('charge',d3.forceManyBody().strength(-5000))
        .force('collide',d3.forceCollide(135).iterations(4))
        .force('x',d3.forceX(0).strength(.01))
        .force('y',d3.forceY(0).strength(.015)).stop();
      simulation.tick(500);
      const minX=d3.min(nodes,n=>n.x)-170,maxX=d3.max(nodes,n=>n.x)+170,minY=d3.min(nodes,n=>n.y)-100,maxY=d3.max(nodes,n=>n.y)+100;
      const canvas=host.querySelector('.dfd-canvas');canvas.replaceChildren();
      if(!nodes.length){canvas.textContent='This diagram has no defined nodes.';return;}
      const svg=d3.select(canvas).append('svg').attr('viewBox',`${minX} ${minY} ${maxX-minX} ${maxY-minY}`).attr('role','img').attr('aria-label',diagram.name).style('min-width','760px');
      svg.append('defs').append('marker').attr('id','dfd-arrow').attr('viewBox','0 -5 10 10').attr('refX',9).attr('markerWidth',8).attr('markerHeight',8).attr('orient','auto').append('path').attr('d','M0,-5L10,0L0,5').attr('fill','#94a3b8');
      flows.forEach((flow,index)=>{
        const source=byId.get(flow.source_id),target=byId.get(flow.target_id);
        const dx=target.x-source.x,dy=target.y-source.y,len=Math.hypot(dx,dy)||1;
        const trim=n=>Math.min(105/Math.max(.001,Math.abs(dx/len)),45/Math.max(.001,Math.abs(dy/len)));
        const start=trim(source),end=trim(target)+8;
        const x1=source.x+dx/len*start,y1=source.y+dy/len*start,x2=target.x-dx/len*end,y2=target.y-dy/len*end;
        const siblings=flows.filter(f=>(f.source_id===source.id&&f.target_id===target.id)||(f.source_id===target.id&&f.target_id===source.id));
        const offset=(siblings.indexOf(flow)-(siblings.length-1)/2)*100*(source.id<target.id?1:-1);
        const cx=(x1+x2)/2-dy/len*offset,cy=(y1+y2)/2+dx/len*offset;
        svg.append('path').attr('d',`M${x1},${y1} Q${cx},${cy} ${x2},${y2}`).attr('fill','none').attr('stroke','#94a3b8').attr('stroke-width',2).attr('marker-end','url(#dfd-arrow)');
        const x=(x1+2*cx+x2)/4,y=(y1+2*cy+y2)/4;
        const label=svg.append('g').attr('transform',`translate(${x},${y})`);
        label.append('rect').attr('x',-110).attr('y',-14).attr('width',220).attr('height',30).attr('rx',4).attr('fill','#020617');
        label.append('text').attr('text-anchor','middle').attr('dominant-baseline','central').attr('fill','#e2e8f0').attr('font-size',16).text(`${index+1}. ${flow.name.length>24?flow.name.slice(0,23)+'…':flow.name}`).append('title').text(flow.name);
      });
      const drawNodes=svg.selectAll('.dfd-node').data(nodes).join('g').attr('class','dfd-node').attr('transform',n=>`translate(${n.x},${n.y})`);
      drawNodes.each(function(node){
        const group=d3.select(this),color=node.kind==='process'?'#a5b4fc':node.kind==='data_store'?'#67e8f9':'#cbd5e1';
        if(node.kind==='data_store') {
          group.append('rect').attr('x',-105).attr('y',-45).attr('width',210).attr('height',90).attr('fill','#0f172a');
          group.append('path').attr('d','M105,-45H-105V45H105 M-75,-45V45').attr('fill','none').attr('stroke',color).attr('stroke-width',2);
        } else group.append('rect').attr('x',-105).attr('y',-45).attr('width',210).attr('height',90).attr('rx',node.kind==='process'?15:0).attr('fill','#0f172a').attr('stroke',color).attr('stroke-width',2);
        group.append('title').text(`${node.kind}: ${node.name}${node.description?' — '+node.description:''}`);
        group.append('text').attr('text-anchor','middle').attr('y',-25).attr('fill',color).attr('font-size',12).text(node.kind==='process'?`Process ${processes.indexOf(node)+1}`:node.kind==='data_store'?'Data store':'External entity');
        const words=node.name.split(/\s+/),lines=[''];
        words.forEach(word=>{if((lines[lines.length-1]+' '+word).length>21)lines.push(word);else lines[lines.length-1]+=(lines[lines.length-1]?' ':'')+word;});
        const text=group.append('text').attr('text-anchor','middle').attr('fill','#f8fafc').attr('font-size',17);
        lines.slice(0,3).forEach((line,i)=>text.append('tspan').attr('x',node.kind==='data_store'?10:0).attr('y',i*18-2).text(line));
      });
      const names=new Map(state.dataObjects.map(d=>[d.id,d.name]));
      host.querySelector('.dfd-flow-list').innerHTML=flows.map((f,i)=>`<article><strong>${i+1}. ${escape(f.name)}</strong><p>${escape(byId.get(f.source_id).name)} → ${escape(byId.get(f.target_id).name)}</p><p>Data: ${f.data_objects.map(id=>escape(names.get(id)||id)).join(', ')}</p>${f.description?`<p>${escape(f.description)}</p>`:''}</article>`).join('') || '<p>No data flows defined.</p>';
    }
    control.addEventListener('change',draw);draw();
  }
  window.TectonDFD={render};
})();
