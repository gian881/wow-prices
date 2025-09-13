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

    socket = new WebSocket(URL)

    socket.onopen = () => {
      state.isConnected = true
    }

    socket.onmessage = (event) => {
      try {
        state.lastMessage = JSON.parse(event.data)
      } catch (error) {
        console.error('Erro ao processar a mensagem do WebSocket:', error)
      }
    }

    socket.onclose = () => {
      state.isConnected = false
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

  sendMessage(message: object) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    } else {
      console.error('Não é possível enviar mensagem. WebSocket não está conectado.')
    }
  },
}
