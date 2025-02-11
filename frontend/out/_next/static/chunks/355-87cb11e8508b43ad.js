"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[355],{434:(e,t,r)=>{r.d(t,{b:()=>u});var n=r(2115),o=r(3360),i=r(5155),l="horizontal",a=["horizontal","vertical"],s=n.forwardRef((e,t)=>{let{decorative:r,orientation:n=l,...s}=e,u=a.includes(n)?n:l;return(0,i.jsx)(o.sG.div,{"data-orientation":u,...r?{role:"none"}:{"aria-orientation":"vertical"===u?u:void 0,role:"separator"},...s,ref:t})});s.displayName="Separator";var u=s},9710:(e,t,r)=>{r.d(t,{Kq:()=>H,UC:()=>F,bL:()=>q,l9:()=>z});var n=r(2115),o=r(3610),i=r(8068),l=r(8166),a=r(3741),s=r(7668),u=r(9895),c=(r(7323),r(7028)),d=r(3360),p=r(2317),f=r(1488),h=r(3543),v=r(5155),[x,g]=(0,l.A)("Tooltip",[u.Bk]),y=(0,u.Bk)(),b="TooltipProvider",w="tooltip.open",[m,C]=x(b),T=e=>{let{__scopeTooltip:t,delayDuration:r=700,skipDelayDuration:o=300,disableHoverableContent:i=!1,children:l}=e,[a,s]=n.useState(!0),u=n.useRef(!1),c=n.useRef(0);return n.useEffect(()=>{let e=c.current;return()=>window.clearTimeout(e)},[]),(0,v.jsx)(m,{scope:t,isOpenDelayed:a,delayDuration:r,onOpen:n.useCallback(()=>{window.clearTimeout(c.current),s(!1)},[]),onClose:n.useCallback(()=>{window.clearTimeout(c.current),c.current=window.setTimeout(()=>s(!0),o)},[o]),isPointerInTransitRef:u,onPointerInTransitChange:n.useCallback(e=>{u.current=e},[]),disableHoverableContent:i,children:l})};T.displayName=b;var E="Tooltip",[k,L]=x(E),R=e=>{let{__scopeTooltip:t,children:r,open:o,defaultOpen:i=!1,onOpenChange:l,disableHoverableContent:a,delayDuration:c}=e,d=C(E,e.__scopeTooltip),p=y(t),[h,x]=n.useState(null),g=(0,s.B)(),b=n.useRef(0),m=null!=a?a:d.disableHoverableContent,T=null!=c?c:d.delayDuration,L=n.useRef(!1),[R=!1,j]=(0,f.i)({prop:o,defaultProp:i,onChange:e=>{e?(d.onOpen(),document.dispatchEvent(new CustomEvent(w))):d.onClose(),null==l||l(e)}}),_=n.useMemo(()=>R?L.current?"delayed-open":"instant-open":"closed",[R]),P=n.useCallback(()=>{window.clearTimeout(b.current),b.current=0,L.current=!1,j(!0)},[j]),M=n.useCallback(()=>{window.clearTimeout(b.current),b.current=0,j(!1)},[j]),N=n.useCallback(()=>{window.clearTimeout(b.current),b.current=window.setTimeout(()=>{L.current=!0,j(!0),b.current=0},T)},[T,j]);return n.useEffect(()=>()=>{b.current&&(window.clearTimeout(b.current),b.current=0)},[]),(0,v.jsx)(u.bL,{...p,children:(0,v.jsx)(k,{scope:t,contentId:g,open:R,stateAttribute:_,trigger:h,onTriggerChange:x,onTriggerEnter:n.useCallback(()=>{d.isOpenDelayed?N():P()},[d.isOpenDelayed,N,P]),onTriggerLeave:n.useCallback(()=>{m?M():(window.clearTimeout(b.current),b.current=0)},[M,m]),onOpen:P,onClose:M,disableHoverableContent:m,children:r})})};R.displayName=E;var j="TooltipTrigger",_=n.forwardRef((e,t)=>{let{__scopeTooltip:r,...l}=e,a=L(j,r),s=C(j,r),c=y(r),p=n.useRef(null),f=(0,i.s)(t,p,a.onTriggerChange),h=n.useRef(!1),x=n.useRef(!1),g=n.useCallback(()=>h.current=!1,[]);return n.useEffect(()=>()=>document.removeEventListener("pointerup",g),[g]),(0,v.jsx)(u.Mz,{asChild:!0,...c,children:(0,v.jsx)(d.sG.button,{"aria-describedby":a.open?a.contentId:void 0,"data-state":a.stateAttribute,...l,ref:f,onPointerMove:(0,o.m)(e.onPointerMove,e=>{"touch"===e.pointerType||x.current||s.isPointerInTransitRef.current||(a.onTriggerEnter(),x.current=!0)}),onPointerLeave:(0,o.m)(e.onPointerLeave,()=>{a.onTriggerLeave(),x.current=!1}),onPointerDown:(0,o.m)(e.onPointerDown,()=>{h.current=!0,document.addEventListener("pointerup",g,{once:!0})}),onFocus:(0,o.m)(e.onFocus,()=>{h.current||a.onOpen()}),onBlur:(0,o.m)(e.onBlur,a.onClose),onClick:(0,o.m)(e.onClick,a.onClose)})})});_.displayName=j;var[P,M]=x("TooltipPortal",{forceMount:void 0}),N="TooltipContent",D=n.forwardRef((e,t)=>{let r=M(N,e.__scopeTooltip),{forceMount:n=r.forceMount,side:o="top",...i}=e,l=L(N,e.__scopeTooltip);return(0,v.jsx)(c.C,{present:n||l.open,children:l.disableHoverableContent?(0,v.jsx)(A,{side:o,...i,ref:t}):(0,v.jsx)(O,{side:o,...i,ref:t})})}),O=n.forwardRef((e,t)=>{let r=L(N,e.__scopeTooltip),o=C(N,e.__scopeTooltip),l=n.useRef(null),a=(0,i.s)(t,l),[s,u]=n.useState(null),{trigger:c,onClose:d}=r,p=l.current,{onPointerInTransitChange:f}=o,h=n.useCallback(()=>{u(null),f(!1)},[f]),x=n.useCallback((e,t)=>{let r=e.currentTarget,n={x:e.clientX,y:e.clientY},o=function(e,t){let r=Math.abs(t.top-e.y),n=Math.abs(t.bottom-e.y),o=Math.abs(t.right-e.x),i=Math.abs(t.left-e.x);switch(Math.min(r,n,o,i)){case i:return"left";case o:return"right";case r:return"top";case n:return"bottom";default:throw Error("unreachable")}}(n,r.getBoundingClientRect());u(function(e){let t=e.slice();return t.sort((e,t)=>e.x<t.x?-1:e.x>t.x?1:e.y<t.y?-1:e.y>t.y?1:0),function(e){if(e.length<=1)return e.slice();let t=[];for(let r=0;r<e.length;r++){let n=e[r];for(;t.length>=2;){let e=t[t.length-1],r=t[t.length-2];if((e.x-r.x)*(n.y-r.y)>=(e.y-r.y)*(n.x-r.x))t.pop();else break}t.push(n)}t.pop();let r=[];for(let t=e.length-1;t>=0;t--){let n=e[t];for(;r.length>=2;){let e=r[r.length-1],t=r[r.length-2];if((e.x-t.x)*(n.y-t.y)>=(e.y-t.y)*(n.x-t.x))r.pop();else break}r.push(n)}return(r.pop(),1===t.length&&1===r.length&&t[0].x===r[0].x&&t[0].y===r[0].y)?t:t.concat(r)}(t)}([...function(e,t){let r=arguments.length>2&&void 0!==arguments[2]?arguments[2]:5,n=[];switch(t){case"top":n.push({x:e.x-r,y:e.y+r},{x:e.x+r,y:e.y+r});break;case"bottom":n.push({x:e.x-r,y:e.y-r},{x:e.x+r,y:e.y-r});break;case"left":n.push({x:e.x+r,y:e.y-r},{x:e.x+r,y:e.y+r});break;case"right":n.push({x:e.x-r,y:e.y-r},{x:e.x-r,y:e.y+r})}return n}(n,o),...function(e){let{top:t,right:r,bottom:n,left:o}=e;return[{x:o,y:t},{x:r,y:t},{x:r,y:n},{x:o,y:n}]}(t.getBoundingClientRect())])),f(!0)},[f]);return n.useEffect(()=>()=>h(),[h]),n.useEffect(()=>{if(c&&p){let e=e=>x(e,p),t=e=>x(e,c);return c.addEventListener("pointerleave",e),p.addEventListener("pointerleave",t),()=>{c.removeEventListener("pointerleave",e),p.removeEventListener("pointerleave",t)}}},[c,p,x,h]),n.useEffect(()=>{if(s){let e=e=>{let t=e.target,r={x:e.clientX,y:e.clientY},n=(null==c?void 0:c.contains(t))||(null==p?void 0:p.contains(t)),o=!function(e,t){let{x:r,y:n}=e,o=!1;for(let e=0,i=t.length-1;e<t.length;i=e++){let l=t[e].x,a=t[e].y,s=t[i].x,u=t[i].y;a>n!=u>n&&r<(s-l)*(n-a)/(u-a)+l&&(o=!o)}return o}(r,s);n?h():o&&(h(),d())};return document.addEventListener("pointermove",e),()=>document.removeEventListener("pointermove",e)}},[c,p,s,d,h]),(0,v.jsx)(A,{...e,ref:a})}),[B,I]=x(E,{isInside:!1}),A=n.forwardRef((e,t)=>{let{__scopeTooltip:r,children:o,"aria-label":i,onEscapeKeyDown:l,onPointerDownOutside:s,...c}=e,d=L(N,r),f=y(r),{onClose:x}=d;return n.useEffect(()=>(document.addEventListener(w,x),()=>document.removeEventListener(w,x)),[x]),n.useEffect(()=>{if(d.trigger){let e=e=>{let t=e.target;(null==t?void 0:t.contains(d.trigger))&&x()};return window.addEventListener("scroll",e,{capture:!0}),()=>window.removeEventListener("scroll",e,{capture:!0})}},[d.trigger,x]),(0,v.jsx)(a.qW,{asChild:!0,disableOutsidePointerEvents:!1,onEscapeKeyDown:l,onPointerDownOutside:s,onFocusOutside:e=>e.preventDefault(),onDismiss:x,children:(0,v.jsxs)(u.UC,{"data-state":d.stateAttribute,...f,...c,ref:t,style:{...c.style,"--radix-tooltip-content-transform-origin":"var(--radix-popper-transform-origin)","--radix-tooltip-content-available-width":"var(--radix-popper-available-width)","--radix-tooltip-content-available-height":"var(--radix-popper-available-height)","--radix-tooltip-trigger-width":"var(--radix-popper-anchor-width)","--radix-tooltip-trigger-height":"var(--radix-popper-anchor-height)"},children:[(0,v.jsx)(p.xV,{children:o}),(0,v.jsx)(B,{scope:r,isInside:!0,children:(0,v.jsx)(h.b,{id:d.contentId,role:"tooltip",children:i||o})})]})})});D.displayName=N;var S="TooltipArrow";n.forwardRef((e,t)=>{let{__scopeTooltip:r,...n}=e,o=y(r);return I(S,r).isInside?null:(0,v.jsx)(u.i3,{...o,...n,ref:t})}).displayName=S;var H=T,q=R,z=_,F=D},3543:(e,t,r)=>{r.d(t,{b:()=>a,s:()=>l});var n=r(2115),o=r(3360),i=r(5155),l=n.forwardRef((e,t)=>(0,i.jsx)(o.sG.span,{...e,ref:t,style:{position:"absolute",border:0,width:1,height:1,padding:0,margin:-1,overflow:"hidden",clip:"rect(0, 0, 0, 0)",whiteSpace:"nowrap",wordWrap:"normal",...e.style}}));l.displayName="VisuallyHidden";var a=l},8535:(e,t,r)=>{r.d(t,{A:()=>n});let n=(0,r(4057).A)("PanelLeft",[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",key:"afitv7"}],["path",{d:"M9 3v18",key:"fh3hqa"}]])}}]);