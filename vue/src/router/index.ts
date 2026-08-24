import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/messages',
    name: 'Message',
    // Message 组件由 App.vue 通过 v-show 管理，此处仅保留路由占位
    component: () => import('../views/Empty.vue')
  },
  {
    path: '/media',
    name: 'Media',
    component: () => import('../views/Media.vue')
  },
  {
    path: '/media/:id(\\d+)',
    name: 'MediaDetail',
    component: () => import('../views/MediaDetail.vue'),
    props: (route: any) => ({ mediaId: Number(route.params.id) })
  },
  {
    path: '/folders',
    name: 'Folder',
    component: () => import('../views/Folder.vue')
  },
  {
    path: '/folders/:id(\\d+)',
    name: 'FolderDetail',
    component: () => import('../views/FolderDetail.vue'),
    props: (route: any) => ({ folderId: Number(route.params.id) })
  },
  {
    path: '/admin',
    component: () => import('../views/Admin.vue'),
    children: [
      {
        path: '',
        name: 'Admin',
        component: () => import('../components/admin/AdminDashboard.vue')
      },
      {
        path: 'tables',
        name: 'AdminTables',
        component: () => import('../components/admin/TableBrowser.vue')
      },
      {
        path: 'missing-files',
        name: 'MissingPhysicalFiles',
        component: () => import('../views/MissingPhysicalFiles.vue')
      },
      {
        path: 'duplicate-files',
        name: 'DuplicatePhysicalFiles',
        component: () => import('../views/DuplicatePhysicalFiles.vue')
      }
    ]
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('../views/Transactions.vue')
  },
  {
    path: '/collection',
    name: 'Collection',
    component: () => import('../views/Collection.vue')
  },
  {
    path: '/people',
    name: 'People',
    component: () => import('../views/People.vue')
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
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

export default router
