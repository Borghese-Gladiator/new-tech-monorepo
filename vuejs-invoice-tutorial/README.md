## Created on Jul 8th, 2022

# invoice-vuejs-tutorial
Followed tutorial to build Vue3 + TailwindCSS + Firebase Realtime Database app
- [https://codesource.io/build-an-invoicing-app-with-vuejs-and-tailwind-css/](https://codesource.io/build-an-invoicing-app-with-vuejs-and-tailwind-css/)
- [https://codesource.io/understanding-firebase-realtime-database-using-react/](https://codesource.io/understanding-firebase-realtime-database-using-react/)
- Articles used Vue2, but I used Vue3 with similar code
- [https://www.vuemastery.com/blog/vue-router-a-tutorial-for-vue-3/](https://www.vuemastery.com/blog/vue-router-a-tutorial-for-vue-3/)
- Fix bug of tailwindcss not applying styles [https://tailwindcss.com/docs/guides/vite](https://tailwindcss.com/docs/guides/vite)
- [https://firebase.google.com/docs/database/web/start](https://firebase.google.com/docs/database/web/start)
- [https://firebase.google.com/docs/database/web/read-and-write](https://firebase.google.com/docs/database/web/read-and-write)

## Notes
Vue.js Complaints
- Vue2 and Vue3 do not update imports properly during hot reload, especially when I update the paths (eg: .. to .)
- Vue2 requires explicitly stating which components are used after importing them which is a pain.
- Both no unused variables error and no single word names error are pretty annoying

Firebase
- Cloud Firestore is Firebase's newest database for mobile app development. It builds on the successes of the Realtime Database with a new, more intuitive data model. Cloud Firestore also features richer, faster queries and scales further than the Realtime Database.
- Realtime Database is Firebase's original database. It's an efficient, low-latency solution for mobile apps that require synced states across clients in realtime.

### Bootstrapping Steps
- `npx @vue/cli create invoice-vuejs-tutorial`
- `npm i tailwindcss`
- `npx tailwindcss init`
- load tailwind.css to main.js
- add NavMenu.vue
- add routing to display Home page
  - `npm i vue-router`
  - create views/Home.vue with form and invoice creation button
  - create router/index.js
  - add router in main.js
  - update App.vue to display router-view
- rewrite router to use Vue3 router
- fix dev packages - `npm i -D sass sass-loader`
- fix bug of tailwindcss not being loaded (tailwind.config.js was missing content)
- add firebase
  - `npm i firebase`
  - NOTE: tutorial had older implementation - Web Version 8 vs Web Version 9 and I installed web version 9 but was using version 8 code (copy-pasting Firebase config also does not work since it requires database URL)
    - Official documentation shows latest code which I followed to fix code
      - [https://firebase.google.com/docs/database/web/start](https://firebase.google.com/docs/database/web/start)
			- [https://firebase.google.com/docs/database/web/read-and-write](https://firebase.google.com/docs/database/web/read-and-write)
    - Realtime Database - https://firebase.google.com/docs/database/web/start
    - Cloud Firestore - https://firebase.google.com/docs/firestore/quickstart
    - I rewrote firebase.js and HomePage.vue usage to accomadate newer versions for Realtime Database
  - add env variables for deployment (vue requires env variables to be prefixed with VUE_) [https://stackoverflow.com/questions/50828904/using-environment-variables-with-vue-js](https://stackoverflow.com/questions/50828904/using-environment-variables-with-vue-js)
  - create example.env
- Deploy content to Netlify using Git-based Deployment
  - build command: "npm run build"
	- build directory: "dist"
	- set all environment variables listed in example.env

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
