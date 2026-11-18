const $ = (s) => document.querySelector(s);
const state = { status: "", tasks: [], users: [], categories: [] };
const esc = (value="") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function api(url, options={}) {
  const response = await fetch(url, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.erro || "Não foi possível concluir a operação.");
  return data;
}
function toast(message) { const el=$("#toast"); el.textContent=message; el.classList.add("show"); setTimeout(()=>el.classList.remove("show"),2600); }
function dateBR(value) { if(!value) return "Sem prazo"; const [y,m,d]=value.split("-"); return `${d}/${m}/${y}`; }
function statusClass(s) { return s === "Concluída" ? "status-done" : s === "Em andamento" ? "status-progress" : "status-pending"; }
async function loadBase() {
  [state.users,state.categories] = await Promise.all([api("/api/users"),api("/api/categories")]);
  const userOptions=state.users.map(u=>`<option value="${u.id_usuario}">${esc(u.nome)}</option>`).join("");
  $("#user").innerHTML=userOptions;
  const catOptions=state.categories.map(c=>`<option value="${c.id_categoria}">${esc(c.nome)}</option>`).join("");
  $("#category").innerHTML='<option value="">Sem categoria</option>'+catOptions;
  $("#category-filter").innerHTML='<option value="">Todas as categorias</option>'+catOptions;
}
async function loadSummary() {
  const s=await api("/api/summary");
  $("#stat-total").textContent=s.total; $("#stat-pending").textContent=s.pendentes;
  $("#stat-progress").textContent=s.andamento; $("#stat-done").textContent=s.concluidas;
}
async function loadTasks() {
  const params=new URLSearchParams(); if(state.status) params.set("status",state.status);
  if($("#category-filter").value) params.set("categoria",$("#category-filter").value);
  if($("#search").value.trim()) params.set("q",$("#search").value.trim());
  state.tasks=await api("/api/tasks?"+params.toString());
  $("#task-count").textContent=`${state.tasks.length} tarefa(s)`;
  const list=$("#task-list");
  if(!state.tasks.length){list.innerHTML='<div class="empty-state"><strong>Nenhuma tarefa encontrada</strong>Cadastre uma nova tarefa ou ajuste os filtros.</div>';return;}
  list.innerHTML=state.tasks.map(t=>`<article class="task-card"><div><h3>${esc(t.titulo)}</h3><p>${esc(t.descricao||"Sem descrição informada")}</p><div class="task-meta"><span class="pill ${statusClass(t.status)}">${esc(t.status)}</span><span class="pill">${esc(t.categoria_nome||"Sem categoria")}</span><span class="pill">Prazo: ${dateBR(t.data_prazo)}</span><span class="pill priority priority-${t.prioridade.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')}">Prioridade ${esc(t.prioridade)}</span><span class="pill">Responsável: ${esc(t.usuario_nome)}</span></div></div><div class="task-actions"><button class="action-btn" data-edit="${t.id_tarefa}" aria-label="Editar tarefa">✎</button><button class="action-btn" data-delete="${t.id_tarefa}" aria-label="Excluir tarefa">⌫</button></div></article>`).join("");
}
async function refresh(){await loadSummary();await loadTasks();}
function openTask(task=null){const f=$("#task-form");f.reset();$("#task-id").value=task?.id_tarefa||"";$("#form-title").textContent=task?"Editar tarefa":"Nova tarefa";
  $("#title").value=task?.titulo||"";$("#description").value=task?.descricao||"";$("#due-date").value=task?.data_prazo||"";
  $("#status").value=task?.status||"Pendente";$("#priority").value=task?.prioridade||"Média";
  $("#user").value=task?.id_usuario||state.users[0]?.id_usuario||"";$("#category").value=task?.id_categoria||"";$("#task-dialog").showModal();}
$("#new-task").addEventListener("click",()=>openTask());
$("#task-form").addEventListener("submit",async e=>{e.preventDefault();const id=$("#task-id").value;const body={titulo:$("#title").value,descricao:$("#description").value,data_prazo:$("#due-date").value,status:$("#status").value,prioridade:$("#priority").value,id_usuario:$("#user").value,id_categoria:$("#category").value};try{await api(id?`/api/tasks/${id}`:"/api/tasks",{method:id?"PUT":"POST",body:JSON.stringify(body)});$("#task-dialog").close();toast(id?"Tarefa atualizada.":"Tarefa cadastrada.");await refresh();}catch(err){toast(err.message);}});
$("#task-list").addEventListener("click",async e=>{const edit=e.target.closest("[data-edit]");const del=e.target.closest("[data-delete]");if(edit){const task=state.tasks.find(t=>t.id_tarefa===Number(edit.dataset.edit));if(task)openTask(task);}if(del){const id=del.dataset.delete;if(confirm("Deseja realmente excluir esta tarefa?")){try{await api(`/api/tasks/${id}`,{method:"DELETE"});toast("Tarefa excluída.");await refresh();}catch(err){toast(err.message);}}}});
$("#manage-categories").addEventListener("click",()=>$("#category-dialog").showModal());
$("#category-form").addEventListener("submit",async e=>{e.preventDefault();try{await api("/api/categories",{method:"POST",body:JSON.stringify({nome:$("#category-name").value,descricao:$("#category-description").value})});$("#category-dialog").close();$("#category-form").reset();await loadBase();toast("Categoria criada.");}catch(err){toast(err.message);}});
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>$("#"+b.dataset.close).close()));
document.querySelectorAll(".nav-item[data-status]").forEach(b=>b.addEventListener("click",()=>{state.status=b.dataset.status;document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));b.classList.add("active");$("#list-title").textContent=state.status;loadTasks();}));
$("#nav-all").addEventListener("click",()=>{state.status="";document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active"));$("#nav-all").classList.add("active");$("#list-title").textContent="Todas as tarefas";loadTasks();});
$("#category-filter").addEventListener("change",loadTasks);let searchTimer;$("#search").addEventListener("input",()=>{clearTimeout(searchTimer);searchTimer=setTimeout(loadTasks,220);});
(async()=>{try{await loadBase();await refresh();}catch(err){toast(err.message);$("#task-list").innerHTML='<div class="empty-state"><strong>Não foi possível carregar os dados</strong>Verifique se o servidor foi iniciado corretamente.</div>';}})();
