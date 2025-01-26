import React, { useEffect, useState } from 'react';

interface Todo {
  id: number;
  title: string;
  completed: boolean;
}

export const TodoList: React.FC = () => {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchTodos = async () => {
      try {
        const response = await fetch('http://localhost:3000/api/todos');
        const data = await response.json();
        setTodos(data);
      } catch (error: any) {
        console.error('Failed to fetch todos:', error);
        setError(error as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchTodos();
  }, []);

  if (loading) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h1>Todo List</h1>
      {error && <p style={{ color: 'red' }}>{error.message}</p>}
      <ul>
        {todos.map((todo) => (
          <li key={todo.id}>
            {todo.title} {todo.completed ? '✅' : '❌'}
          </li>
        ))}
      </ul>
    </div>
  );
};
