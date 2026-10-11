/* One node per system; all declared directed transfers remain visible. */
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render(host, edges) {
    if (!edges.length) {host.textContent='No declared transfers for this data object.';return;}
    host._lineageEdges = edges;
    if (!host._lineageObserver) {
      host._lineageWidth = host.clientWidth;
      host._lineageObserver = new ResizeObserver(() => {
        const width = host.clientWidth;
        if (width > 0 && width !== host._lineageWidth) {
          host._lineageWidth = width;
          render(host, host._lineageEdges);
        }
      });
      host._lineageObserver.observe(host);
    }
    const nodes = new Map();
    edges.forEach(e => {
      for (const side of ['source','target']) {
        const id=e[`${side}_system_id`];
        if (!nodes.has(id)) nodes.set(id,{id,name:e[`${side}_system_name`],rank:0});
      }
    });
    // Breadth-first distances from sources; cycles use a stable seed and retain every edge.
    const incoming = new Set(edges.map(e=>e.target_system_id));
    const roots=[...nodes.values()].filter(n=>!incoming.has(n.id));
    const visited=new Set(), queue=roots.length ? roots : [nodes.values().next().value];
    queue.forEach(n=>visited.add(n.id));
    while(queue.length) {
      const n=queue.shift();
      edges.filter(e=>e.source_system_id===n.id).forEach(e=>{
        const target=nodes.get(e.target_system_id);
        if(!visited.has(target.id)){target.rank=n.rank+1;visited.add(target.id);queue.push(target);}
      });
      if(!queue.length && visited.size<nodes.size){const next=[...nodes.values()].find(n=>!visited.has(n.id));visited.add(next.id);queue.push(next);}
    }
    const mobile=host.clientWidth<650, ranks=d3.group([...nodes.values()],n=>n.rank);
    const maxRank=d3.max([...nodes.values()],n=>n.rank), maxRows=d3.max([...ranks.values()],r=>r.length);
    const step=mobile?300:410, cross=mobile?280:230, nw=mobile?240:220, nh=100;
    ranks.forEach(list=>list.sort((a,b)=>a.name.localeCompare(b.name)).forEach((n,i)=>{n.x=mobile?30+i*cross:30+n.rank*step;n.y=mobile?30+n.rank*step:40+i*cross;}));
    const width=mobile?60+maxRows*cross:60+maxRank*step+nw;
    const height=mobile?60+maxRank*step+nh:100+(maxRows-1)*cross+nh;
    host.innerHTML='<div class="lineage-graph-scroll"></div>';
    const svg=d3.select(host.firstChild).append('svg').attr('width',width).attr('height',height).attr('role','img').attr('aria-label','Connected system-level data lineage');
    svg.append('defs').append('marker').attr('id','lineage-arrow').attr('viewBox','0 0 10 10').attr('refX',9).attr('refY',5).attr('markerWidth',8).attr('markerHeight',8).attr('orient','auto').append('path').attr('d','M0,0 L10,5 L0,10 Z').attr('fill','#a5b4fc');
    edges.forEach(e=>{
      const s=nodes.get(e.source_system_id),t=nodes.get(e.target_system_id);
      const forward=t.rank>s.rank;
      let path,lx,ly;
      if(mobile){const x=s.x+nw/2,y=s.y+nh,tx=t.x+nw/2,ty=t.y;const mid=(y+ty)/2;path=`M${x},${y} C${x},${mid} ${tx},${mid} ${tx},${ty}`;lx=(x+tx)/2-110;ly=mid-65;}
      else {const x=s.x+nw,y=s.y+nh/2,tx=t.x,ty=t.y+nh/2;const mid=forward?(x+tx)/2:Math.max(x,tx+nw)+80;path=`M${x},${y} C${mid},${y} ${mid},${ty} ${tx},${ty}`;lx=forward?(x+tx)/2-100:mid-100;ly=(y+ty)/2-78;}
      svg.append('path').attr('class','lineage-edge').attr('d',path).attr('marker-end','url(#lineage-arrow)');
      svg.append('foreignObject').attr('class','lineage-edge-label').attr('x',lx).attr('y',ly).attr('width',mobile?220:200).attr('height',155).append('xhtml:div').attr('class','lineage-edge-channels').html([...e.channels.values()].map(c=>`<div><strong>${esc(c.name)}</strong><small>${esc(c.protocol || 'Protocol unspecified')}</small></div>`).join(''));
    });
    [...nodes.values()].forEach(n=>{
      const sends=edges.some(e=>e.source_system_id===n.id),receives=edges.some(e=>e.target_system_id===n.id);
      svg.append('foreignObject').attr('class','lineage-node').attr('data-system-id',n.id).attr('x',n.x).attr('y',n.y).attr('width',nw).attr('height',nh).append('xhtml:div').attr('class','lineage-node-card').html(`<small>${sends&&receives?'Receives & sends':sends?'Sends data':'Receives data'}</small><strong>${esc(n.name)}</strong>`);
    });
  }
  window.TectonLineage={render};
})();
