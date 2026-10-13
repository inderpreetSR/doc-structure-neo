"use strict";
const $=(id)=>document.getElementById(id);
const esc=(v)=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let db,roleId="api_platform",sysId="los",incidentId="cors",lastReport="",lastDiagram="";
const role=id=>db.roles.find(x=>x.id===id);
const system=id=>db.systems.find(x=>x.id===id);
const group=id=>db.groups.find(x=>x.id===id);
const smallRole=id=>esc(role(id)?.name||id);
const chips=(ids,handler)=>ids.map(id=>'<button type="button" class="chip" data-'+handler+'="'+esc(id)+'">'+(handler==="role"?smallRole(id):esc(system(id)?.name||id))+'</button>').join("")||'<span class="dim">None recorded</span>';
const list=(arr)=>'<ol class="checklist">'+arr.map(x=>'<li>'+esc(x)+'</li>').join("")+'</ol>';
function tab(name){document.querySelectorAll(".tabs button").forEach(b=>{const v=b.dataset.tab===name;b.classList.toggle("active",v);b.setAttribute("aria-selected",String(v));});document.querySelectorAll(".workspace").forEach(e=>e.classList.toggle("active",e.id===name));}
function openRole(id){roleId=id;tab("org");$("role-search").value="";$("role-group").value="";renderRoles();}
function renderRoles(){
const q=$("role-search").value.trim().toLowerCase(),g=$("role-group").value;
const found=db.roles.filter(r=>(!g||r.group===g)&&[r.name,r.responsibility,r.hierarchy,r.id].join(" ").toLowerCase().includes(q));
$("role-list").innerHTML=found.map(r=>'<button type="button" class="list-row '+(r.id===roleId?'selected':'')+'" data-role="'+esc(r.id)+'"><strong>'+esc(r.name)+'</strong><small>'+esc(group(r.group)?.name)+'</small></button>').join("")||'<p class="dim">No matching roles.</p>';
const r=role(roleId);if(!r)return;
const owned=db.systems.filter(s=>s.owner===r.id);
$("role-detail").innerHTML='<span class="badge">'+esc(r.group)+'</span><h2>'+esc(r.name)+'</h2><p class="lead">'+esc(r.responsibility)+'</p><div class="kv"><span>Reference hierarchy</span><strong>'+esc(r.hierarchy)+'</strong></div><div class="kv"><span>Typical reporting / functional oversight</span><strong>'+esc(r.reportsTo)+'</strong></div><div class="kv"><span>Escalation pathway</span><strong>'+esc(r.escalation)+'</strong></div><h3>Collaborating functions</h3><div class="chips">'+chips(r.collaborates,"role")+'</div><h3>Services under reference ownership</h3><div class="chips">'+chips(owned.map(s=>s.id),"system")+'</div><div class="callout"><strong>Authority note:</strong> These are illustrative functional relationships, not actual employees, reporting lines or an approved RACI.</div>';
}
function renderSystems(){
const q=$("system-search").value.trim().toLowerCase();
const found=db.systems.filter(s=>[s.name,s.purpose,...s.aliases].join(" ").toLowerCase().includes(q));
$("system-list").innerHTML=found.map(s=>'<button type="button" class="list-row '+(s.id===sysId?'selected':'')+'" data-system="'+esc(s.id)+'"><strong>'+esc(s.name)+'</strong><small>'+esc(role(s.owner)?.name)+'</small></button>').join("")||'<p class="dim">No matching systems.</p>';
const s=system(sysId);if(!s)return;
$("system-detail").innerHTML='<span class="badge">System / service</span><h2>'+esc(s.name)+'</h2><p>'+esc(s.purpose)+'</p><div class="kv"><span>Technical owner</span><strong>'+smallRole(s.owner)+'</strong></div><div class="kv"><span>Business owner</span><strong>'+esc(s.businessOwner)+'</strong></div><div class="kv"><span>Contracts / dependencies</span><strong>'+esc(s.contracts.join(" · "))+'</strong></div>';
const p=$("system-path");
p.innerHTML='<div class="path-label">UPSTREAM · Produces data or services needed here</div>'+ (s.upstream.length?s.upstream.map(id=>card(id)).join(""):'<p class="dim">No upstream dependency registered.</p>')+'<div class="path-label">SELECTED SERVICE</div>'+card(s.id,true)+'<div class="path-label">DOWNSTREAM · Direct consumers</div>'+(s.downstream.length?s.downstream.map(id=>card(id)).join(""):'<p class="dim">No downstream consumer registered.</p>');
function card(id,active=false){return '<button type="button" class="path-card '+(active?'central':'')+'" data-system="'+esc(id)+'"><strong>'+esc(system(id).name)+'</strong><em>'+smallRole(system(id).owner)+'</em></button>'}
const nodes=[...new Set([...s.upstream,s.id,...s.downstream])],safe=id=>id.replace(/[^A-Za-z0-9_]/g,"_"),label=id=>system(id).name.replace(/["\[\]<>]/g,"");
const edges=[];
for(const id of nodes){for(const to of system(id).downstream)if(nodes.includes(to))edges.push("  "+safe(id)+" --> "+safe(to));}
lastDiagram="flowchart LR\n"+nodes.map(id=>"  "+safe(id)+'["'+label(id)+'"]').join("\n")+"\n"+edges.join("\n");
$("mermaid-output").textContent=lastDiagram;
}
function renderIncidents(){
$("incident-list").innerHTML=db.incidents.map(i=>'<button type="button" class="incident-card '+(i.id===incidentId?'selected':'')+'" data-incident="'+esc(i.id)+'"><strong>'+esc(i.name)+'</strong><small>'+smallRole(i.primary)+'</small></button>').join("");
const i=db.incidents.find(x=>x.id===incidentId);
$("incident-detail").innerHTML='<span class="badge">Investigation playbook</span><h2>'+esc(i.name)+'</h2><p>'+esc(i.symptom)+'</p><div class="kv"><span>Initial technical owner</span><strong>'+smallRole(i.primary)+'</strong></div><div class="kv"><span>Consult</span><div class="chips">'+chips(i.consult,"role")+'</div></div><div class="kv"><span>Impact classification</span><strong>'+esc(i.severity)+'</strong></div><h3>First-line checks</h3>'+list(i.checks)+'<h3>Escalation pathway</h3>'+list(i.escalation)+'<h3>Affected services</h3><div class="chips">'+chips(i.systems,"system")+'</div><div class="callout">'+esc(i.safety)+'</div>';
}
function suggestedType(text){const value=text.toLowerCase();const matches=db.templates.map(t=>({id:t.id,score:t.keywords.reduce((n,k)=>n+(value.includes(k)?(k.includes(" ")?3:1):0),0)})).sort((a,b)=>b.score-a.score);return matches[0].score?matches[0].id:null;}
function renderChange(){
let title=$("change-title").value.trim()||"Untitled proposed change",description=$("change-description").value.trim(),t=db.templates.find(x=>x.id===$("change-type").value);
const systems=t.defaultSystems.map(id=>system(id));
const controls=db.controls.filter(c=>c.applies.includes(t.id));
const line=x=>"- "+x;
const md=["# Change Impact Proposal: "+title,"","Template: "+t.name,"Status: DRAFT — requires review","Source: Enterprise Tech Operating Atlas reference rules","", "## Description",description||"(No description entered — complete before change approval.)","","## Impacted services",...systems.map(s=>line(s.name+" | Tech: "+role(s.owner).name+" | Business: "+s.businessOwner)),"","## Proposed RACI","| Activity | R | A | C | I |","|---|---|---|---|---|",...t.raci.map(r=>"| "+r.task+" | "+smallRole(r.r)+" | "+smallRole(r.a)+" | "+r.c.map(smallRole).join(", ")+" | "+r.i.map(smallRole).join(", ")+" |"),"","## Validation checklist",...t.checks.map(line),"","## Controls for review",...controls.map(c=>line(c.name+" — "+c.description)),"","## Governance disclaimer","Ownership, approval, severity and service inventory are proposals only; validate with actual system and process owners before implementation."];
lastReport=md.join("\n");
$("change-result").innerHTML='<div class="result"><span class="badge">Draft · Human review required</span><h3>Impacted reference services ('+systems.length+')</h3><div class="chips">'+chips(systems.map(s=>s.id),"system")+'</div><h3>Proposed RACI</h3><div class="table-wrap"><table><thead><tr><th>Activity</th><th>R</th><th>A</th><th>C</th><th>I</th></tr></thead><tbody>'+t.raci.map(r=>'<tr><td>'+esc(r.task)+'</td><td>'+smallRole(r.r)+'</td><td>'+smallRole(r.a)+'</td><td>'+r.c.map(smallRole).join(", ")+'</td><td>'+r.i.map(smallRole).join(", ")+'</td></tr>').join("")+'</tbody></table></div><h3>Validation checklist</h3>'+list(t.checks)+'<h3>Control reviews</h3>'+list(controls.map(c=>c.name+": "+c.description))+'<div class="callout"><strong>Review required:</strong> Validate technical service owner, business owner, release approver, change authority, privacy and security impact. Do not treat this reference output as approved.</div><div class="actions"><button id="copy-report" class="secondary">Copy Markdown</button><button id="download-report" class="primary">Download .md</button></div></div>';
}
function download(name,text){const blob=new Blob([text],{type:"text/markdown;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);}
function safeFile(s){return(s.toLowerCase().replace(/[^a-z0-9_-]+/g,"-").replace(/^-|-$/g,"").slice(0,55)||"change")+"-impact.md";}
async function copy(text){try{await navigator.clipboard.writeText(text);alert("Copied.");}catch{alert("Clipboard unavailable here. Select and copy from the code/report view.");}}
function init(){
$("stats").innerHTML=[[db.roles.length,"Functional roles"],[db.systems.length,"Connected services"],[db.incidents.length,"Incident playbooks"],[db.templates.length,"Change templates"]].map(([n,label])=>'<span class="stat"><b>'+n+'</b><small>'+label+'</small></span>').join("");
$("role-group").innerHTML+=[...db.groups].map(g=>'<option value="'+esc(g.id)+'">'+esc(g.name)+'</option>').join("");
$("change-type").innerHTML=db.templates.map(t=>'<option value="'+esc(t.id)+'">'+esc(t.name)+'</option>').join("");
renderRoles();renderSystems();renderIncidents();
document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;if(b.dataset.tab){tab(b.dataset.tab);return;}if(b.dataset.role){openRole(b.dataset.role);return;}if(b.dataset.system){sysId=b.dataset.system;tab("dependency");$("system-search").value="";renderSystems();return;}if(b.dataset.incident){incidentId=b.dataset.incident;renderIncidents();return;}if(b.id==="detect-template"){const guess=suggestedType($("change-title").value+" "+$("change-description").value);if(guess)$("change-type").value=guess;else alert("No strong keyword match. Select a template manually.");}if(b.id==="generate-change")renderChange();if(b.id==="copy-mermaid")copy(lastDiagram);if(b.id==="copy-report"&&lastReport)copy(lastReport);if(b.id==="download-report"&&lastReport)download(safeFile($("change-title").value),lastReport);});
$("role-search").addEventListener("input",renderRoles);$("role-group").addEventListener("change",renderRoles);$("system-search").addEventListener("input",renderSystems);
const hash=location.hash.replace("#","");if(["org","dependency","incident","change"].includes(hash))tab(hash);
$("loading").hidden=true;
}
fetch("data/atlas.json").then(r=>{if(!r.ok)throw Error("HTTP "+r.status);return r.json()}).then(data=>{db=data;init()}).catch(e=>{$("loading").textContent="Atlas data could not be loaded ("+e.message+"). Serve the repository with a local HTTP server instead of opening index.html as a file.";});
