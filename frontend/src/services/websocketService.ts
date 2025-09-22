import { reactive } from 'vue'

export const state = reactive({
  isConnected: false,
  lastMessage: null as object | null,
})

const URL = import.meta.env.VITE_WS_BASE_URL
let socket: WebSocket | null = null

export const websocketService = {
  connect() {
    if (socket && socket.readyState === WebSocket.OPEN) {
      return
    }

    console.log('Iniciando conexão WebSocket... com URL:', URL)

    socket = new WebSocket(URL)

    console.log('Tentando conectar ao WebSocket...')

    socket.onopen = () => {
      state.isConnected = true
      console.log('WebSocket conectado com sucesso.')
    }

    socket.onmessage = (event) => {
      console.log('Mensagem recebida do WebSocket:', event.data)

      try {
        state.lastMessage = JSON.parse(event.data)
      } catch (error) {
        if (error instanceof SyntaxError) {
          console.error('Erro de sintaxe ao analisar a mensagem JSON do WebSocket:', error)
        } else {
          console.error('Erro ao processar a mensagem do WebSocket:', error)
        }
      }
    }

    socket.onclose = () => {
      state.isConnected = false
      console.log('WebSocket desconectado. Tentando reconectar...')
      setTimeout(() => {
        this.connect()
      }, 5000)
    }

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error)
      state.isConnected = false
    }
  },

  disconnect() {
    if (socket) {
      socket.close()
    }
  },

  sendJSONMessage(message: object) {
    console.log('Enviando mensagem pelo WebSocket:', message)
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    } else {
      console.error('Não é possível enviar mensagem. WebSocket não está conectado.')
    }
  },
}
