import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
 
interface Post {
  id: number;
  title: string;
  body: string;
}
 
function usePostLoading() {
  const { postId } = useParams<{ postId: string }>();
  const [isLoading, setIsLoading] = useState(false);
  const [post, setPost] = useState<Post | null>(null);
  
  useEffect(() => {
    const abortController = new AbortController();
   
    setIsLoading(true);
    fetch(`https://jsonplaceholder.typicode.com/posts/${postId}`, {
      signal: abortController.signal,
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        }
        return Promise.reject();
      })
      .then((fetchedPost: Post) => {
        setPost(fetchedPost);
      })
      .catch(() => {
        if (abortController.signal.aborted) {
          console.log('The user aborted the request');
        } else {
          console.error('The request failed');
        }
      })
      .finally(() => {
        setIsLoading(false);
      });
   
    return () => {
      abortController.abort();
    };
  }, [postId]);
 
  return {
    post,
    isLoading,
  };
}
 
export default usePostLoading;