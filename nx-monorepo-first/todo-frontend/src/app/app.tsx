// Uncomment this line to use CSS modules
// import styles from './app.module.css';
import NxWelcome from './nx-welcome';
import { TodoList } from './TodoList';

export function App() {
  return (
    <div>
      {/* <NxWelcome title="todo-frontend" /> */}
      <TodoList />
    </div>
  );
}

export default App;
