(this.webpackJsonp28fess=this.webpackJsonp28fess||[]).push([[0],{119:function(e,t,n){},120:function(e,t,n){},151:function(e,t){},170:function(e,t,n){"use strict";n.r(t);var a=n(0),r=n(12),c=n.n(r),i=(n(119),n(120),n(109)),o=n(16),s=n(209),l=n(110),j=n(69),d=n(8),u=n(203),b=n(173),h=n(207),p=n(211),x=n.p+"static/media/28.f06538be.png",O=n(75),f=n.n(O),m=n(32),g=n(4),y=function(e){var t=Object(m.useSpring)({from:{opacity:0},to:{opacity:1},config:{duration:500,delay:500}}),n={color:"#FFFFF",fontFamily:"'Quicksand', sans-serif",fontSize:"1em",lineHeight:1.625,fontWeight:400};return Object(g.jsx)(m.animated.div,{className:"inner",style:t,children:Object(g.jsxs)(u.a,{container:!0,spacing:1,alignItems:"center",children:[Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)("img",{className:"logo",src:x,alt:"SMAN 28 Jakarta"})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(b.a,{variant:"h3",component:"h3",className:"title",fontWeight:"fontWeightBold",children:"@28FESS"})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsxs)(b.a,{variant:"body1",component:"p",style:n,children:["28FESS adalah akun menfess otomatis khusus untuk",Object(g.jsx)("span",{className:"bold",children:" siswa 28"}),". 28FESS",Object(g.jsx)("em",{className:"color-red",children:" bukan"})," official account dan tidak terkait dengan instansi manapun."]})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(h.a,{href:"https://liff.line.me/1645278921-kWRPP32q?accountId=235fcixk&openerPlatform=native&openerKey=chatMessage",style:Object(d.a)(Object(d.a)({},n),{},{color:"#1bf551",fontWeight:"bold"}),target:"_blank",children:"Add Line Official Account 28FESS BOT"})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)("hr",{})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsxs)(p.a,{variant:"contained",color:"default",size:"large",onClick:function(){return e.history.push("/tweet")},children:[Object(g.jsx)(f.a,{style:{color:"#1DA1F2"}})," Tweet"]})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsxs)(p.a,{variant:"contained",color:"primary",size:"large",onClick:function(){return e.history.push("/reply")},children:[Object(g.jsx)(f.a,{style:{color:"#1DA1F2"}})," Reply Tweet"]})})]})})},w=n(19),k=n.n(w),v=n(30),S=n(14),F=n(210),C=n(208),T=n(6),N=n(68),P=n.n(N),I=Object(C.a)({multilineColor:{color:"white"}}),W=Object(T.a)({root:{"& label.Mui-focused":{color:"#1DA1F2",fontSize:"1rem"},"& label":{color:"#1DA1F2"},"& .MuiInput-underline:after":{borderBottomColor:"red"},"& .MuiOutlinedInput-root":{"& fieldset":{borderColor:"#1DA1F2"},"&:hover fieldset":{borderColor:"grey"},"&.Mui-focused fieldset":{borderColor:"white"}}}});var E=function(e){var t=Object(a.useState)(""),n=Object(S.a)(t,2),r=n[0],c=n[1],i=Object(a.useState)(""),o=Object(S.a)(i,2),s=o[0],l=o[1],j=Object(a.useState)(""),d=Object(S.a)(j,2),h=d[0],x=d[1],O=I(),f=Object(m.useSpring)({from:{opacity:0},to:{opacity:1},config:{duration:500,delay:500}}),y=Object(a.useState)(F.a),w=Object(S.a)(y,2),C=w[0],T=w[1];Object(a.useEffect)((function(){T(W(F.a))}),[]);var N=function(){var e=Object(v.a)(k.a.mark((function e(t){var n,a;return k.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t.preventDefault(),s.toLowerCase().includes("dupan!")){e.next=5;break}c("Tweet wajib berisi keyword 'dupan!'"),e.next=17;break;case 5:return e.next=7,fetch("https://dualapan.herokuapp.com/api/tweet",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:s})});case 7:if(!(n=e.sent).ok){e.next=16;break}return""!==r&&c(""),e.next=12,n.json();case 12:a=e.sent,x(a.link),e.next=17;break;case 16:c("Failed to upload tweet.");case 17:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}();return Object(g.jsx)(m.animated.div,{className:"inner",style:f,children:Object(g.jsxs)("form",{noValidate:!0,autoComplete:"off",onSubmit:N,children:[""!==h&&window.location.replace(h),Object(g.jsxs)(u.a,{container:!0,spacing:1,children:[Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(b.a,{variant:"h3",component:"h3",className:"title",fontWeight:"fontWeightBold",children:"Tweet @28FESS"})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(C,{multiline:!0,rows:4,variant:"outlined",style:{width:"100%",color:"white"},value:s,onChange:function(e){return l(e.target.value)},error:""!==r,label:"Tweet Text",helperText:r,InputProps:{className:O.multilineColor}})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsxs)(p.a,{type:"submit",variant:"contained",color:"primary",style:{width:"100%"},children:[Object(g.jsx)(P.a,{style:{paddingRight:"20px"}}),"Post Tweet"]})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(p.a,{variant:"contained",color:"secondary",onClick:function(){return e.history.push("/")},children:"Home"})})]})]})})},L=n(108),A=n.n(L),D=Object(C.a)({cssLabel:{color:"white"},root:{borderColor:"white",color:"white"}}),R=function(e){var t=Object(a.useState)(""),n=Object(S.a)(t,2),r=n[0],c=n[1],i=Object(a.useState)(""),o=Object(S.a)(i,2),s=o[0],l=o[1],j=Object(a.useState)(""),d=Object(S.a)(j,2),h=d[0],x=d[1],O=Object(a.useState)(""),f=Object(S.a)(O,2),y=f[0],w=f[1],C=D(),T=Object(m.useSpring)({from:{opacity:0},to:{opacity:1},config:{duration:500,delay:500}}),N=function(){var e=Object(v.a)(k.a.mark((function e(t){var n,a;return k.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return t.preventDefault(),console.log(s),e.next=4,fetch("https://dualapan.herokuapp.com/api/get-tweet-html?link=".concat(s));case 4:if(!(n=e.sent).ok){e.next=13;break}return e.next=8,n.json();case 8:a=e.sent,c(a.html),w(""),e.next=14;break;case 13:w("Error get tweet");case 14:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),I=function(){var e=Object(v.a)(k.a.mark((function e(t){var n,a;return k.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t.preventDefault(),!(h.length<5)){e.next=5;break}w("Tweet terlalu pendek"),e.next=17;break;case 5:return e.next=7,fetch("https://dualapan.herokuapp.com/api/tweet",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:h,reply:!0,reply_link:s})});case 7:if(!(n=e.sent).ok){e.next=16;break}return""!==y&&w(""),e.next=12,n.json();case 12:a=e.sent,window.location.replace(a.link),e.next=17;break;case 16:w("Failed to upload tweet.");case 17:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}();return Object(g.jsx)(m.animated.div,{className:"inner",style:T,children:Object(g.jsx)("form",{noValidate:!0,autoComplete:"off",onSubmit:""===r?N:I,children:Object(g.jsxs)(u.a,{container:!0,spacing:1,children:[""!==r?Object(g.jsxs)(g.Fragment,{children:[Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:A()(r)}),Object(g.jsx)(u.a,{item:!0,xs:12,children:Object(g.jsx)(F.a,{label:"Reply Tweet",variant:"outlined",error:""!==y,helperText:y,value:h,onChange:function(e){return x(e.target.value)},multiline:!0,rows:3,style:{width:"100%"},InputLabelProps:{classes:{root:C.cssLabel}},InputProps:{classes:{root:C.root,notchedOutline:C.root}}})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsxs)(p.a,{type:"submit",variant:"contained",color:"primary",style:{width:"100%"},children:[Object(g.jsx)(P.a,{style:{paddingRight:"20px"}}),"Send Reply"]})})]}):Object(g.jsxs)(g.Fragment,{children:[Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(b.a,{variant:"h3",component:"h3",className:"title",fontWeight:"fontWeightBold",children:"Reply @28FESS"})}),Object(g.jsx)(u.a,{item:!0,xs:12,children:Object(g.jsx)(F.a,{label:"Tweet Link To Reply",value:s,onChange:function(e){return l(e.target.value)},variant:"outlined",style:{width:"100%"},InputLabelProps:{classes:{root:C.cssLabel}},InputProps:{classes:{root:C.root,notchedOutline:C.root}}})}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(p.a,{type:"submit",variant:"contained",color:"primary",style:{width:"100%"},children:"Check Link"})})]}),Object(g.jsx)(u.a,{item:!0,xs:12,align:"center",children:Object(g.jsx)(p.a,{variant:"contained",color:"secondary",onClick:function(){return e.history.push("/")},children:"Home"})})]})})})};var B=Object(l.a)({typography:{fontFamily:"'Quicksand', sans-serif",h3:{fontWeight:"bold"},palette:{primary:j.a}}}),M=function(){return Object(g.jsx)(s.a,{theme:B,children:Object(g.jsx)(i.a,{children:Object(g.jsxs)(o.c,{children:[Object(g.jsx)(o.a,{exact:!0,path:"/",component:y}),Object(g.jsx)(o.a,{exact:!0,path:"/tweet",component:E}),Object(g.jsx)(o.a,{exact:!0,path:"/reply",component:R})]})})})};c.a.render(Object(g.jsx)("div",{id:"main",children:Object(g.jsx)(M,{})}),document.getElementById("root"))}},[[170,1,2]]]);
//# sourceMappingURL=main.b653453e.chunk.js.map