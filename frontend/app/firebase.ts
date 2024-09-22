import { initializeApp } from 'firebase/app'
import { getDatabase } from 'firebase/database'

// Your web app's Firebase configuration
const firebaseConfig = {
  // apiKey: 'YOUR_API_KEY',
  authDomain: 'aistinkers.firebaseapp.com',
  databaseURL: 'https://aistinkers-default-rtdb.firebaseio.com/',
  projectId: 'aistinkers',
  storageBucket: 'aistinkers.appspot.com',
  // messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
  // appId: 'YOUR_APP_ID',
}

// Initialize Firebase
const app = initializeApp(firebaseConfig)

// Initialize Realtime Database and get a reference to the service
export const database = getDatabase(app)
