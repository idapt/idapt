"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[908],{1601:(e,t,a)=>{a.d(t,{tF:()=>I,XU:()=>A,YP:()=>c,s_:()=>f,fw:()=>k,Lz:()=>g,cX:()=>N,Dz:()=>v,eE:()=>o,v9:()=>y,bJ:()=>m,F1:()=>b,xA:()=>_,hV:()=>d,SY:()=>x,Bo:()=>w,xz:()=>h,U5:()=>z,go:()=>U,kN:()=>T,cn:()=>j,Sc:()=>s,UW:()=>n,mc:()=>C,w2:()=>i,IV:()=>S,kC:()=>E,HT:()=>u,vB:()=>p});var r=a(7264);let l=(0,r.UU)((0,r.Z3)()),n=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({...r.wn,url:"/api/auth/token",...e,headers:{"Content-Type":"application/x-www-form-urlencoded",...null==e?void 0:e.headers}})},i=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({url:"/api/auth/register",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},o=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/settings/{identifier}",...e})},s=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/settings/{identifier}",...e})},u=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).patch({security:[{scheme:"bearer",type:"http"}],url:"/api/settings/{identifier}",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},c=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({security:[{scheme:"bearer",type:"http"}],url:"/api/settings/{identifier}",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},d=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/settings",...e})},p=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/upload-file",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},v=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/{encoded_original_path}",...e})},h=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/folder/{encoded_original_path}",...e})},y=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/file/{encoded_original_path}/download",...e})},m=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/folder/{encoded_original_path}/download",...e})},g=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/file-manager/processed-data/{encoded_original_path}",...e})},b=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/chats",...e})},f=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/chats/{chat_uuid}",...e})},x=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}/chats/{chat_uuid}",...e})},_=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources",...e})},k=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}",...e})},w=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}",...e})},S=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).patch({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},I=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({security:[{scheme:"bearer",type:"http"}],url:"/api/datasources/{datasource_name}",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},C=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({security:[{scheme:"bearer",type:"http"}],url:"/api/processing",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},T=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/processing/status",...e})},j=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/stacks/steps",...e})},U=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/stacks/stacks",...e})},A=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).post({security:[{scheme:"bearer",type:"http"}],url:"/api/stacks/stacks",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},N=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).delete({security:[{scheme:"bearer",type:"http"}],url:"/api/stacks/stacks/{stack_identifier}",...e})},E=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).put({security:[{scheme:"bearer",type:"http"}],url:"/api/stacks/stacks/{stack_identifier}",...e,headers:{"Content-Type":"application/json",...null==e?void 0:e.headers}})},z=e=>{var t;return(null!==(t=null==e?void 0:e.client)&&void 0!==t?t:l).get({security:[{scheme:"bearer",type:"http"}],url:"/api/ollama-status",...e})}},7908:(e,t,a)=>{a.d(t,{O:()=>c,A:()=>d});var r=a(5155),l=a(2115),n=a(1601),i=a(2558);async function o(e){let t=new TextEncoder().encode(e);return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",t))).map(e=>e.toString(16).padStart(2,"0")).join("")}var s=a(6046);let u=(0,l.createContext)(null);function c(e){let{children:t}=e,[a,c]=(0,l.useState)(!0),[d,p]=(0,l.useState)(null),[v,h]=(0,l.useState)(null),[y,m]=(0,l.useState)(null),g=(0,s.useRouter)();(0,l.useEffect)(()=>{(()=>{let e=localStorage.getItem("authToken");e&&p(e);let t=localStorage.getItem("userUuid");t&&h(t);let a=localStorage.getItem("email");a&&m(a),c(!1)})()},[]);let b=async(e,t)=>{let a=await o(e),r=await o(t),l=await (0,n.UW)({body:{username:a,password:r,grant_type:"password"}});if(l.data){localStorage.setItem("authToken",l.data.access_token),p(l.data.access_token),localStorage.setItem("email",e),m(e);let t=(0,i.$n)(l.data.access_token);localStorage.setItem("userUuid",t.sub),h(t.sub),g.push("/app/chat")}},f=async(e,t)=>{let a=await o(e),r=await o(t),l=await (0,n.w2)({body:{user_uuid:a,hashed_password:r}});if(l.data){localStorage.setItem("authToken",l.data.access_token),p(l.data.access_token),localStorage.setItem("email",e),m(e);let t=(0,i.$n)(l.data.access_token);localStorage.setItem("userUuid",t.sub),h(t.sub),g.push("/app/chat")}};return a?(0,r.jsx)("div",{className:"flex justify-center items-center h-screen",children:(0,r.jsx)("div",{className:"animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900 dark:border-white"})}):(0,r.jsx)(u.Provider,{value:{token:d,login:b,register:f,logout:()=>{localStorage.removeItem("authToken"),localStorage.removeItem("userUuid"),localStorage.removeItem("email"),p(null)},isAuthenticated:!!d,userUuid:v,email:y},children:t})}let d=()=>(0,l.useContext)(u)},2558:(e,t,a)=>{a.d(t,{$n:()=>n,b2:()=>i,lk:()=>l,y8:()=>o});var r=a(5714).Buffer;function l(){return"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,e=>{let t=16*Math.random()|0;return("x"===e?t:3&t|8).toString(16)})}function n(e){return JSON.parse(r.from(e.split(".")[1],"base64").toString())}function i(e){return e.reduce((e,t)=>{let a="";return"string"==typeof t.content&&(a=t.content),e.push({id:t.uuid,role:t.role,content:a,toolInvocations:[]}),e},[])}function o(e){return e.map(e=>{if("assistant"!==e.role||!e.toolInvocations)return e;let t=[];for(let a of e.toolInvocations)"result"===a.state&&t.push(a.toolCallId);let a=e.toolInvocations.filter(e=>"result"===e.state||t.includes(e.toolCallId));return{...e,toolInvocations:a}}).filter(e=>e.content.length>0||e.toolInvocations&&e.toolInvocations.length>0)}}}]);