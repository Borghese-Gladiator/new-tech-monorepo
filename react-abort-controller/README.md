## Created on June 10th, 2022 12:35 AM

# React Abort Controller
First Abort Controller to handle race conditions in React - [https://wanago.io/2022/04/11/abort-controller-race-conditions-react/](https://wanago.io/2022/04/11/abort-controller-race-conditions-react/)

## Notes

#### Steps
- `npx create-react-app --template typescript`
- Installed and set up react-router-dom@6 - [https://reactrouter.com/docs/en/v6/getting-started/installation#create-react-app](https://reactrouter.com/docs/en/v6/getting-started/installation#create-react-app)
- Add race condition code (Post component)
  - Race Condition in Post code
    - user fetches first post
    - user switches to second post before first post finishes loading
    - second post loads and displays
    - first post loads and then overwrites
- Added didCancel flag that prevents rerender if page was switched
- Add AbortController to Post hook
  > While the above solution fixes the problem, it is not optimal. The browser still waits for the HTTP request to finish but ignores its result. To improve this, we can use the AbortController.
  - Flow of AbortController
    - user fetches first post
    - user switches to second post
    - useEffect cleans after previous post and runs abortController.abort() before second post starts fetch
    - second post loads and displays
- Add AbortController to wait util

## Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).
