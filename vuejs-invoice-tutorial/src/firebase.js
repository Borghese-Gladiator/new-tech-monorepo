
// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries
// Your web app's Firebase configuration
const firebaseConfig = {
	apiKey: process.env.VUE_API_KEY,
	authDomain: process.env.VUE_AUTH_DOMAIN,
	projectId: process.env.VUE_PROJECT_ID,
	storageBucket: process.env.VUE_STORAGE_BUCKLLET,
	messagingSenderId: process.env.VUE_MESSAGINGS_SENDER_ID,
	appId: process.env.VUE_APP_ID,
	databaseURL: process.env.VUE_DATABASE_URL
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export default app;