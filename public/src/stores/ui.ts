import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: ()=>({ message:'', visible:false }),
  actions:{
    show(msg:string){ this.message = msg; this.visible = true; setTimeout(()=>this.visible=false, 2500) }
  }
})

export const useLoadingStore = defineStore('loading', {
  state: ()=>({ loading:false, text:'处理中...' }),
  actions:{ start(text?:string){ this.text = text || '处理中...'; this.loading = true }, stop(){ this.loading=false } }
})