import { FC, ReactElement } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Post from './components/Post';
import { wait } from './utils';
import './App.css';

const Home: FC = (): ReactElement => {
  return (
    <>
      <main>
        <h2>Welcome to the homepage!</h2>
        <p>You can do this, I believe in you.</p>
      </main>
      <nav>
        <Link to="/about">About</Link>
        <Link to="/posts/1">Post 1</Link>
      </nav>
    </>
  )
}

const About: FC = (): ReactElement => {
  return (
    <>
      <main>
        <h2>Who are we?</h2>
        <p>
          That feels like an existential question, don't you
          think?
        </p>
      </main>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/posts/1">Post 1</Link>
      </nav>
    </>
  )
}

const abortController = new AbortController();
 
setTimeout(() => {
  abortController.abort();
}, 1000);
 
wait(5000, abortController.signal)
  .then(() => {
    console.log('5 seconds passed');
  })
  .catch(() => {
    console.log('Waiting was interrupted');
  });

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/posts/:postId" element={<Post />} />
      </Routes>
    </div>
  );
}

export default App;
