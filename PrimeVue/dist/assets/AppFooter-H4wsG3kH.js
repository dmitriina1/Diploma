import{o as s,c as d,b,m,B as U,J as P,E,M as R,Y as oe,a2 as z,O as w,U as se,ai as W,l as S,W as Z,F,g as ue,z as D,p as v,n as C,q as L,a as g,t as x,a3 as le,r as A,f as k,X as me,aj as de,d as Y,ak as ce,h as be,w as y,u as h,k as N,i as fe}from"./index-CRpKplOa.js";import{b as j,R as pe,s as $,x as _,f as he,u as Ie,a as O}from"./auth-CA8NM3zp.js";var J={name:"BarsIcon",extends:j};function ve(t){return we(t)||ke(t)||ye(t)||ge()}function ge(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function ye(t,e){if(t){if(typeof t=="string")return T(t,e);var n={}.toString.call(t).slice(8,-1);return n==="Object"&&t.constructor&&(n=t.constructor.name),n==="Map"||n==="Set"?Array.from(t):n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?T(t,e):void 0}}function ke(t){if(typeof Symbol<"u"&&t[Symbol.iterator]!=null||t["@@iterator"]!=null)return Array.from(t)}function we(t){if(Array.isArray(t))return T(t)}function T(t,e){(e==null||e>t.length)&&(e=t.length);for(var n=0,i=Array(e);n<e;n++)i[n]=t[n];return i}function Pe(t,e,n,i,o,r){return s(),d("svg",m({width:"14",height:"14",viewBox:"0 0 14 14",fill:"none",xmlns:"http://www.w3.org/2000/svg"},t.pti()),ve(e[0]||(e[0]=[b("path",{"fill-rule":"evenodd","clip-rule":"evenodd",d:"M13.3226 3.6129H0.677419C0.497757 3.6129 0.325452 3.54152 0.198411 3.41448C0.0713707 3.28744 0 3.11514 0 2.93548C0 2.75581 0.0713707 2.58351 0.198411 2.45647C0.325452 2.32943 0.497757 2.25806 0.677419 2.25806H13.3226C13.5022 2.25806 13.6745 2.32943 13.8016 2.45647C13.9286 2.58351 14 2.75581 14 2.93548C14 3.11514 13.9286 3.28744 13.8016 3.41448C13.6745 3.54152 13.5022 3.6129 13.3226 3.6129ZM13.3226 7.67741H0.677419C0.497757 7.67741 0.325452 7.60604 0.198411 7.479C0.0713707 7.35196 0 7.17965 0 6.99999C0 6.82033 0.0713707 6.64802 0.198411 6.52098C0.325452 6.39394 0.497757 6.32257 0.677419 6.32257H13.3226C13.5022 6.32257 13.6745 6.39394 13.8016 6.52098C13.9286 6.64802 14 6.82033 14 6.99999C14 7.17965 13.9286 7.35196 13.8016 7.479C13.6745 7.60604 13.5022 7.67741 13.3226 7.67741ZM0.677419 11.7419H13.3226C13.5022 11.7419 13.6745 11.6706 13.8016 11.5435C13.9286 11.4165 14 11.2442 14 11.0645C14 10.8848 13.9286 10.7125 13.8016 10.5855C13.6745 10.4585 13.5022 10.3871 13.3226 10.3871H0.677419C0.497757 10.3871 0.325452 10.4585 0.198411 10.5855C0.0713707 10.7125 0 10.8848 0 11.0645C0 11.2442 0.0713707 11.4165 0.198411 11.5435C0.325452 11.6706 0.497757 11.7419 0.677419 11.7419Z",fill:"currentColor"},null,-1)])),16)}J.render=Pe;var xe=`
    .p-menubar {
        display: flex;
        align-items: center;
        background: dt('menubar.background');
        border: 1px solid dt('menubar.border.color');
        border-radius: dt('menubar.border.radius');
        color: dt('menubar.color');
        padding: dt('menubar.padding');
        gap: dt('menubar.gap');
    }

    .p-menubar-start,
    .p-megamenu-end {
        display: flex;
        align-items: center;
    }

    .p-menubar-root-list,
    .p-menubar-submenu {
        display: flex;
        margin: 0;
        padding: 0;
        list-style: none;
        outline: 0 none;
    }

    .p-menubar-root-list {
        align-items: center;
        flex-wrap: wrap;
        gap: dt('menubar.gap');
    }

    .p-menubar-root-list > .p-menubar-item > .p-menubar-item-content {
        border-radius: dt('menubar.base.item.border.radius');
    }

    .p-menubar-root-list > .p-menubar-item > .p-menubar-item-content > .p-menubar-item-link {
        padding: dt('menubar.base.item.padding');
    }

    .p-menubar-item-content {
        transition:
            background dt('menubar.transition.duration'),
            color dt('menubar.transition.duration');
        border-radius: dt('menubar.item.border.radius');
        color: dt('menubar.item.color');
    }

    .p-menubar-item-link {
        cursor: pointer;
        display: flex;
        align-items: center;
        text-decoration: none;
        overflow: hidden;
        position: relative;
        color: inherit;
        padding: dt('menubar.item.padding');
        gap: dt('menubar.item.gap');
        user-select: none;
        outline: 0 none;
    }

    .p-menubar-item-label {
        line-height: 1;
    }

    .p-menubar-item-icon {
        color: dt('menubar.item.icon.color');
    }

    .p-menubar-submenu-icon {
        color: dt('menubar.submenu.icon.color');
        margin-left: auto;
        font-size: dt('menubar.submenu.icon.size');
        width: dt('menubar.submenu.icon.size');
        height: dt('menubar.submenu.icon.size');
    }

    .p-menubar-submenu .p-menubar-submenu-icon:dir(rtl) {
        margin-left: 0;
        margin-right: auto;
    }

    .p-menubar-item.p-focus > .p-menubar-item-content {
        color: dt('menubar.item.focus.color');
        background: dt('menubar.item.focus.background');
    }

    .p-menubar-item.p-focus > .p-menubar-item-content .p-menubar-item-icon {
        color: dt('menubar.item.icon.focus.color');
    }

    .p-menubar-item.p-focus > .p-menubar-item-content .p-menubar-submenu-icon {
        color: dt('menubar.submenu.icon.focus.color');
    }

    .p-menubar-item:not(.p-disabled) > .p-menubar-item-content:hover {
        color: dt('menubar.item.focus.color');
        background: dt('menubar.item.focus.background');
    }

    .p-menubar-item:not(.p-disabled) > .p-menubar-item-content:hover .p-menubar-item-icon {
        color: dt('menubar.item.icon.focus.color');
    }

    .p-menubar-item:not(.p-disabled) > .p-menubar-item-content:hover .p-menubar-submenu-icon {
        color: dt('menubar.submenu.icon.focus.color');
    }

    .p-menubar-item-active > .p-menubar-item-content {
        color: dt('menubar.item.active.color');
        background: dt('menubar.item.active.background');
    }

    .p-menubar-item-active > .p-menubar-item-content .p-menubar-item-icon {
        color: dt('menubar.item.icon.active.color');
    }

    .p-menubar-item-active > .p-menubar-item-content .p-menubar-submenu-icon {
        color: dt('menubar.submenu.icon.active.color');
    }

    .p-menubar-submenu {
        display: none;
        position: absolute;
        min-width: 12.5rem;
        z-index: 1;
        background: dt('menubar.submenu.background');
        border: 1px solid dt('menubar.submenu.border.color');
        border-radius: dt('menubar.submenu.border.radius');
        box-shadow: dt('menubar.submenu.shadow');
        color: dt('menubar.submenu.color');
        flex-direction: column;
        padding: dt('menubar.submenu.padding');
        gap: dt('menubar.submenu.gap');
    }

    .p-menubar-submenu .p-menubar-separator {
        border-block-start: 1px solid dt('menubar.separator.border.color');
    }

    .p-menubar-submenu .p-menubar-item {
        position: relative;
    }

    .p-menubar-submenu > .p-menubar-item-active > .p-menubar-submenu {
        display: block;
        left: 100%;
        top: 0;
    }

    .p-menubar-end {
        margin-left: auto;
        align-self: center;
    }

    .p-menubar-end:dir(rtl) {
        margin-left: 0;
        margin-right: auto;
    }

    .p-menubar-button {
        display: none;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        width: dt('menubar.mobile.button.size');
        height: dt('menubar.mobile.button.size');
        position: relative;
        color: dt('menubar.mobile.button.color');
        border: 0 none;
        background: transparent;
        border-radius: dt('menubar.mobile.button.border.radius');
        transition:
            background dt('menubar.transition.duration'),
            color dt('menubar.transition.duration'),
            outline-color dt('menubar.transition.duration');
        outline-color: transparent;
    }

    .p-menubar-button:hover {
        color: dt('menubar.mobile.button.hover.color');
        background: dt('menubar.mobile.button.hover.background');
    }

    .p-menubar-button:focus-visible {
        box-shadow: dt('menubar.mobile.button.focus.ring.shadow');
        outline: dt('menubar.mobile.button.focus.ring.width') dt('menubar.mobile.button.focus.ring.style') dt('menubar.mobile.button.focus.ring.color');
        outline-offset: dt('menubar.mobile.button.focus.ring.offset');
    }

    .p-menubar-mobile {
        position: relative;
    }

    .p-menubar-mobile .p-menubar-button {
        display: flex;
    }

    .p-menubar-mobile .p-menubar-root-list {
        position: absolute;
        display: none;
        width: 100%;
        flex-direction: column;
        top: 100%;
        left: 0;
        z-index: 1;
        padding: dt('menubar.submenu.padding');
        background: dt('menubar.submenu.background');
        border: 1px solid dt('menubar.submenu.border.color');
        box-shadow: dt('menubar.submenu.shadow');
        border-radius: dt('menubar.submenu.border.radius');
        gap: dt('menubar.submenu.gap');
    }

    .p-menubar-mobile .p-menubar-root-list:dir(rtl) {
        left: auto;
        right: 0;
    }

    .p-menubar-mobile .p-menubar-root-list > .p-menubar-item > .p-menubar-item-content > .p-menubar-item-link {
        padding: dt('menubar.item.padding');
    }

    .p-menubar-mobile-active .p-menubar-root-list {
        display: flex;
    }

    .p-menubar-mobile .p-menubar-root-list .p-menubar-item {
        width: 100%;
        position: static;
    }

    .p-menubar-mobile .p-menubar-root-list .p-menubar-separator {
        border-block-start: 1px solid dt('menubar.separator.border.color');
    }

    .p-menubar-mobile .p-menubar-root-list > .p-menubar-item > .p-menubar-item-content .p-menubar-submenu-icon {
        margin-left: auto;
        transition: transform 0.2s;
    }

    .p-menubar-mobile .p-menubar-root-list > .p-menubar-item > .p-menubar-item-content .p-menubar-submenu-icon:dir(rtl),
    .p-menubar-mobile .p-menubar-submenu-icon:dir(rtl) {
        margin-left: 0;
        margin-right: auto;
    }

    .p-menubar-mobile .p-menubar-root-list > .p-menubar-item-active > .p-menubar-item-content .p-menubar-submenu-icon {
        transform: rotate(-180deg);
    }

    .p-menubar-mobile .p-menubar-submenu .p-menubar-submenu-icon {
        transition: transform 0.2s;
        transform: rotate(90deg);
    }

    .p-menubar-mobile .p-menubar-item-active > .p-menubar-item-content .p-menubar-submenu-icon {
        transform: rotate(-90deg);
    }

    .p-menubar-mobile .p-menubar-submenu {
        width: 100%;
        position: static;
        box-shadow: none;
        border: 0 none;
        padding-inline-start: dt('menubar.submenu.mobile.indent');
        padding-inline-end: 0;
    }
`,Ce={submenu:function(e){var n=e.instance,i=e.processedItem;return{display:n.isItemActive(i)?"flex":"none"}}},Le={root:function(e){var n=e.instance;return["p-menubar p-component",{"p-menubar-mobile":n.queryMatches,"p-menubar-mobile-active":n.mobileActive}]},start:"p-menubar-start",button:"p-menubar-button",rootList:"p-menubar-root-list",item:function(e){var n=e.instance,i=e.processedItem;return["p-menubar-item",{"p-menubar-item-active":n.isItemActive(i),"p-focus":n.isItemFocused(i),"p-disabled":n.isItemDisabled(i)}]},itemContent:"p-menubar-item-content",itemLink:"p-menubar-item-link",itemIcon:"p-menubar-item-icon",itemLabel:"p-menubar-item-label",submenuIcon:"p-menubar-submenu-icon",submenu:"p-menubar-submenu",separator:"p-menubar-separator",end:"p-menubar-end"},Ae=U.extend({name:"menubar",style:xe,classes:Le,inlineStyles:Ce}),X={name:"AngleDownIcon",extends:j};function Se(t){return Ee(t)||ze(t)||Me(t)||Ke()}function Ke(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function Me(t,e){if(t){if(typeof t=="string")return V(t,e);var n={}.toString.call(t).slice(8,-1);return n==="Object"&&t.constructor&&(n=t.constructor.name),n==="Map"||n==="Set"?Array.from(t):n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?V(t,e):void 0}}function ze(t){if(typeof Symbol<"u"&&t[Symbol.iterator]!=null||t["@@iterator"]!=null)return Array.from(t)}function Ee(t){if(Array.isArray(t))return V(t)}function V(t,e){(e==null||e>t.length)&&(e=t.length);for(var n=0,i=Array(e);n<e;n++)i[n]=t[n];return i}function Fe(t,e,n,i,o,r){return s(),d("svg",m({width:"14",height:"14",viewBox:"0 0 14 14",fill:"none",xmlns:"http://www.w3.org/2000/svg"},t.pti()),Se(e[0]||(e[0]=[b("path",{d:"M3.58659 4.5007C3.68513 4.50023 3.78277 4.51945 3.87379 4.55723C3.9648 4.59501 4.04735 4.65058 4.11659 4.7207L7.11659 7.7207L10.1166 4.7207C10.2619 4.65055 10.4259 4.62911 10.5843 4.65956C10.7427 4.69002 10.8871 4.77074 10.996 4.88976C11.1049 5.00877 11.1726 5.15973 11.1889 5.32022C11.2052 5.48072 11.1693 5.6422 11.0866 5.7807L7.58659 9.2807C7.44597 9.42115 7.25534 9.50004 7.05659 9.50004C6.85784 9.50004 6.66722 9.42115 6.52659 9.2807L3.02659 5.7807C2.88614 5.64007 2.80725 5.44945 2.80725 5.2507C2.80725 5.05195 2.88614 4.86132 3.02659 4.7207C3.09932 4.64685 3.18675 4.58911 3.28322 4.55121C3.37969 4.51331 3.48305 4.4961 3.58659 4.5007Z",fill:"currentColor"},null,-1)])),16)}X.render=Fe;var Q={name:"AngleRightIcon",extends:j};function _e(t){return Ve(t)||Te(t)||De(t)||Oe()}function Oe(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function De(t,e){if(t){if(typeof t=="string")return B(t,e);var n={}.toString.call(t).slice(8,-1);return n==="Object"&&t.constructor&&(n=t.constructor.name),n==="Map"||n==="Set"?Array.from(t):n==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?B(t,e):void 0}}function Te(t){if(typeof Symbol<"u"&&t[Symbol.iterator]!=null||t["@@iterator"]!=null)return Array.from(t)}function Ve(t){if(Array.isArray(t))return B(t)}function B(t,e){(e==null||e>t.length)&&(e=t.length);for(var n=0,i=Array(e);n<e;n++)i[n]=t[n];return i}function Be(t,e,n,i,o,r){return s(),d("svg",m({width:"14",height:"14",viewBox:"0 0 14 14",fill:"none",xmlns:"http://www.w3.org/2000/svg"},t.pti()),_e(e[0]||(e[0]=[b("path",{d:"M5.25 11.1728C5.14929 11.1694 5.05033 11.1455 4.9592 11.1025C4.86806 11.0595 4.78666 10.9984 4.72 10.9228C4.57955 10.7822 4.50066 10.5916 4.50066 10.3928C4.50066 10.1941 4.57955 10.0035 4.72 9.86283L7.72 6.86283L4.72 3.86283C4.66067 3.71882 4.64765 3.55991 4.68275 3.40816C4.71785 3.25642 4.79932 3.11936 4.91585 3.01602C5.03238 2.91268 5.17819 2.84819 5.33305 2.83149C5.4879 2.81479 5.64411 2.84671 5.78 2.92283L9.28 6.42283C9.42045 6.56346 9.49934 6.75408 9.49934 6.95283C9.49934 7.15158 9.42045 7.34221 9.28 7.48283L5.78 10.9228C5.71333 10.9984 5.63193 11.0595 5.5408 11.1025C5.44966 11.1455 5.35071 11.1694 5.25 11.1728Z",fill:"currentColor"},null,-1)])),16)}Q.render=Be;var je={name:"BaseMenubar",extends:$,props:{model:{type:Array,default:null},buttonProps:{type:null,default:null},breakpoint:{type:String,default:"960px"},ariaLabelledby:{type:String,default:null},ariaLabel:{type:String,default:null}},style:Ae,provide:function(){return{$pcMenubar:this,$parentInstance:this}}},ee={name:"MenubarSub",hostName:"Menubar",extends:$,emits:["item-mouseenter","item-click","item-mousemove"],props:{items:{type:Array,default:null},root:{type:Boolean,default:!1},popup:{type:Boolean,default:!1},mobileActive:{type:Boolean,default:!1},templates:{type:Object,default:null},level:{type:Number,default:0},menuId:{type:String,default:null},focusedItemId:{type:String,default:null},activeItemPath:{type:Object,default:null}},list:null,methods:{getItemId:function(e){return"".concat(this.menuId,"_").concat(e.key)},getItemKey:function(e){return this.getItemId(e)},getItemProp:function(e,n,i){return e&&e.item?W(e.item[n],i):void 0},getItemLabel:function(e){return this.getItemProp(e,"label")},getItemLabelId:function(e){return"".concat(this.menuId,"_").concat(e.key,"_label")},getPTOptions:function(e,n,i){return this.ptm(i,{context:{item:e.item,index:n,active:this.isItemActive(e),focused:this.isItemFocused(e),disabled:this.isItemDisabled(e),level:this.level}})},isItemActive:function(e){return this.activeItemPath.some(function(n){return n.key===e.key})},isItemVisible:function(e){return this.getItemProp(e,"visible")!==!1},isItemDisabled:function(e){return this.getItemProp(e,"disabled")},isItemFocused:function(e){return this.focusedItemId===this.getItemId(e)},isItemGroup:function(e){return P(e.items)},onItemClick:function(e,n){this.getItemProp(n,"command",{originalEvent:e,item:n.item}),this.$emit("item-click",{originalEvent:e,processedItem:n,isFocus:!0})},onItemMouseEnter:function(e,n){this.$emit("item-mouseenter",{originalEvent:e,processedItem:n})},onItemMouseMove:function(e,n){this.$emit("item-mousemove",{originalEvent:e,processedItem:n})},getAriaPosInset:function(e){return e-this.calculateAriaSetSize.slice(0,e).length+1},getMenuItemProps:function(e,n){return{action:m({class:this.cx("itemLink"),tabindex:-1},this.getPTOptions(e,n,"itemLink")),icon:m({class:[this.cx("itemIcon"),this.getItemProp(e,"icon")]},this.getPTOptions(e,n,"itemIcon")),label:m({class:this.cx("itemLabel")},this.getPTOptions(e,n,"itemLabel")),submenuicon:m({class:this.cx("submenuIcon")},this.getPTOptions(e,n,"submenuIcon"))}}},computed:{calculateAriaSetSize:function(){var e=this;return this.items.filter(function(n){return e.isItemVisible(n)&&e.getItemProp(n,"separator")})},getAriaSetSize:function(){var e=this;return this.items.filter(function(n){return e.isItemVisible(n)&&!e.getItemProp(n,"separator")}).length}},components:{AngleRightIcon:Q,AngleDownIcon:X},directives:{ripple:pe}},$e=["id","aria-label","aria-disabled","aria-expanded","aria-haspopup","aria-setsize","aria-posinset","data-p-active","data-p-focused","data-p-disabled"],Re=["onClick","onMouseenter","onMousemove"],Ne=["href","target"],Ge=["id"],He=["id"];function qe(t,e,n,i,o,r){var l=S("MenubarSub",!0),p=Z("ripple");return s(),d("ul",m({class:n.level===0?t.cx("rootList"):t.cx("submenu")},n.level===0?t.ptm("rootList"):t.ptm("submenu")),[(s(!0),d(F,null,ue(n.items,function(a,u){return s(),d(F,{key:r.getItemKey(a)},[r.isItemVisible(a)&&!r.getItemProp(a,"separator")?(s(),d("li",m({key:0,id:r.getItemId(a),style:r.getItemProp(a,"style"),class:[t.cx("item",{processedItem:a}),r.getItemProp(a,"class")],role:"menuitem","aria-label":r.getItemLabel(a),"aria-disabled":r.isItemDisabled(a)||void 0,"aria-expanded":r.isItemGroup(a)?r.isItemActive(a):void 0,"aria-haspopup":r.isItemGroup(a)&&!r.getItemProp(a,"to")?"menu":void 0,"aria-setsize":r.getAriaSetSize,"aria-posinset":r.getAriaPosInset(u)},{ref_for:!0},r.getPTOptions(a,u,"item"),{"data-p-active":r.isItemActive(a),"data-p-focused":r.isItemFocused(a),"data-p-disabled":r.isItemDisabled(a)}),[b("div",m({class:t.cx("itemContent"),onClick:function(c){return r.onItemClick(c,a)},onMouseenter:function(c){return r.onItemMouseEnter(c,a)},onMousemove:function(c){return r.onItemMouseMove(c,a)}},{ref_for:!0},r.getPTOptions(a,u,"itemContent")),[n.templates.item?(s(),v(L(n.templates.item),{key:1,item:a.item,root:n.root,hasSubmenu:r.getItemProp(a,"items"),label:r.getItemLabel(a),props:r.getMenuItemProps(a,u)},null,8,["item","root","hasSubmenu","label","props"])):D((s(),d("a",m({key:0,href:r.getItemProp(a,"url"),class:t.cx("itemLink"),target:r.getItemProp(a,"target"),tabindex:"-1"},{ref_for:!0},r.getPTOptions(a,u,"itemLink")),[n.templates.itemicon?(s(),v(L(n.templates.itemicon),{key:0,item:a.item,class:C(t.cx("itemIcon"))},null,8,["item","class"])):r.getItemProp(a,"icon")?(s(),d("span",m({key:1,class:[t.cx("itemIcon"),r.getItemProp(a,"icon")]},{ref_for:!0},r.getPTOptions(a,u,"itemIcon")),null,16)):g("",!0),b("span",m({id:r.getItemLabelId(a),class:t.cx("itemLabel")},{ref_for:!0},r.getPTOptions(a,u,"itemLabel")),x(r.getItemLabel(a)),17,Ge),r.getItemProp(a,"items")?(s(),d(F,{key:2},[n.templates.submenuicon?(s(),v(L(n.templates.submenuicon),{key:0,root:n.root,active:r.isItemActive(a),class:C(t.cx("submenuIcon"))},null,8,["root","active","class"])):(s(),v(L(n.root?"AngleDownIcon":"AngleRightIcon"),m({key:1,class:t.cx("submenuIcon")},{ref_for:!0},r.getPTOptions(a,u,"submenuIcon")),null,16,["class"]))],64)):g("",!0)],16,Ne)),[[p]])],16,Re),r.isItemVisible(a)&&r.isItemGroup(a)?(s(),v(l,{key:0,id:r.getItemId(a)+"_list",menuId:n.menuId,role:"menu",style:le(t.sx("submenu",!0,{processedItem:a})),focusedItemId:n.focusedItemId,items:a.items,mobileActive:n.mobileActive,activeItemPath:n.activeItemPath,templates:n.templates,level:n.level+1,"aria-labelledby":r.getItemLabelId(a),pt:t.pt,unstyled:t.unstyled,onItemClick:e[0]||(e[0]=function(f){return t.$emit("item-click",f)}),onItemMouseenter:e[1]||(e[1]=function(f){return t.$emit("item-mouseenter",f)}),onItemMousemove:e[2]||(e[2]=function(f){return t.$emit("item-mousemove",f)})},null,8,["id","menuId","style","focusedItemId","items","mobileActive","activeItemPath","templates","level","aria-labelledby","pt","unstyled"])):g("",!0)],16,$e)):g("",!0),r.isItemVisible(a)&&r.getItemProp(a,"separator")?(s(),d("li",m({key:1,id:r.getItemId(a),class:[t.cx("separator"),r.getItemProp(a,"class")],style:r.getItemProp(a,"style"),role:"separator"},{ref_for:!0},t.ptm("separator")),null,16,He)):g("",!0)],64)}),128))],16)}ee.render=qe;var te={name:"Menubar",extends:je,inheritAttrs:!1,emits:["focus","blur"],matchMediaListener:null,data:function(){return{mobileActive:!1,focused:!1,focusedItemInfo:{index:-1,level:0,parentKey:""},activeItemPath:[],dirty:!1,query:null,queryMatches:!1}},watch:{activeItemPath:function(e){P(e)?(this.bindOutsideClickListener(),this.bindResizeListener()):(this.unbindOutsideClickListener(),this.unbindResizeListener())}},outsideClickListener:null,container:null,menubar:null,mounted:function(){this.bindMatchMediaListener()},beforeUnmount:function(){this.mobileActive=!1,this.unbindOutsideClickListener(),this.unbindResizeListener(),this.unbindMatchMediaListener(),this.container&&_.clear(this.container),this.container=null},methods:{getItemProp:function(e,n){return e?W(e[n]):void 0},getItemLabel:function(e){return this.getItemProp(e,"label")},isItemDisabled:function(e){return this.getItemProp(e,"disabled")},isItemVisible:function(e){return this.getItemProp(e,"visible")!==!1},isItemGroup:function(e){return P(this.getItemProp(e,"items"))},isItemSeparator:function(e){return this.getItemProp(e,"separator")},getProccessedItemLabel:function(e){return e?this.getItemLabel(e.item):void 0},isProccessedItemGroup:function(e){return e&&P(e.items)},toggle:function(e){var n=this;this.mobileActive?(this.mobileActive=!1,_.clear(this.menubar),this.hide()):(this.mobileActive=!0,_.set("menu",this.menubar,this.$primevue.config.zIndex.menu),setTimeout(function(){n.show()},1)),this.bindOutsideClickListener(),e.preventDefault()},show:function(){w(this.menubar)},hide:function(e,n){var i=this;this.mobileActive&&(this.mobileActive=!1,setTimeout(function(){w(i.$refs.menubutton)},0)),this.activeItemPath=[],this.focusedItemInfo={index:-1,level:0,parentKey:""},n&&w(this.menubar),this.dirty=!1},onFocus:function(e){this.focused=!0,this.focusedItemInfo=this.focusedItemInfo.index!==-1?this.focusedItemInfo:{index:this.findFirstFocusedItemIndex(),level:0,parentKey:""},this.$emit("focus",e)},onBlur:function(e){this.focused=!1,this.focusedItemInfo={index:-1,level:0,parentKey:""},this.searchValue="",this.dirty=!1,this.$emit("blur",e)},onKeyDown:function(e){var n=e.metaKey||e.ctrlKey;switch(e.code){case"ArrowDown":this.onArrowDownKey(e);break;case"ArrowUp":this.onArrowUpKey(e);break;case"ArrowLeft":this.onArrowLeftKey(e);break;case"ArrowRight":this.onArrowRightKey(e);break;case"Home":this.onHomeKey(e);break;case"End":this.onEndKey(e);break;case"Space":this.onSpaceKey(e);break;case"Enter":case"NumpadEnter":this.onEnterKey(e);break;case"Escape":this.onEscapeKey(e);break;case"Tab":this.onTabKey(e);break;case"PageDown":case"PageUp":case"Backspace":case"ShiftLeft":case"ShiftRight":break;default:!n&&se(e.key)&&this.searchItems(e,e.key);break}},onItemChange:function(e,n){var i=e.processedItem,o=e.isFocus;if(!z(i)){var r=i.index,l=i.key,p=i.level,a=i.parentKey,u=i.items,f=P(u),c=this.activeItemPath.filter(function(I){return I.parentKey!==a&&I.parentKey!==l});f&&c.push(i),this.focusedItemInfo={index:r,level:p,parentKey:a},f&&(this.dirty=!0),o&&w(this.menubar),!(n==="hover"&&this.queryMatches)&&(this.activeItemPath=c)}},onItemClick:function(e){var n=e.originalEvent,i=e.processedItem,o=this.isProccessedItemGroup(i),r=z(i.parent),l=this.isSelected(i);if(l){var p=i.index,a=i.key,u=i.level,f=i.parentKey;this.activeItemPath=this.activeItemPath.filter(function(I){return a!==I.key&&a.startsWith(I.key)}),this.focusedItemInfo={index:p,level:u,parentKey:f},this.dirty=!r,w(this.menubar)}else if(o)this.onItemChange(e);else{var c=r?i:this.activeItemPath.find(function(I){return I.parentKey===""});this.hide(n),this.changeFocusedItemIndex(n,c?c.index:-1),this.mobileActive=!1,w(this.menubar)}},onItemMouseEnter:function(e){this.dirty&&this.onItemChange(e,"hover")},onItemMouseMove:function(e){this.focused&&this.changeFocusedItemIndex(e,e.processedItem.index)},menuButtonClick:function(e){this.toggle(e)},menuButtonKeydown:function(e){(e.code==="Enter"||e.code==="NumpadEnter"||e.code==="Space")&&this.menuButtonClick(e)},onArrowDownKey:function(e){var n=this.visibleItems[this.focusedItemInfo.index],i=n?z(n.parent):null;if(i){var o=this.isProccessedItemGroup(n);o&&(this.onItemChange({originalEvent:e,processedItem:n}),this.focusedItemInfo={index:-1,parentKey:n.key},this.onArrowRightKey(e))}else{var r=this.focusedItemInfo.index!==-1?this.findNextItemIndex(this.focusedItemInfo.index):this.findFirstFocusedItemIndex();this.changeFocusedItemIndex(e,r)}e.preventDefault()},onArrowUpKey:function(e){var n=this,i=this.visibleItems[this.focusedItemInfo.index],o=z(i.parent);if(o){var r=this.isProccessedItemGroup(i);if(r){this.onItemChange({originalEvent:e,processedItem:i}),this.focusedItemInfo={index:-1,parentKey:i.key};var l=this.findLastItemIndex();this.changeFocusedItemIndex(e,l)}}else{var p=this.activeItemPath.find(function(u){return u.key===i.parentKey});if(this.focusedItemInfo.index===0)this.focusedItemInfo={index:-1,parentKey:p?p.parentKey:""},this.searchValue="",this.onArrowLeftKey(e),this.activeItemPath=this.activeItemPath.filter(function(u){return u.parentKey!==n.focusedItemInfo.parentKey});else{var a=this.focusedItemInfo.index!==-1?this.findPrevItemIndex(this.focusedItemInfo.index):this.findLastFocusedItemIndex();this.changeFocusedItemIndex(e,a)}}e.preventDefault()},onArrowLeftKey:function(e){var n=this,i=this.visibleItems[this.focusedItemInfo.index],o=i?this.activeItemPath.find(function(l){return l.key===i.parentKey}):null;if(o)this.onItemChange({originalEvent:e,processedItem:o}),this.activeItemPath=this.activeItemPath.filter(function(l){return l.parentKey!==n.focusedItemInfo.parentKey}),e.preventDefault();else{var r=this.focusedItemInfo.index!==-1?this.findPrevItemIndex(this.focusedItemInfo.index):this.findLastFocusedItemIndex();this.changeFocusedItemIndex(e,r),e.preventDefault()}},onArrowRightKey:function(e){var n=this.visibleItems[this.focusedItemInfo.index],i=n?this.activeItemPath.find(function(l){return l.key===n.parentKey}):null;if(i){var o=this.isProccessedItemGroup(n);o&&(this.onItemChange({originalEvent:e,processedItem:n}),this.focusedItemInfo={index:-1,parentKey:n.key},this.onArrowDownKey(e))}else{var r=this.focusedItemInfo.index!==-1?this.findNextItemIndex(this.focusedItemInfo.index):this.findFirstFocusedItemIndex();this.changeFocusedItemIndex(e,r),e.preventDefault()}},onHomeKey:function(e){this.changeFocusedItemIndex(e,this.findFirstItemIndex()),e.preventDefault()},onEndKey:function(e){this.changeFocusedItemIndex(e,this.findLastItemIndex()),e.preventDefault()},onEnterKey:function(e){if(this.focusedItemInfo.index!==-1){var n=E(this.menubar,'li[id="'.concat("".concat(this.focusedItemId),'"]')),i=n&&E(n,'a[data-pc-section="itemlink"]');i?i.click():n&&n.click();var o=this.visibleItems[this.focusedItemInfo.index],r=this.isProccessedItemGroup(o);!r&&(this.focusedItemInfo.index=this.findFirstFocusedItemIndex())}e.preventDefault()},onSpaceKey:function(e){this.onEnterKey(e)},onEscapeKey:function(e){if(this.focusedItemInfo.level!==0){var n=this.focusedItemInfo;this.hide(e,!1),this.focusedItemInfo={index:Number(n.parentKey.split("_")[0]),level:0,parentKey:""}}e.preventDefault()},onTabKey:function(e){if(this.focusedItemInfo.index!==-1){var n=this.visibleItems[this.focusedItemInfo.index],i=this.isProccessedItemGroup(n);!i&&this.onItemChange({originalEvent:e,processedItem:n})}this.hide()},bindOutsideClickListener:function(){var e=this;this.outsideClickListener||(this.outsideClickListener=function(n){var i=e.container&&!e.container.contains(n.target),o=!(e.target&&(e.target===n.target||e.target.contains(n.target)));i&&o&&e.hide()},document.addEventListener("click",this.outsideClickListener,!0))},unbindOutsideClickListener:function(){this.outsideClickListener&&(document.removeEventListener("click",this.outsideClickListener,!0),this.outsideClickListener=null)},bindResizeListener:function(){var e=this;this.resizeListener||(this.resizeListener=function(n){oe()||e.hide(n,!0),e.mobileActive=!1},window.addEventListener("resize",this.resizeListener))},unbindResizeListener:function(){this.resizeListener&&(window.removeEventListener("resize",this.resizeListener),this.resizeListener=null)},bindMatchMediaListener:function(){var e=this;if(!this.matchMediaListener){var n=matchMedia("(max-width: ".concat(this.breakpoint,")"));this.query=n,this.queryMatches=n.matches,this.matchMediaListener=function(){e.queryMatches=n.matches,e.mobileActive=!1},this.query.addEventListener("change",this.matchMediaListener)}},unbindMatchMediaListener:function(){this.matchMediaListener&&(this.query.removeEventListener("change",this.matchMediaListener),this.matchMediaListener=null)},isItemMatched:function(e){var n;return this.isValidItem(e)&&((n=this.getProccessedItemLabel(e))===null||n===void 0?void 0:n.toLocaleLowerCase().startsWith(this.searchValue.toLocaleLowerCase()))},isValidItem:function(e){return!!e&&!this.isItemDisabled(e.item)&&!this.isItemSeparator(e.item)&&this.isItemVisible(e.item)},isValidSelectedItem:function(e){return this.isValidItem(e)&&this.isSelected(e)},isSelected:function(e){return this.activeItemPath.some(function(n){return n.key===e.key})},findFirstItemIndex:function(){var e=this;return this.visibleItems.findIndex(function(n){return e.isValidItem(n)})},findLastItemIndex:function(){var e=this;return R(this.visibleItems,function(n){return e.isValidItem(n)})},findNextItemIndex:function(e){var n=this,i=e<this.visibleItems.length-1?this.visibleItems.slice(e+1).findIndex(function(o){return n.isValidItem(o)}):-1;return i>-1?i+e+1:e},findPrevItemIndex:function(e){var n=this,i=e>0?R(this.visibleItems.slice(0,e),function(o){return n.isValidItem(o)}):-1;return i>-1?i:e},findSelectedItemIndex:function(){var e=this;return this.visibleItems.findIndex(function(n){return e.isValidSelectedItem(n)})},findFirstFocusedItemIndex:function(){var e=this.findSelectedItemIndex();return e<0?this.findFirstItemIndex():e},findLastFocusedItemIndex:function(){var e=this.findSelectedItemIndex();return e<0?this.findLastItemIndex():e},searchItems:function(e,n){var i=this;this.searchValue=(this.searchValue||"")+n;var o=-1,r=!1;return this.focusedItemInfo.index!==-1?(o=this.visibleItems.slice(this.focusedItemInfo.index).findIndex(function(l){return i.isItemMatched(l)}),o=o===-1?this.visibleItems.slice(0,this.focusedItemInfo.index).findIndex(function(l){return i.isItemMatched(l)}):o+this.focusedItemInfo.index):o=this.visibleItems.findIndex(function(l){return i.isItemMatched(l)}),o!==-1&&(r=!0),o===-1&&this.focusedItemInfo.index===-1&&(o=this.findFirstFocusedItemIndex()),o!==-1&&this.changeFocusedItemIndex(e,o),this.searchTimeout&&clearTimeout(this.searchTimeout),this.searchTimeout=setTimeout(function(){i.searchValue="",i.searchTimeout=null},500),r},changeFocusedItemIndex:function(e,n){this.focusedItemInfo.index!==n&&(this.focusedItemInfo.index=n,this.scrollInView())},scrollInView:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:-1,n=e!==-1?"".concat(this.$id,"_").concat(e):this.focusedItemId,i=E(this.menubar,'li[id="'.concat(n,'"]'));i&&i.scrollIntoView&&i.scrollIntoView({block:"nearest",inline:"start"})},createProcessedItems:function(e){var n=this,i=arguments.length>1&&arguments[1]!==void 0?arguments[1]:0,o=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{},r=arguments.length>3&&arguments[3]!==void 0?arguments[3]:"",l=[];return e&&e.forEach(function(p,a){var u=(r!==""?r+"_":"")+a,f={item:p,index:a,level:i,key:u,parent:o,parentKey:r};f.items=n.createProcessedItems(p.items,i+1,f,u),l.push(f)}),l},containerRef:function(e){this.container=e},menubarRef:function(e){this.menubar=e?e.$el:void 0}},computed:{processedItems:function(){return this.createProcessedItems(this.model||[])},visibleItems:function(){var e=this,n=this.activeItemPath.find(function(i){return i.key===e.focusedItemInfo.parentKey});return n?n.items:this.processedItems},focusedItemId:function(){return this.focusedItemInfo.index!==-1?"".concat(this.$id).concat(P(this.focusedItemInfo.parentKey)?"_"+this.focusedItemInfo.parentKey:"","_").concat(this.focusedItemInfo.index):null}},components:{MenubarSub:ee,BarsIcon:J}};function K(t){"@babel/helpers - typeof";return K=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},K(t)}function G(t,e){var n=Object.keys(t);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(t);e&&(i=i.filter(function(o){return Object.getOwnPropertyDescriptor(t,o).enumerable})),n.push.apply(n,i)}return n}function H(t){for(var e=1;e<arguments.length;e++){var n=arguments[e]!=null?arguments[e]:{};e%2?G(Object(n),!0).forEach(function(i){Ue(t,i,n[i])}):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(n)):G(Object(n)).forEach(function(i){Object.defineProperty(t,i,Object.getOwnPropertyDescriptor(n,i))})}return t}function Ue(t,e,n){return(e=We(e))in t?Object.defineProperty(t,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):t[e]=n,t}function We(t){var e=Ze(t,"string");return K(e)=="symbol"?e:e+""}function Ze(t,e){if(K(t)!="object"||!t)return t;var n=t[Symbol.toPrimitive];if(n!==void 0){var i=n.call(t,e);if(K(i)!="object")return i;throw new TypeError("@@toPrimitive must return a primitive value.")}return(e==="string"?String:Number)(t)}var Ye=["aria-haspopup","aria-expanded","aria-controls","aria-label"];function Je(t,e,n,i,o,r){var l=S("BarsIcon"),p=S("MenubarSub");return s(),d("div",m({ref:r.containerRef,class:t.cx("root")},t.ptmi("root")),[t.$slots.start?(s(),d("div",m({key:0,class:t.cx("start")},t.ptm("start")),[A(t.$slots,"start")],16)):g("",!0),A(t.$slots,t.$slots.button?"button":"menubutton",{id:t.$id,class:C(t.cx("button")),toggleCallback:function(u){return r.menuButtonClick(u)}},function(){var a;return[t.model&&t.model.length>0?(s(),d("a",m({key:0,ref:"menubutton",role:"button",tabindex:"0",class:t.cx("button"),"aria-haspopup":!!(t.model.length&&t.model.length>0),"aria-expanded":o.mobileActive,"aria-controls":t.$id,"aria-label":(a=t.$primevue.config.locale.aria)===null||a===void 0?void 0:a.navigation,onClick:e[0]||(e[0]=function(u){return r.menuButtonClick(u)}),onKeydown:e[1]||(e[1]=function(u){return r.menuButtonKeydown(u)})},H(H({},t.buttonProps),t.ptm("button"))),[A(t.$slots,t.$slots.buttonicon?"buttonicon":"menubuttonicon",{},function(){return[k(l,me(de(t.ptm("buttonicon"))),null,16)]})],16,Ye)):g("",!0)]}),k(p,{ref:r.menubarRef,id:t.$id+"_list",role:"menubar",items:r.processedItems,templates:t.$slots,root:!0,mobileActive:o.mobileActive,tabindex:"0","aria-activedescendant":o.focused?r.focusedItemId:void 0,menuId:t.$id,focusedItemId:o.focused?r.focusedItemId:void 0,activeItemPath:o.activeItemPath,level:0,"aria-labelledby":t.ariaLabelledby,"aria-label":t.ariaLabel,pt:t.pt,unstyled:t.unstyled,onFocus:r.onFocus,onBlur:r.onBlur,onKeydown:r.onKeyDown,onItemClick:r.onItemClick,onItemMouseenter:r.onItemMouseEnter,onItemMousemove:r.onItemMouseMove},null,8,["id","items","templates","mobileActive","aria-activedescendant","menuId","focusedItemId","activeItemPath","aria-labelledby","aria-label","pt","unstyled","onFocus","onBlur","onKeydown","onItemClick","onItemMouseenter","onItemMousemove"]),t.$slots.end?(s(),d("div",m({key:1,class:t.cx("end")},t.ptm("end")),[A(t.$slots,"end")],16)):g("",!0)],16)}te.render=Je;var Xe=`
    .p-avatar {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: dt('avatar.width');
        height: dt('avatar.height');
        font-size: dt('avatar.font.size');
        background: dt('avatar.background');
        color: dt('avatar.color');
        border-radius: dt('avatar.border.radius');
    }

    .p-avatar-image {
        background: transparent;
    }

    .p-avatar-circle {
        border-radius: 50%;
    }

    .p-avatar-circle img {
        border-radius: 50%;
    }

    .p-avatar-icon {
        font-size: dt('avatar.icon.size');
        width: dt('avatar.icon.size');
        height: dt('avatar.icon.size');
    }

    .p-avatar img {
        width: 100%;
        height: 100%;
    }

    .p-avatar-lg {
        width: dt('avatar.lg.width');
        height: dt('avatar.lg.width');
        font-size: dt('avatar.lg.font.size');
    }

    .p-avatar-lg .p-avatar-icon {
        font-size: dt('avatar.lg.icon.size');
        width: dt('avatar.lg.icon.size');
        height: dt('avatar.lg.icon.size');
    }

    .p-avatar-xl {
        width: dt('avatar.xl.width');
        height: dt('avatar.xl.width');
        font-size: dt('avatar.xl.font.size');
    }

    .p-avatar-xl .p-avatar-icon {
        font-size: dt('avatar.xl.icon.size');
        width: dt('avatar.xl.icon.size');
        height: dt('avatar.xl.icon.size');
    }

    .p-avatar-group {
        display: flex;
        align-items: center;
    }

    .p-avatar-group .p-avatar + .p-avatar {
        margin-inline-start: dt('avatar.group.offset');
    }

    .p-avatar-group .p-avatar {
        border: 2px solid dt('avatar.group.border.color');
    }

    .p-avatar-group .p-avatar-lg + .p-avatar-lg {
        margin-inline-start: dt('avatar.lg.group.offset');
    }

    .p-avatar-group .p-avatar-xl + .p-avatar-xl {
        margin-inline-start: dt('avatar.xl.group.offset');
    }
`,Qe={root:function(e){var n=e.props;return["p-avatar p-component",{"p-avatar-image":n.image!=null,"p-avatar-circle":n.shape==="circle","p-avatar-lg":n.size==="large","p-avatar-xl":n.size==="xlarge"}]},label:"p-avatar-label",icon:"p-avatar-icon"},et=U.extend({name:"avatar",style:Xe,classes:Qe}),tt={name:"BaseAvatar",extends:$,props:{label:{type:String,default:null},icon:{type:String,default:null},image:{type:String,default:null},size:{type:String,default:"normal"},shape:{type:String,default:"square"},ariaLabelledby:{type:String,default:null},ariaLabel:{type:String,default:null}},style:et,provide:function(){return{$pcAvatar:this,$parentInstance:this}}};function M(t){"@babel/helpers - typeof";return M=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(e){return typeof e}:function(e){return e&&typeof Symbol=="function"&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e},M(t)}function q(t,e,n){return(e=nt(e))in t?Object.defineProperty(t,e,{value:n,enumerable:!0,configurable:!0,writable:!0}):t[e]=n,t}function nt(t){var e=it(t,"string");return M(e)=="symbol"?e:e+""}function it(t,e){if(M(t)!="object"||!t)return t;var n=t[Symbol.toPrimitive];if(n!==void 0){var i=n.call(t,e);if(M(i)!="object")return i;throw new TypeError("@@toPrimitive must return a primitive value.")}return(e==="string"?String:Number)(t)}var ne={name:"Avatar",extends:tt,inheritAttrs:!1,emits:["error"],methods:{onError:function(e){this.$emit("error",e)}},computed:{dataP:function(){return he(q(q({},this.shape,this.shape),this.size,this.size))}}},rt=["aria-labelledby","aria-label","data-p"],at=["data-p"],ot=["data-p"],st=["src","alt","data-p"];function ut(t,e,n,i,o,r){return s(),d("div",m({class:t.cx("root"),"aria-labelledby":t.ariaLabelledby,"aria-label":t.ariaLabel},t.ptmi("root"),{"data-p":r.dataP}),[A(t.$slots,"default",{},function(){return[t.label?(s(),d("span",m({key:0,class:t.cx("label")},t.ptm("label"),{"data-p":r.dataP}),x(t.label),17,at)):t.$slots.icon?(s(),v(L(t.$slots.icon),{key:1,class:C(t.cx("icon"))},null,8,["class"])):t.icon?(s(),d("span",m({key:2,class:[t.cx("icon"),t.icon]},t.ptm("icon"),{"data-p":r.dataP}),null,16,ot)):t.image?(s(),d("img",m({key:3,src:t.image,alt:t.ariaLabel,onError:e[0]||(e[0]=function(){return r.onError&&r.onError.apply(r,arguments)})},t.ptm("image"),{"data-p":r.dataP}),null,16,st)):g("",!0)]})],16,rt)}ne.render=ut;const lt={class:"app-header"},mt={class:"container-lg nav-wrap"},dt=["href","onClick"],ct=["href"],bt={class:"header-actions"},ft={class:"profile-name"},pt={__name:"NavBar",setup(t){const e=Ie(),n=ce(),i=be(),o=N(()=>{var a,u;return(((a=e.user)==null?void 0:a.display_name)||((u=e.user)==null?void 0:u.username)||"?").charAt(0).toUpperCase()}),r=N(()=>{const p=[{label:"Вопросы",icon:"pi pi-question-circle",route:"/interview-questions"},{label:"Тренажер",icon:"pi pi-bolt",route:"/trainer"},{label:"AI Interview",icon:"pi pi-comments",route:"/ai-interview"},{label:"Задания",icon:"pi pi-briefcase",route:"/test-assignments"},{label:"Навыки",icon:"pi pi-chart-bar",route:"/hh-requirements"},{label:"Записи",icon:"pi pi-video",route:"/recordings"}];return e.isAdmin&&p.push({label:"Админ",icon:"pi pi-shield",route:"/admin"}),p});function l(){e.logout(),i.push("/")}return(p,a)=>{const u=S("router-link"),f=Z("ripple");return s(),d("header",lt,[b("div",mt,[k(h(te),{model:r.value,class:"app-menubar"},{start:y(()=>[k(u,{to:"/",class:"brand-link"},{default:y(()=>[...a[2]||(a[2]=[b("i",{class:"pi pi-sparkles brand-icon"},null,-1),b("span",{class:"brand-title"},"InterviewHub Prime",-1)])]),_:1})]),item:y(({item:c,props:I})=>[c.route?(s(),v(u,{key:0,to:c.route,custom:""},{default:y(({href:ie,navigate:re,isActive:ae})=>[D((s(),d("a",m({href:ie},I.action,{class:["menu-link",{"menu-link-active":ae}],onClick:re}),[b("i",{class:C(c.icon)},null,2),b("span",null,x(c.label),1)],16,dt)),[[f]])]),_:2},1032,["to"])):D((s(),d("a",m({key:1},I.action,{href:c.url,target:"_blank",rel:"noopener",class:"menu-link"}),[b("i",{class:C(c.icon)},null,2),b("span",null,x(c.label),1)],16,ct)),[[f]])]),end:y(()=>[b("div",bt,[k(h(O),{rounded:"",text:"",severity:"secondary",icon:h(n).isDark?"pi pi-sun":"pi pi-moon",onClick:a[0]||(a[0]=c=>h(n).toggle())},null,8,["icon"]),h(e).isAuthenticated?(s(),v(u,{key:0,to:"/profile",class:"profile-link"},{default:y(()=>[k(h(ne),{label:o.value,shape:"circle",class:"profile-avatar"},null,8,["label"]),b("span",ft,x(h(e).displayName),1)]),_:1})):g("",!0),h(e).isAuthenticated?(s(),v(h(O),{key:1,label:"Выйти",icon:"pi pi-sign-out",size:"small",outlined:"",severity:"secondary",onClick:l})):(s(),v(h(O),{key:2,label:"Войти",size:"small",icon:"pi pi-sign-in",onClick:a[1]||(a[1]=c=>h(i).push("/login"))}))])]),_:1},8,["model"])])])}}},Pt=Y(pt,[["__scopeId","data-v-d612512e"]]),ht={class:"app-footer"},It={class:"container-lg footer-inner"},vt={class:"footer-left"},gt={class:"footer-links"},yt={__name:"AppFooter",setup(t){const e=new Date().getFullYear();return(n,i)=>{const o=S("router-link");return s(),d("footer",ht,[b("div",It,[b("div",vt,[i[0]||(i[0]=b("i",{class:"pi pi-sparkles"},null,-1)),b("span",null,"InterviewHub Prime © "+x(h(e)),1)]),b("div",gt,[k(o,{to:"/suggest"},{default:y(()=>[...i[1]||(i[1]=[fe("Предложить видео",-1)])]),_:1}),i[2]||(i[2]=b("a",{href:"https://primevue.org/",target:"_blank",rel:"noopener"},"PrimeVue",-1)),i[3]||(i[3]=b("a",{href:"https://github.com",target:"_blank",rel:"noopener"},"GitHub",-1))])])])}}},xt=Y(yt,[["__scopeId","data-v-e0616d6d"]]);export{xt as A,Pt as N,Q as a,X as s};
