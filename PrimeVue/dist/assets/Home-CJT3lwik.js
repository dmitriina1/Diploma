import{B as A,o as c,c as p,m as k,r as M,a as L,_ as F,b as n,d as T,e as V,f as l,w as d,u as a,F as _,g as $,h as q,i as w,t as v,j as K,n as R,k as z}from"./index-CRpKplOa.js";import{s as y}from"./index-CUQrBlLv.js";import{s as B,f as H,a as b}from"./auth-CA8NM3zp.js";import{s as S}from"./index-CIDYvPdb.js";import{N as Q,A as U}from"./AppFooter-H4wsG3kH.js";import{u as W}from"./index-B7nggic0.js";var Z=`
    .p-divider-horizontal {
        display: flex;
        width: 100%;
        position: relative;
        align-items: center;
        margin: dt('divider.horizontal.margin');
        padding: dt('divider.horizontal.padding');
    }

    .p-divider-horizontal:before {
        position: absolute;
        display: block;
        inset-block-start: 50%;
        inset-inline-start: 0;
        width: 100%;
        content: '';
        border-block-start: 1px solid dt('divider.border.color');
    }

    .p-divider-horizontal .p-divider-content {
        padding: dt('divider.horizontal.content.padding');
    }

    .p-divider-vertical {
        min-height: 100%;
        display: flex;
        position: relative;
        justify-content: center;
        margin: dt('divider.vertical.margin');
        padding: dt('divider.vertical.padding');
    }

    .p-divider-vertical:before {
        position: absolute;
        display: block;
        inset-block-start: 0;
        inset-inline-start: 50%;
        height: 100%;
        content: '';
        border-inline-start: 1px solid dt('divider.border.color');
    }

    .p-divider.p-divider-vertical .p-divider-content {
        padding: dt('divider.vertical.content.padding');
    }

    .p-divider-content {
        z-index: 1;
        background: dt('divider.content.background');
        color: dt('divider.content.color');
    }

    .p-divider-solid.p-divider-horizontal:before {
        border-block-start-style: solid;
    }

    .p-divider-solid.p-divider-vertical:before {
        border-inline-start-style: solid;
    }

    .p-divider-dashed.p-divider-horizontal:before {
        border-block-start-style: dashed;
    }

    .p-divider-dashed.p-divider-vertical:before {
        border-inline-start-style: dashed;
    }

    .p-divider-dotted.p-divider-horizontal:before {
        border-block-start-style: dotted;
    }

    .p-divider-dotted.p-divider-vertical:before {
        border-inline-start-style: dotted;
    }

    .p-divider-left:dir(rtl),
    .p-divider-right:dir(rtl) {
        flex-direction: row-reverse;
    }
`,G={root:function(e){var i=e.props;return{justifyContent:i.layout==="horizontal"?i.align==="center"||i.align===null?"center":i.align==="left"?"flex-start":i.align==="right"?"flex-end":null:null,alignItems:i.layout==="vertical"?i.align==="center"||i.align===null?"center":i.align==="top"?"flex-start":i.align==="bottom"?"flex-end":null:null}}},J={root:function(e){var i=e.props;return["p-divider p-component","p-divider-"+i.layout,"p-divider-"+i.type,{"p-divider-left":i.layout==="horizontal"&&(!i.align||i.align==="left")},{"p-divider-center":i.layout==="horizontal"&&i.align==="center"},{"p-divider-right":i.layout==="horizontal"&&i.align==="right"},{"p-divider-top":i.layout==="vertical"&&i.align==="top"},{"p-divider-center":i.layout==="vertical"&&(!i.align||i.align==="center")},{"p-divider-bottom":i.layout==="vertical"&&i.align==="bottom"}]},content:"p-divider-content"},X=A.extend({name:"divider",style:Z,classes:J,inlineStyles:G}),Y={name:"BaseDivider",extends:B,props:{align:{type:String,default:null},layout:{type:String,default:"horizontal"},type:{type:String,default:"solid"}},style:X,provide:function(){return{$pcDivider:this,$parentInstance:this}}};function g(t){"@babel/helpers - typeof";return g=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},g(t)}function j(t,e,i){return(e=tt(e))in t?Object.defineProperty(t,e,{value:i,enumerable:!0,configurable:!0,writable:!0}):t[e]=i,t}function tt(t){var e=et(t,"string");return g(e)=="symbol"?e:e+""}function et(t,e){if(g(t)!="object"||!t)return t;var i=t[Symbol.toPrimitive];if(i!==void 0){var s=i.call(t,e);if(g(s)!="object")return s;throw new TypeError("@@toPrimitive must return a primitive value.")}return(e==="string"?String:Number)(t)}var D={name:"Divider",extends:Y,inheritAttrs:!1,computed:{dataP:function(){return H(j(j(j({},this.align,this.align),this.layout,this.layout),this.type,this.type))}}},it=["aria-orientation","data-p"],nt=["data-p"];function rt(t,e,i,s,f,h){return c(),p("div",k({class:t.cx("root"),style:t.sx("root"),role:"separator","aria-orientation":t.layout,"data-p":h.dataP},t.ptmi("root")),[t.$slots.default?(c(),p("div",k({key:0,class:t.cx("content"),"data-p":h.dataP},t.ptm("content")),[M(t.$slots,"default")],16,nt)):L("",!0)],16,it)}D.render=rt;var ot={root:{position:"relative"}},st={root:"p-chart"},at=A.extend({name:"chart",classes:st,inlineStyles:ot}),lt={name:"BaseChart",extends:B,props:{type:String,data:null,options:null,plugins:null,width:{type:Number,default:300},height:{type:Number,default:150},canvasProps:{type:null,default:null}},style:at,provide:function(){return{$pcChart:this,$parentInstance:this}}},N={name:"Chart",extends:lt,inheritAttrs:!1,emits:["select","loaded"],chart:null,watch:{data:{handler:function(){this.reinit()},deep:!0},type:function(){this.reinit()},options:function(){this.reinit()}},mounted:function(){this.initChart()},beforeUnmount:function(){this.chart&&(this.chart.destroy(),this.chart=null)},methods:{initChart:function(){var e=this;F(()=>import("./auto-CpL4W96M.js"),[]).then(function(i){e.chart&&(e.chart.destroy(),e.chart=null),i&&i.default&&(e.chart=new i.default(e.$refs.canvas,{type:e.type,data:e.data,options:e.options,plugins:e.plugins})),e.$emit("loaded",e.chart)})},getCanvas:function(){return this.$canvas},getChart:function(){return this.chart},getBase64Image:function(){return this.chart.toBase64Image()},refresh:function(){this.chart&&this.chart.update()},reinit:function(){this.initChart()},onCanvasClick:function(e){if(this.chart){var i=this.chart.getElementsAtEventForMode(e,"nearest",{intersect:!0},!1),s=this.chart.getElementsAtEventForMode(e,"dataset",{intersect:!0},!1);i&&i[0]&&s&&this.$emit("select",{originalEvent:e,element:i[0],dataset:s})}},generateLegend:function(){if(this.chart)return this.chart.generateLegend()}}};function m(t){"@babel/helpers - typeof";return m=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},m(t)}function E(t,e){var i=Object.keys(t);if(Object.getOwnPropertySymbols){var s=Object.getOwnPropertySymbols(t);e&&(s=s.filter(function(f){return Object.getOwnPropertyDescriptor(t,f).enumerable})),i.push.apply(i,s)}return i}function I(t){for(var e=1;e<arguments.length;e++){var i=arguments[e]!=null?arguments[e]:{};e%2?E(Object(i),!0).forEach(function(s){dt(t,s,i[s])}):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(i)):E(Object(i)).forEach(function(s){Object.defineProperty(t,s,Object.getOwnPropertyDescriptor(i,s))})}return t}function dt(t,e,i){return(e=ct(e))in t?Object.defineProperty(t,e,{value:i,enumerable:!0,configurable:!0,writable:!0}):t[e]=i,t}function ct(t){var e=pt(t,"string");return m(e)=="symbol"?e:e+""}function pt(t,e){if(m(t)!="object"||!t)return t;var i=t[Symbol.toPrimitive];if(i!==void 0){var s=i.call(t,e);if(m(s)!="object")return s;throw new TypeError("@@toPrimitive must return a primitive value.")}return(e==="string"?String:Number)(t)}var ut=["width","height"];function vt(t,e,i,s,f,h){return c(),p("div",k({class:t.cx("root"),style:t.sx("root")},t.ptmi("root")),[n("canvas",k({ref:"canvas",width:t.width,height:t.height,onClick:e[0]||(e[0]=function(C){return h.onCanvasClick(C)})},I(I({},t.canvasProps),t.ptm("canvas"))),null,16,ut)],16)}N.render=vt;const ht={class:"page-shell"},ft={class:"container-lg home-page"},yt={class:"hero-grid"},bt={class:"hero-badges"},gt={class:"hero-actions"},mt={class:"hero-stats"},_t={class:"hero-stat-value"},$t={class:"hero-stat-label"},wt={class:"pipeline-mini"},St={class:"tools-section"},kt={class:"tools-grid"},Ct={class:"tool-title"},Pt={class:"tool-desc"},jt={class:"flow-section"},Ot={class:"flow-grid"},xt={class:"cta-section"},zt={class:"cta-content"},Et={class:"cta-actions"},It={__name:"Home",setup(t){const e=W(),i=q();V(()=>{e.fetchQuestions()});const s=z(()=>{const u=new Set(e.questions.map(o=>o.video_url||o.youtube_url||o.source_url||o.video_id||o.processed_video_id).filter(Boolean)).size;return[{label:"Вопросов",value:e.questions.length||"0"},{label:"Технологий",value:e.topics.length||"0"},{label:"Видео",value:u||"0"}]}),f=z(()=>{const u={};for(const r of e.questions)r.topic&&(u[r.topic]=(u[r.topic]||0)+1);const o=Object.entries(u).sort((r,P)=>P[1]-r[1]).slice(0,6);return{labels:o.map(r=>r[0]),datasets:[{label:"Вопросы",data:o.map(r=>r[1]),fill:!0,tension:.35,borderColor:"#10b981",backgroundColor:"rgba(16, 185, 129, 0.2)"}]}}),h={plugins:{legend:{display:!1}},scales:{y:{beginAtZero:!0,ticks:{precision:0}}},maintainAspectRatio:!1},C=[{route:"/interview-questions",icon:"pi pi-question-circle",title:"База вопросов",description:"Фильтры по темам, сложности и вероятности вопроса."},{route:"/trainer",icon:"pi pi-bolt",title:"Тренажер SM-2",description:"Интервальные повторения и закрепление ответа."},{route:"/ai-interview",icon:"pi pi-comments",title:"AI Interview",description:"Практика формулировок в диалоге с AI-интервьюером."},{route:"/test-assignments",icon:"pi pi-briefcase",title:"Тестовые задания",description:"Коллекция задач от компаний для портфолио-практики."},{route:"/recordings",icon:"pi pi-video",title:"Записи",description:"Архив обработанных интервью с таймкодами и вопросами."},{route:"/hh-requirements",icon:"pi pi-chart-bar",title:"Навыки вакансий",description:"Аналитика востребованных навыков по рынку."}],O=[{index:"01",title:"Загрузка и транскрибация",description:"Whisper извлекает текст и структуру разговора из видео."},{index:"02",title:"Извлечение вопросов",description:"LLM выделяет релевантные вопросы и убирает дубликаты."},{index:"03",title:"Подготовка и тренировка",description:"Ты учишься по базе и закрепляешь материал в тренажере."}];function x(u){i.push(u)}return(u,o)=>(c(),p("div",ht,[l(Q),n("main",ft,[n("section",yt,[l(a(y),{class:"hero-card"},{content:d(()=>[n("div",bt,[l(a(S),{value:"AI-powered подготовка",severity:"success",rounded:"",class:"hero-tag"}),l(a(S),{value:"PrimeVue Edition",severity:"contrast",rounded:""})]),o[4]||(o[4]=n("h1",{class:"h-page hero-title"},[w(" Готовься к "),n("span",null,"IT-собеседованиям"),w(" системно и быстрее ")],-1)),o[5]||(o[5]=n("p",{class:"hero-sub"}," Вопросы, тренажер SM-2, mock-интервью, анализ вакансий и обработка видео в едином рабочем пространстве без переключения между разными сервисами. ",-1)),n("div",gt,[l(a(b),{label:"Начать подготовку",icon:"pi pi-play",onClick:o[0]||(o[0]=r=>a(i).push("/interview-questions"))}),l(a(b),{label:"Тренажер SM-2",icon:"pi pi-bolt",severity:"secondary",outlined:"",onClick:o[1]||(o[1]=r=>a(i).push("/trainer"))})]),n("div",mt,[(c(!0),p(_,null,$(s.value,r=>(c(),p("div",{key:r.label,class:"hero-stat-item"},[n("div",_t,v(r.value),1),n("div",$t,v(r.label),1)]))),128))])]),_:1}),l(a(y),{class:"stats-card"},{title:d(()=>[...o[6]||(o[6]=[w("Динамика по темам",-1)])]),content:d(()=>[o[7]||(o[7]=n("p",{class:"stats-sub"},"Топ-6 тем по количеству собранных вопросов",-1)),l(a(D)),l(a(N),{type:"line",data:f.value,options:h,class:"home-chart"},null,8,["data"]),n("div",wt,[(c(),p(_,null,$(O,r=>n("div",{key:r.title,class:"pipeline-item"},[l(a(S),{value:r.index,severity:"secondary",rounded:""},null,8,["value"]),n("span",null,v(r.title),1)])),64))])]),_:1})]),n("section",St,[o[8]||(o[8]=n("div",{class:"tools-head"},[n("h2",{class:"section-title"},"Инструменты платформы"),n("p",{class:"p-muted"},"Ежедневная практика, контроль прогресса и приоритизация тем в одном интерфейсе.")],-1)),n("div",kt,[(c(),p(_,null,$(C,r=>l(a(y),{key:r.route,class:"tool-card",onClick:P=>x(r.route)},{title:d(()=>[n("div",Ct,[n("i",{class:R(r.icon)},null,2),n("span",null,v(r.title),1)])]),content:d(()=>[n("p",Pt,v(r.description),1)]),footer:d(()=>[l(a(b),{label:"Открыть",text:"",icon:"pi pi-arrow-right",iconPos:"right",onClick:K(P=>x(r.route),["stop"])},null,8,["onClick"])]),_:2},1032,["onClick"])),64))])]),n("section",jt,[l(a(y),{class:"flow-card"},{title:d(()=>[...o[9]||(o[9]=[w("Как это работает",-1)])]),content:d(()=>[n("div",Ot,[(c(),p(_,null,$(O,r=>n("div",{key:r.title,class:"flow-step"},[l(a(S),{value:r.index,rounded:""},null,8,["value"]),n("h3",null,v(r.title),1),n("p",null,v(r.description),1)])),64))])]),_:1})]),n("section",xt,[l(a(y),{class:"cta-card"},{content:d(()=>[n("div",zt,[o[10]||(o[10]=n("div",null,[n("h2",null,"Готов начать подготовку?"),n("p",null,"Собери персональный ритм: вопросы, карточки и аналитика навыков в одном цикле.")],-1)),n("div",Et,[l(a(b),{label:"К вопросам",icon:"pi pi-compass",onClick:o[2]||(o[2]=r=>a(i).push("/interview-questions"))}),l(a(b),{label:"Открыть записи",icon:"pi pi-video",severity:"secondary",outlined:"",onClick:o[3]||(o[3]=r=>a(i).push("/recordings"))})])])]),_:1})])]),l(U)]))}},Ft=T(It,[["__scopeId","data-v-81ff9f5d"]]);export{Ft as default};
