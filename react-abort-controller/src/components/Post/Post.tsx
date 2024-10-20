import React from 'react';
import usePostLoading from './usePostLoading';
 
const Post = () => {
  const { post, isLoading } = usePostLoading();
 
  if (!post || isLoading) {
    return <div>Loading...</div>;
  }
 
  return (
    <div>
      <p>{post.id}</p>
      <p>{post.title}</p>
      <p>{post.body}</p>
    </div>
  );
};
 
export default Post;