import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Message',
    component: () => import('../views/Message.vue')
  },
  {
    path: '/actor',
    name: 'Actor',
    component: () => import('../views/Actor.vue')
  },
  {
    path: '/media',
    name: 'Media',
    component: () => import('../views/Media.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

export default router
