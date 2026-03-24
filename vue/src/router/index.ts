import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Actor from '../views/Actor.vue'
import ActorDetail from '../views/ActorDetail.vue'
import Message from '../views/Message.vue'
import Media from '../views/Media.vue'
import MediaDetail from '../views/MediaDetail.vue'
import Article from '../views/Article.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/actor',
    name: 'Actor',
    component: Actor
  },
  {
    path: '/actor/:id',
    name: 'ActorDetail',
    component: ActorDetail
  },
  {
    path: '/message',
    name: 'Message',
    component: Message
  },
  {
    path: '/media',
    name: 'Media',
    component: Media
  },
  {
    path: '/media/:id',
    name: 'MediaDetail',
    component: MediaDetail
  },
  {
    path: '/article',
    name: 'Article',
    component: Article
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 所有页面之间的导航都使用滚动行为
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Keep-alive includes
router.beforeEach((_to, _from, next) => {
  const app = document.getElementById('app')
  if (app) {
    const keepAliveInclude = ['Media', 'Actor', 'Message', 'Tag', 'Article', 'Home']
    app.setAttribute('data-keep-alive', keepAliveInclude.join(','))
  }
  next()
})

export default router
