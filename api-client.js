(function(){
'use strict';
var BASE='/api/v1';
var TOKEN_KEY='t4f_v13_api_token';
var syncTimer=null,syncInFlight=false,pendingState=null;
function token(){return sessionStorage.getItem(TOKEN_KEY)||'';}
function setToken(v){if(v)sessionStorage.setItem(TOKEN_KEY,v);else sessionStorage.removeItem(TOKEN_KEY);}
async function request(path,options){
  options=options||{};
  var headers=Object.assign({'Content-Type':'application/json'},options.headers||{});
  if(token())headers.Authorization='Bearer '+token();
  var r=await fetch(BASE+path,Object.assign({},options,{headers:headers}));
  var ct=r.headers.get('content-type')||'';
  var body=ct.indexOf('application/json')>=0?await r.json():await r.text();
  if(!r.ok){
    var msg='Request failed: '+r.status;
    if(body){
      if(typeof body.detail==='string')msg=body.detail;
      else if(Array.isArray(body.detail)&&body.detail.length>0){
        msg=body.detail.map(function(d){return (d&&d.msg)||JSON.stringify(d);}).join(', ');
      }
      else if(body.error)msg=body.error;
      else if(typeof body==='object')msg=JSON.stringify(body);
    }
    var e=new Error(msg);
    e.status=r.status;
    e.body=body;
    throw e;
  }
  return body;
}
async function login(organization_id,email,password){var r=await request('/auth/login',{method:'POST',body:JSON.stringify({organization_id:organization_id,email:email,password:password})});setToken(r.token);return r;}
async function me(){return request('/auth/me');}
async function logout(){try{await request('/auth/logout',{method:'POST',body:'{}'});}catch(e){}setToken('');}
async function changePassword(current_password,new_password){return request('/auth/change-password',{method:'POST',body:JSON.stringify({current_password:current_password||'',new_password:new_password})});}
async function getState(){return request('/workspace/state');}
async function putState(state){return request('/workspace/state',{method:'PUT',body:JSON.stringify({state:state})});}
function scheduleStateSync(state){if(!token())return;pendingState=state;clearTimeout(syncTimer);syncTimer=setTimeout(flushStateSync,700);}
async function flushStateSync(){if(syncInFlight||!pendingState||!token())return;syncInFlight=true;var snapshot=pendingState;pendingState=null;try{await putState(snapshot);window.dispatchEvent(new CustomEvent('t4f-backend-sync',{detail:{ok:true}}));}catch(e){pendingState=snapshot;window.dispatchEvent(new CustomEvent('t4f-backend-sync',{detail:{ok:false,error:e.message}}));}finally{syncInFlight=false;if(pendingState)syncTimer=setTimeout(flushStateSync,1200);}}
async function health(){try{return await request('/system/health');}catch(e){return {ok:false,error:e.message};}}
window.T4FBackend={BASE:BASE,token:token,setToken:setToken,login:login,me:me,logout:logout,changePassword:changePassword,getState:getState,putState:putState,scheduleStateSync:scheduleStateSync,flushStateSync:flushStateSync,health:health,request:request};
})();
