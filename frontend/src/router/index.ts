import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: 'WOW Prices',
      },
    },
    {
      path: '/items',
      name: 'items',
      component: () => import('../views/AllItemsView.vue'),
      meta: {
        title: 'Todos os itens - WOW Prices',
      },
    },
    {
      path: '/item/:id',
      name: 'item',
      component: () => import('../views/ItemView.vue'),
      meta: {
        title: 'Item detalhado - WOW Prices',
      },
    },
    {
      path: '/week',
      name: 'week',
      component: () => import('../views/WeekView.vue'),
      meta: {
        title: 'Semana - WOW Prices',
      },
    },
    {
      path: '/calculator',
      name: 'calculator',
      component: () => import('../views/CalculatorView.vue'),
      meta: {
        title: 'Calculadora - WOW Prices',
      },
    },
  ],
})

router.beforeEach((to) => {
  const { title } = to.meta
  const defaultTitle = 'WOW Prices'

  if (title && typeof title === 'string') {
    document.title = title
  } else {
    document.title = defaultTitle
  }
})

export default router
